# coding: utf-8

# $Revision$

# Don't Judge Mail - Postfix Policy Daemon
#
# DJM runtime configuration and command line parsing.
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

from djm.logging import error

try:
	import configparser
except ImportError:
	import ConfigParser as configparser

from argparse import ArgumentParser

class ConfParser(object):
	def __init__(self):
		'''Thin wrapper for ConfigParser and ArgumentParser

			* Supports "non-mandatory" conf options
			* Supports "default" values for conf options
			* Command line options can override conf options
			* You don't need to specify section for get() method
		'''

		cmd_parser = ArgumentParser(description='Don\'t Judge Mail - Postfix Policy Daemon')
		cmd_parser.add_argument('--conf', dest='conf_file',
			default=None)
		cmd_parser.add_argument('--version', action='store_true', default=False)
		# Configuration overrides
		# NOTE: Don't specify defaults! Defaults should be provided
		#       in configuration file
		cmd_parser.add_argument('--allow-hosts', metavar='HOST1,HOST2')
		cmd_parser.add_argument('--debug', action='store_true')
		cmd_parser.add_argument('--listen', metavar='IP_ADDR:PORT')
		cmd_parser.add_argument('--pid-file', metavar='/PATH/TO/daemon_name.pid')
		cmd_parser.add_argument('--plugins', metavar='PLUGIN1,PLUGIN2')
		cmd_parser.add_argument('--servers', metavar='N')

		self.cmdline = vars(cmd_parser.parse_args())

		if 'version' in self.cmdline and self.cmdline['version']:
			from djm.__version__ import version
			print('djmd v%s'%(version))
			sys.exit(0)


		try:
			self.parser = configparser.SafeConfigParser()

			if not self.cmdline['conf_file']:
				# OK, no conf file. Add default section where the cmdline args
				# shall be saved (btw, one can't add section named 'default')
				self.parser.add_section('djmd')
			else:
				cf = open(self.cmdline['conf_file'])
				self.parser.readfp(cf)
				cf.close()

			for k, v in self.cmdline.items():
				if v:
					self.parser.set('djmd', k, str(v))
		except configparser.Error as e:
			error('Configuration problem: %s' % (e), sys.stderr)
		except EnvironmentError:
			error('Could not open configuration file: %s' %
				(self.cmdline['conf_file']), sys.stderr)


	def get(self, option, section='djmd', default=None, mandatory=True):
		try:
			return self.parser.get(section, option)
		except configparser.NoOptionError as e:
			if not mandatory:
				return default
			else:
				error('Configuration problem: %s' % (e))
		except configparser.Error as e:
			error('Configuration problem: %s' % (e))


	def set(self, option, value, section='djmd'):
		try:
			self.parser.set(section, option, value)
		except configparser.NoSectionError as e:
			error('Configuration problem: %s' % (e))


	def has(self, option, section='djmd'):
		return self.parser.has_option(section, option)


	def items(self, section='djmd'):
		try:
			return self.parser.items(section)
		except configparser.Error as e:
			error('Configuration problem: %s' % (e))

