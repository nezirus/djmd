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
from argparse import ArgumentParser
try:
	import configparser
except ImportError:
	import ConfigParser as configparser

from djm.logging import error

class ConfParser(object):
	'''Thin wrapper for ConfigParser and ArgumentParser
		* Supports "non-mandatory" conf options
		* Supports "default" values for conf options
		* Command line options can override conf options
		* You don't need to specify section for get() method
	'''

	def __init__(self, default_section='djmd'):
		'''
		Keyword arguments:
		default_section -- Section name for get() calls
		'''

		self.default_section = default_section
		cmd_parser = ArgumentParser(description=
			'Don\'t Judge Mail - Postfix Policy Daemon')

		# Options with no counterpart in conf file
		cmd_parser.add_argument('--conf', dest='conf_file')
		cmd_parser.add_argument('--version', action='store_true', default=False)

		# Overridable options
		# Defaults should be provided in configuration file, not here
		cmd_parser.add_argument('--allow-hosts', metavar='HOST1,HOST2')
		cmd_parser.add_argument('--debug', action='store_true')
		cmd_parser.add_argument('--listen', metavar='IP_ADDR:PORT')
		cmd_parser.add_argument('--pid-file', metavar='/PATH/TO/daemon_name.pid')
		cmd_parser.add_argument('--plugins', metavar='PLUGIN1,PLUGIN2')
		cmd_parser.add_argument('--servers', metavar='N')
		cmd_parser.add_argument('--init-database', action='store_true')

		self.cmdline = vars(cmd_parser.parse_args())

		if 'version' in self.cmdline and self.cmdline['version']:
			from djm.__version__ import version
			print('djmd v%s'%(version))
			sys.exit(0)

		try:
			self.parser = configparser.SafeConfigParser()

			if 'conf_file' not in self.cmdline:
				# OK, no conf file. Add default section where the cmdline args
				# shall be saved (btw, one can't add section named 'default')
				self.parser.add_section(default_section)
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

	def get(self, option, section=None, default=None, mandatory=True):
		'''Get an option value for the named section

		Keyword arguments:
		section -- Section name override
		mandatory -- Enforce existance of option value
		default -- Default value for non mandatory options
		'''

		s = section if section else self.default_section
		try:
			return self.parser.get(s, option)
		except configparser.NoOptionError as e:
			if not mandatory:
				return default
			else:
				error('Configuration problem: %s' % (e))
		except configparser.Error as e:
			error('Configuration problem: %s' % (e))

	def set(self, option, value, section=None):
		'''Set the given option to the specified value

		Keyword arguments:
		section -- Section name override
		'''
		s = section if section else self.default_section
		try:
			self.parser.set(s, option, value)
		except configparser.NoSectionError as e:
			error('Configuration problem: %s' % (e))

	def has(self, option, section=None):
		'''If the given section exists, and contains the given option,
		return True; otherwise return False.

		Keyword arguments:
		section -- Section name override for set() calls
		'''
		s = section if section else self.default_section
		return self.parser.has_option(s, option)

	def items(self, section=None):
		'''Return a list of (name, value) pairs for each option
		in the given section.

		Keyword arguments:
		section -- Section name override
		'''
		s = section if section else self.default_section
		try:
			return self.parser.items(s)
		except configparser.Error as e:
			error('Configuration problem: %s' % (e))
