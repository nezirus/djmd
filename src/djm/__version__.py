# coding: utf-8
from __future__ import unicode_literals

version_info = [1, 0, 0, 'b', 2]
version = '.'.join([str(x) for x in version_info[0:3]])

# Final versions should not have anything except X.Y.Z in version string
if version_info[3] != 'final':
	version +=  version_info[3] + str(version_info[4])
