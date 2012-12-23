# coding: utf-8

# $Revision$

# Don't Judge Mail - Postfix Policy Daemon
#
# Quota plugin. Limits number of incoming and outgoing emails,
# per (SASL) username, email address, email domain or IP address.
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
from djm.postfix import hosted_domains

class Quota(PolicyPlugin):
	''' Introduce quotas for some of the email server resources.
		 * Number of sent/recieved emails
		 * Recipient count
		 * Message size

		Limits can be configured with the following keys:
			* authenticated username
			* sender/recipient email,
			* sender/recipient domain
			* sender IP address

		The most preffered filter is username, since it usually can't
		be forged, and possibility of miconfiguration is minimal.
		(i.e. the "policy target" is clear)

		'*' is the catch-all key and it is treated differently from
		standard keys.
	'''

	def __init__(self, conf):
		self.set_conf(conf)

	def set_conf(self, conf):
		self.conf = conf

	def __call__(self, request):
		conf = self.conf

		db_name = conf.get('database', 'plugin:quota', 'default', mandatory=False)
		db = connect(conf, db_name)

		if not db:
			return PolicyResponse().dunno()

		try:
			quota_keys = {
				'sasl_username': request['sasl_username'],
				'sender': request['sender'],
				'sender_domain': None,
				'recipient': request['recipient'],
				'recipient_count': request['recipient_count'],
				'recipient_domain': request['recipient'].rsplit('@', 1)[1],
				'client_address': request['client_address'],
				'size': request['size'],
			}
		except (KeyError, IndexError):
			error('Missing policy request attribute')
			return PolicyResponse().dunno()

		if '@' in request['sasl_username']:
			quota_keys['sender_domain'] = request['sasl_username'].rsplit('@', 1)[1]
		else:
			quota_keys['sender_domain'] = request['sender'].rsplit('@', 1)[1]

		hd = hosted_domains()
		sd = quota_keys['sender_domain']
		rd = quota_keys['recipient_domain']

		if conf.get('ignore_local', 'plugin:quota') == 'true' and \
			(sd == rd or ((sd in hd) and (rd in hd))):
			return PolicyResponse().dunno()

		c = cursor(db)
		action = None

		for item in self.targeted_policies(c, quota_keys):
			if item['tracking_id'] is None:
				self.new_quota_tracking_item(db, c, item, quota_keys)
		
			resp = self.quota_for(db, c, item, quota_keys)
			action = resp.action

			if action == 'reject':
				return resp
	
		# Stop processing if we've passed positive targeted policies
		if action:
			return resp

		# Maybe our user doesn't exist in quota table?
		for item in self.new_default_policies(c):
			self.new_quota_tracking_item(db, c, item, quota_keys)

		# Process default policies (if any)
		for item in self.default_policies(c, quota_keys):
			resp = self.quota_for(db, c, item, quota_keys)
			if resp.action == 'reject':
				return resp

		return PolicyResponse().dunno()

	def quota_for(self, db, cur, item, quota_keys):
		if item['key'] == '*':
			k = quota_keys[item['key_type']]
		else:
			k = item['key']


		if item['limit_type'] == 'size':
			increment = quota_keys['size']
		else:
			increment = 1.0


		if item['elapsed_time'] >= item['interval_'] \
			or item['elapsed_time'] is None \
			or item['counter'] is None:

			counter = increment
		else:
			counter = (1-(item['elapsed_time']/item['interval_']))*item['counter']

			if counter > item['limit_']:
				info('REJECTED %s:%s score:%.2f policy:%d/%dh' % (
					item['key_type'], k, counter,
					item['limit_'], item['interval_']//3600)
				)
				cur.close()
				db.close()

				return PolicyResponse().reject(item['msg'])
			else:
				counter = counter + increment

		cur.execute('''UPDATE quota_tracking SET counter=%s,
			last_seen=NOW() WHERE quota_id=%s
			AND key_type=%s AND key=%s''',
				(counter, item['id'], item['key_type'], k))
		#info('key:%s increment: %s' % (k, item['counter']))
		#info('key: %s elapsed:%s interval:%s counter=%s old_counter=%s' % (
		#	k,item['elapsed_time'],item['interval_'],counter, item['counter']))
		db.commit()

		return PolicyResponse().accept()

	def new_quota_tracking_item(self, db, cur, item, quota_keys):
		try:
			if item['key'] == '*':
				k = quota_keys[item['key_type']]
			else:
				k = item['key']

			cur.execute('''INSERT INTO quota_tracking
				(quota_id, key_type, key, counter)
				VALUES(%s, %s, %s, %s)''',
				(item['id'], item['key_type'], k, 0.0))
			db.commit()
		except IntegrityError as e:
			# we aspire to be UPSERT so do ignore existing records
			db.rollback()

	def new_default_policies(self, cur):
		# Default policy
		q = '''
			SELECT q.id, q.name, qm.key, qm.key_type,
				q.interval_, q.limit_type, q.limit_
			FROM quota_members AS qm
			LEFT JOIN quotas AS q ON qm.quota_id=q.id
			WHERE qm.key='*' ORDER BY interval_;
		'''
		cur.execute(q)
		return cur.fetchall()

	def default_policies(self, cur, quota_keys):
		# Default policy
		q = '''
			SELECT q.id, q.name, qm.key, qm.key_type,
				q.interval_, q.limit_type, q.limit_, q.msg,
				qt.id as tracking_id, qt.last_seen, qt.counter,
				(extract(epoch from (NOW() - qt.last_seen)))::integer
					AS elapsed_time
			FROM quota_members AS qm
			LEFT JOIN quotas AS q ON qm.quota_id=q.id
			LEFT JOIN quota_tracking AS qt ON
			(q.id = qt.quota_id AND qt.key_type=qm.key_type)
			WHERE qm.key='*' AND
		'''

		keys = []
		cond = []

		for k, v in quota_keys.items():
			if v:
				cond.append('(qt.key=%s AND qt.key_type=%s)')
				keys.append(v)
				keys.append(k)

		q += ' OR '.join(cond)
		q += ' ORDER BY key_type, interval_'

		cur.execute(q, keys)

		return cur.fetchall()

	def targeted_policies(self, cur, quota_keys):
		'''x'''

		# Targeted policy
		q = '''
			SELECT q.id, q.name, qm.key, qm.key_type,
				q.interval_, q.limit_type, q.limit_, q.msg,
				qt.id as tracking_id, qt.last_seen, qt.counter,
				(extract(epoch from (NOW() - qt.last_seen)))::integer
					AS elapsed_time
			FROM quota_members AS qm
			LEFT JOIN quotas AS q ON qm.quota_id=q.id
			LEFT JOIN quota_tracking AS qt ON
			(q.id = qt.quota_id AND qt.key_type=qm.key_type AND
			qm.key=qt.key) WHERE
		'''

		keys = []
		cond = []

		for k, v in quota_keys.items():
			if v:
				cond.append('(qm.key=%s AND qm.key_type=%s)')
				keys.append(v)
				keys.append(k)

		q += ' OR '.join(cond)
		q += ' ORDER BY key_type, interval_'

		cur.execute(q, keys)

		return cur.fetchall()

	def install(self):
		'''Create database schema for Quota plugin'''

		_sql = '''
			CREATE TYPE quota_key AS ENUM
			(
				'sasl_username',
				'sender',
				'sender_domain',
				'recipient',
				'recipient_count',
				'recipient_domain',
				'client_address',
				'size'
			);

			CREATE TYPE quota_limit AS ENUM
			(
				'emails',
				'recipients',
				'size'
			);


			CREATE TABLE quotas
			(
			    id SERIAL PRIMARY KEY,
				name text NOT NULL UNIQUE,
				description text,
			    interval_ integer, -- interval in seconds
				limit_type quota_limit NOT NULL,
			    limit_ integer NOT NULL,
				msg text
			);


			CREATE TABLE quota_members
			(
				id SERIAL PRIMARY KEY,
				quota_id integer REFERENCES quotas(id),
				key_type quota_key NOT NULL,
				key text NOT NULL,
				UNIQUE(quota_id, key_type, key)
			);


			CREATE TABLE quota_tracking
			(
			    id SERIAL PRIMARY KEY,
			    quota_id integer references quotas(id) NOT NULL,
				key_type quota_key NOT NULL,
			    key text NOT NULL,
			    counter double precision,
				last_seen timestamp DEFAULT now(),
				UNIQUE(quota_id, key_type, key)
			);
			'''

		_sql_data = '''
			INSERT INTO quotas(name, description, interval_, limit_type, limit_, msg)
			VALUES
				('100/hour', 'Hourly quota for outgoing email', 3600, 'emails', 100, 'You have reached your hourly limit for sending email.'),
				('1000/day', 'Daily quota for outgoing email', 86400, 'emails',1000, 'You have reached your daily limit for sending email'),
				('5000/week', 'Weekly quota for outgoing email', 604800,'emails', 5000, 'You have reached your weekly limit for sending email'),
				('10000/month', 'Monthly quota for outgoing email', 2592000, 'emails', 10000, 'You have reached your monthly limit for sending email')
			;

			INSERT INTO quota_members(quota_id, key_type, key)
			VALUES
				(1, 'sasl_username', '*'),
				(2, 'sasl_username', '*'),
				(3, 'sasl_username', '*'),
				(4, 'sasl_username', '*')
			;

			-- DO NOT assign "real" members to defalt quota rules
			--- e.g. 
			-- INSERT INTO quota_members(quota_id, key_type, key)
			--    VALUES(1, 'sasl_username', 'user@example.net');
			--- ^^^ don't do this ^^^
		'''

		db_name = self.conf.get('database', 'plugin:quota', 'default')
		db = connect(self.conf, db_name)

		if not db:
			return

		cur = db.cursor()
		cur.execute(_sql)
		cur.execute(_sql_data)
		cur.close()
		db.commit()
		db.close()

	def uninstall(self):
		'''Drop database schema and data for Quota plugin'''

		_sql = '''
			DROP TABLE IF EXISTS quota_tracking, quota_members, quotas;
			DROP TYPE quota_key;
			DROP TYPE quota_limit;
		'''

		db_name = self.conf.get('database', 'plugin:quota', 'default', mandatory=False)
		db = connect(self.conf, db_name)
		if not db:
			return

		cur = db.cursor()
		cur.execute(_sql)
		cur.commit()
		db.close()
