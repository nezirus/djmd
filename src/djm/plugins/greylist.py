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

class Greylist(PolicyPlugin):
	def __call__(self, request):
		conf = self.conf
		db_name = conf.get('database', 'plugin:greylist', 'default', mandatory=False)
		db = connect(conf, db_name)

		return PolicyResponse().dunno()

