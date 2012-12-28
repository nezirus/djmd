#!/usr/bin/env python
# coding: utf-8

# $Revision$

# Don't Judge Mail setup script.
#
# Copyright (C) 2012-2013 Adis Nezirović <adis at localhost.ba>
#
# 'python setup.py install', or
# 'python setup.py --help' for more options
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

# TODO: Distutils doesn't handle Unicode
# from __future__ import unicode_literals

import sys

if not hasattr(sys, 'version_info') or sys.version_info < (2, 6, 0, 'final'):
    raise SystemExit('Don\'t Judge Mail requires Python 2.6 or later.')

# Retrieve version string - evil I know ;-)
import parser
eval(parser.suite(open('src/djm/__version__.py').read()).compile())

from distutils.core import setup

setup(name='djm',
	version=version,
	author='Adis Nezirovic',
	author_email='adis at localhost.ba',
	url='http://djm.localhost.ba',
	description='Postfix Policy Daemon',
	long_description='Postfix Policy Daemon written with Python and Gevent',
	license='GNU GPL v3+',
	packages=['djm', 'djm/plugins'],
	package_dir={'djm': 'src/djm', 'djm/plugins': 'src/djm/plugins'},
	scripts=['src/djmd'],
	data_files=[
		('share/doc/djm', ['LICENSE', 'README.rst', 'INSTALL.rst', 'scripts/rc.djmd']),
		('/etc', ['src/djmd.conf']),
	],
	requires=('gevent (>=1.0)', 'python_daemon (>=1.5)', 'psycopg2 (>=2.4.2)'),
	keywords=('postfix', 'policy', 'daemon', 'greylisting', 'quota', 'rbl'),
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Intended Audience :: System Administrators',
		'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
		'Operating System :: POSIX',
		'Operating System :: POSIX :: Linux',
		'Operating System :: POSIX :: BSD',
		'Operating System :: Unix',
		'Programming Language :: Python',
		'Topic :: Communications :: Email :: Filters',
	],
)

