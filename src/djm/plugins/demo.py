# coding: utf-8

# $Revision$

# Don't Judge Mail - Postfix Policy Daemon
#
# Demo plugin.
# Used for exploring Postfix SMTP Access Policy Delegation protocol
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
# Don't Judge Mail - Postfix Policy Daemon

from __future__ import print_function
from __future__ import unicode_literals

import sys

from djm.policy import PolicyPlugin, PolicyResponse
from djm.logging import info

class Demo(PolicyPlugin):
	def __call__(self, request):

		for k,v in request.items():
			info('%s:%s' % (k, v))

		info('---')

		return PolicyResponse().dunno()

