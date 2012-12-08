# coding: utf-8

# $Revision$

# Don't Judge Mail - Postfix Policy Daemon
#
# Syslog utilities.
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

import sys
import syslog

def openlog(name, options=syslog.LOG_PID, facility=syslog.LOG_MAIL):
	syslog.openlog(name, options, facility)

def closelog():
	return syslog.closelog()

def debug(msg):
	return syslog.syslog(syslog.LOG_DEBUG, 'Debug: %s' % (msg))

def info(msg):
	return syslog.syslog(syslog.LOG_INFO, '%s' % (msg))

def warn(msg):
	return syslog.syslog(syslog.LOG_WARNING, 'Warning: %s' % (msg))

def error(msg, fatal=False):
	syslog.syslog(syslog.LOG_ERR, 'Error: %s' % (msg))

	if fatal:
		print('Error: %s' % (msg), file=sys.stderr)
		syslog.syslog(syslog.LOG_ERR, 'Terminating ...')
		sys.exit(1)
