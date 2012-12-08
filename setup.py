#!/usr/bin/env python
# coding: utf-8

#
# Don't Judge Mail setup script.
#
# './setup.py install', or
# './setup.py --help' for more options


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
	author='Adis Nezirović',
	author_email='adis at localhost.ba',
	url='http://djm.localhost.ba',
	description='Postfix Policy Daemon',
	long_description='Postfix Policy Daemon written with Python/gevent',
	license='GNU GPL v3+',
	packages=['djm'],
	package_dir={'djm': 'src/djm'},
	scripts=['src/djmd', 'scripts/rc.djmd'],
	data_files=[('doc/djm', ['COPYING', 'README']),],
	requires=('gevent (>=1.0)', 'python_daemon (>=1.5)', 'psycopg2 (>=2.4)'),
	keywords=('postfix', 'policy', 'daemon'),
	classifiers=[
		'Development Status :: 5 - Production/Stable',
		'Environment :: Console',
		'Intended Audience :: System Administrators',
		'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
		'Operating System :: POSIX :: Linux',
		'Operating System :: POSIX :: BSD',
		'Programming Language :: Python',
		'Topic :: Communications :: Email :: Filters',
	],
)

