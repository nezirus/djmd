# coding: utf-8

# $Revision$

# Don't Judge Mail - Postfix Policy Daemon
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
import os
from imp import find_module, load_module
from gevent import socket
from gevent.server import StreamServer
from signal import SIGTERM, SIGQUIT, SIGHUP, SIGUSR1
from daemon import DaemonContext
from daemon.pidfile import TimeoutPIDLockFile as LockFile
from lockfile import AlreadyLocked, LockFailed

from djm.logging import openlog, closelog, debug, info, warn, error
from djm.rc import ConfParser

class PolicyResponse(object):
	'''Helper class for Postfix SMTP Access Policy Delegation responses

	See http://www.postfix.org/SMTPD_POLICY_README.html for full specification
	'''
	def __init__(self, action=None, msg=None):
		self.action = action
		self.msg = msg

	def __repr__(self):
		if not self.action:
			return 'action=dunno\n\n'
		elif not self.msg:
			return 'action=%s\n\n' % (self.action)
		else:
			return 'action=%s %s\n\n' % (self.action, self.msg)

	def dunno(self):
		self.action = 'dunno'
		return self
	
	def accept(self):
		self.action = 'ok'
		return self

	def reject(self, msg=None):
		self.action = 'reject'
		self.msg = msg
		return self
	
	def defer(self, msg=None):
		self.action = 'defer'
		self.msg = msg
		return self
	
	def defer_if_permit(self, msg=None):
		self.action = 'defer_if_permit'
		self.msg = msg
		return self
	
	def defer_if_reject(self, msg=None):
		self.action = 'defer_if_reject'
		self.msg = msg
		return self

	def reject_invalid(self):
		self.action = 'reject'
		self.msg = 'Invalid policy request.'
		return self

class PolicyPlugin(object):
	def __init__(self, conf):
		self.conf = conf

	def set_conf(self, conf):
		self.conf = conf

	def __call__(self, request):
		return PolicyResponse().dunno()

class PolicyDaemon(object):
	'''Don't Judge Mail - A Postfix Policy Daemon'''

	def __init__(self, conf=None):

		self.conf = conf if conf else ConfParser()

		try:
			listen = self.conf.get('listen')
			addr = listen.split(':', 1)[0].strip()
			port = listen.rsplit(':', 1)[1].strip()
		except IndexError:
			error('Configuration problem: Could not parse \'listen\' parameter.',
				fatal=True)
		except AttributeError:
			error('Configuration problem: Could not parse \'listen\' parameter.',
				fatal=True)
			
		self.address = (addr, int(port))
		self.ctx = DaemonContext()
		self.ctx.signal_map = {
			SIGTERM: self.terminate,
			SIGQUIT: self.terminate,
			SIGHUP: self.reload,
		}

		if self.conf.has('debug'):
			self.ctx.stderr = sys.stderr

		self._parse_access_rules()

		# init plugins
		self._init_plugins()
		
		self.ctx.pidfile = LockFile(self.conf.get('pid_file'), acquire_timeout=-1)
		self.server = None
	
	def _parse_access_rules(self):
		# access control
		hosts = self.conf.get('allow_hosts').strip()

		if hosts == '*' or hosts == '':
			self.allow_hosts = None
		else:
			self.allow_hosts = [h.strip() for h in hosts.split(',')]

	def _init_plugins(self):
		plugins = self.conf.get('plugins').strip()
		import djm.plugins

		plugin_dir = os.path.dirname(os.path.abspath(djm.plugins.__file__))
		self.plugins = []
			
		if plugins == '':
			error('Configuration problem: No active plugins.',
				fatal=True)
		else:
			plugins = [p.strip() for p in plugins.split(',')]
			try:
				for plugin in plugins:
					file_, path_, desc_ = find_module(plugin, [plugin_dir])
					plugin_mod = load_module(plugin, file_, path_, desc_)
					# Load and initialize plugin object
					plugin_class = getattr(plugin_mod, plugin.capitalize())
					self.plugins.append(plugin_class(self.conf))
			except ImportError as e:
				info(e)
				error('Plugin not found: %s' % (plugin), fatal=True)
			# TODO: close file_?

	def terminate(self, *args):
		'''@callback (SIGTERM handler)'''
		info('Policy daemon terminating.')
		self.server.stop()
		sys.exit(1)	
	
	def reload(self, *args):
		'''@callback (SIGHUP handler)'''
		info('Policy daemon reloading')
		self.conf = ConfParser()

		# Global configuration parameters which can't be handled
		# by reload are: listen, servers, plugins
		# Note that plugins should treat conf parameter as volatile
		for p in self.plugins:
			p.set_conf(self.conf)

		self._parse_access_rules()


	def handle_request(self, sock, address):
		'''@callback (StreamServer worker)

		Parse policy request data supplied by Postfix and respond
		with Postfix access(5) string
		'''
		addr, port = address

		if self.allow_hosts and addr not in self.allow_hosts:
			warn('Access denied for host %s' % (addr))
			return

		try:
			postfix = sock.makefile()
			request = {}
			for line in postfix:
				if not line or line in ('\n', '\r\n'):
					# \n is for compliant clients
					# \r\n for telnet or similar
					break
				else:
					try:
						data = line.strip().split('=')
						attr = data[0].strip()
						value = data[1].strip()
						request[attr] = value
					except IndexError:
						warn('Malformatted policy request data: %s' % (line))
						break
		except socket.error as e:
			info(e)
			return

		if 'request' not in request:
			postfix.write(PolicyResponse().reject_invalid())
			postfix.flush()
			return

		# don't police stressed Postfix
		if 'stress' in request and request['stress'] == 'yes':
			postfix.write(PolicyResponse().dunno())
			postfix.flush()
			return

		response = None

		for plugin in self.plugins:
			response = plugin(request)

			if response.action in ('reject', 'defer_if_permit',
					'defer_if_reject'):
				postfix.write(response)
				postfix.flush()
				return

		if response:
			# The last positive response in plugin call chain
			postfix.write(response)
		else:
			# Failsafe policy response
			postfix.write(PolicyResponse().dunno())

		postfix.flush()
		
	def run(self):
		try:
			with self.ctx:
				self.server = StreamServer(self.address, self.handle_request,
					spawn=int(self.conf.get('servers')))
				closelog()
				openlog('djmd'.encode('ascii'))
				info('Policy daemon started')
				self.server.serve_forever()
		except AlreadyLocked:
			error('PID file \'%s\' ' % (self.conf.get('pid_file')) +
				'already exists. Either the daemon is already running' + 
				' or previous session crashed.',
				 fatal=True)
		except LockFailed:
			error('Could not create PID file \'%s\'.' % 
				(self.conf.get('pid_file')), fatal=True)
