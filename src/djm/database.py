# coding: utf-8

# $Revision$

# Don't Judge Mail - Postfix Policy Daemon
#
# PostgreSQL database utilities with greenlet support.
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
import sys

import psycopg2
import psycopg2.extensions
import psycopg2.extras
import gevent.socket

from djm.logging import info, warn, error

def make_green():
	'''Configure Psycopg to be used with gevent in non-blocking way.'''
	if not hasattr(psycopg2.extensions, 'set_wait_callback'):
		raise ImportError(
			'support for coroutines not available in this Psycopg version (%s)'
			% psycopg2.__version__)

	psycopg2.extensions.set_wait_callback(gevent_wait_callback)

def gevent_wait_callback(conn, timeout=None,
	POLL_OK=psycopg2.extensions.POLL_OK,
	POLL_READ=psycopg2.extensions.POLL_READ,
	POLL_WRITE=psycopg2.extensions.POLL_WRITE,
	wait_read=gevent.socket.wait_read,
	wait_write=gevent.socket.wait_write):
	'''A wait callback useful to allow gevent to work with Psycopg.'''

	while True:
		state = conn.poll()
		if state == POLL_OK:
			break
		elif state == POLL_READ:
			wait_read(conn.fileno(), timeout=timeout)
		elif state == POLL_WRITE:
			wait_write(conn.fileno(), timeout=timeout)
		else:
			raise psycopg2.OperationalError(
				"Bad result from poll: %r" % state)

# DictCursor Factory
def cursor(db):
	return db.cursor(cursor_factory=psycopg2.extras.DictCursor)

class DatabaseConnection(object):
	'''	DB connection factory '''
	def __init__( self ):
		self.is_green = False

	def __call__(self, conf, db='default'):
		if not self.is_green:
			make_green()
			self.is_green = True

		db_params = {}
		for k, v in conf.items('database:%s' % db):
			db_params[k] = v

		try:
			con = psycopg2.connect(**db_params)
			return con
		except psycopg2.Error as e:
			error('Could not connect to the %s database.' % (db,))

# DB connection factory callable
connect = DatabaseConnection()

# Errors
DatabaseError = psycopg2.DatabaseError
DataError = psycopg2.DataError
IntegrityError = psycopg2.IntegrityError
