# coding: utf-8

# $Revision$

# Don't Judge Mail - Postfix Policy Daemon
#
# Greylisting plugin
#
# Copyright (C) 2012-2013 Adis Nezirović <adis at localhost.ba>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import sys

from djm.policy import PolicyPlugin, PolicyResponse
from djm.database import connect, cursor, IntegrityError
from djm.logging import info, warn, error

from gevent import spawn
from time import time

class Greylist(PolicyPlugin):
	def __call__(self, request):
		conf = self.conf
		db_name = conf.get('database', 'plugin:greylist', 'default', mandatory=False)
		db = connect(conf, db_name)
		resp = PolicyResponse()

		if not db:
			return resp.dunno()

		try:
			gk = {
				'sender': request['sender'],
				'sender_domain': request['sender'].rsplit('@', 1)[1],
				'recipient': request['recipient'],
				'client_address': request['client_address'],
			}
		except (KeyError, IndexError):
			error('Missing policy request attribute')
			return resp.dunno()


		# Don't greylist SASL authenticated users
		if 'sasl_username' in request and '@' in request['sasl_username']:
			return resp.dunno()

		c = cursor(db)

		# Client whitelist
		c.execute('''SELECT id FROM greylist_sender_wl WHERE
			sender=%s OR sender=%s''',
			(gk['sender_domain'], gk['client_address']))

		if c.rowcount > 0:
			resp.prepend('X-Greylist', 'Whitelisted by djmd')
			return resp.accept()

		# Auto whitelisted (per domain)
		c.execute('''SELECT id FROM greylist_sender_awl WHERE
			sender_domain=%s AND sender_address=%s''',
			(gk['sender_domain'], gk['client_address']))

		if c.rowcount > 0:
			c.execute('''UPDATE greylist_sender_awl SET last_seen=NOW()
				WHERE sender_domain=%s AND sender_address=%s''',
				(gk['sender_domain'], gk['client_address']))
			db.commit()
			resp.prepend('X-Greylist', 'AWL by djmd')
			return resp.accept()
		
		# New connection or second connection (AWL candidate)
		try:
			c.execute('''INSERT INTO greylist_tracking(sender, sender_address,
				recipient) VALUES(%s, %s, %s)''', 
				(gk['sender'], gk['client_address'], gk['recipient']))
			db.commit()
		except IntegrityError as e:
			db.rollback()
			c.execute('''SELECT first_seen, (extract(epoch from (NOW() -
				first_seen)))::integer as elapsed_time FROM greylist_tracking
				WHERE sender=%s AND sender_address=%s AND recipient=%s''', 
				(gk['sender'], gk['client_address'], gk['recipient']))
			gt = c.fetchone()

			greylist_delay = int(conf.get('greylist_delay', 'plugin:greylist'))

			if gt[1] > greylist_delay:
				try:
					c.execute('''INSERT INTO greylist_sender_awl(sender_domain,
						sender_address, first_seen, last_seen)
						VALUES(%s, %s, %s, NOW())''',
					(gk['sender_domain'], gk['client_address'], gt[0]))
					db.commit()
				except IntegrityError as e:
					# Already whitelisted, move on
					db.rollback()

				# AWL
				resp.prepend('X-Greylist', 'AWL by djmd')
				return resp.accept()

		return resp.reject(msg=conf.get('msg', 'plugin:greylist'))

	def install(self):
		_sql = '''
			CREATE TABLE greylist_tracking (
				id SERIAL PRIMARY KEY,
				sender text,
				sender_address text,
				recipient text,
				first_seen timestamp DEFAULT NOW(),
				UNIQUE(sender, sender_address, recipient)
			);
			CREATE INDEX greylist_track_sender_idx ON greylist_tracking(sender);
			CREATE INDEX greylist_track_sender_addr_idx ON
				greylist_tracking(sender_address);

			CREATE TABLE greylist_sender_awl
			(
				id SERIAL PRIMARY KEY,
				sender_domain text,
				sender_address text,
				first_seen timestamp,
				last_seen timestamp,
				UNIQUE(sender_domain, sender_address)
			);

			CREATE TABLE greylist_sender_wl
			(
				id SERIAL PRIMARY KEY,
				sender text UNIQUE -- domain or IP address
			);

			CREATE TABLE greylist_recipient_wl
			(
				id SERIAL PRIMARY KEY,
				recipient text UNIQUE -- email or domain
			);
		'''

		_sql_drop = '''DROP TABLE greylist_recipient_wl, greylist_sender_wl, 
			greylist_sender_awl, greylist_tracking;
		'''

		db_name = self.conf.get('database', 'plugin:greylist', 'default', mandatory=False)
		db = connect(self.conf, db_name)
		cur = cursor(db)
		cur.execute(_sql_drop)
		db.commit()
		cur.execute(_sql)
		db.commit()
		db.close()

