Don't Judge Mail
================

Don't Judge Mail (DJM for short) is a daemon which implements
`Postfix Policy Delegation Protocol`_. It implements TCP server
which communicates with Postfix mail server.

All decision making is delegated to the policy plugins, which implement
desired functionality such as greylisting, quota/rate limiting.

DJM is licensed under the terms of GNU GPL v3 or later license,
see LICENSE for license text.


Features
--------

- Fast, event based server (Gevent) which can handle large number of clients.

- All policy checking functionality implemented in various plugins.

- Integrated cron/task scheduler, for automatic database maintenance.


Requirements
------------

For DJM to be useful, you must run Postfix mail server, version 2.2 or later.

DJM also requires Python 2.6 or later 2.x version. As soon as Gevent supports
Python 3, we will support it too (though only Python 3.2 or later)

The following additional Python libraries are required:

 * Gevent_ 1.0 or later
 * python-daemon_ 1.5 or later
 * psycopg2_ 2.4.2 or later
 * argparse_ (only for Python 2.6, it is included in later Python versions)

DJM also requires a database where it will store runtime data. Currently we
support PostgreSQL_ database, support for other databases might be available
in the future.

We also recommend running connection pooling software for your database.
e.g. PgBouncer_ for PostgreSQL.

You should install Python requirements using your system package manager or you
could configure Python virtualenv for DJM with help of
``.bootstrap/install.sh`` file.

For detailed installation and configuration instructions see INSTALL.rst file.


Download
--------

You can clone source code repository from Bitbucket `project page`_, or GitHub mirror_.

Tarball archives and Linux distro packages might be available in the
`download area`_ on the Bitbucket.


.. _`Postfix Policy Delegation Protocol`: http://www.postfix.org/SMTPD_POLICY_README.html
.. _PostgreSQL: http://www.postgresql.org
.. _PgBouncer: http://wiki.postgresql.org/wiki/PgBouncer
.. _Gevent: http://www.gevent.org/
.. _python-daemon: http://pypi.python.org/pypi/python-daemon/
.. _psycopg2: http://initd.org/psycopg/
.. _argparse: http://code.google.com/p/argparse/
.. _`project page`: https://bitbucket.org/nezirus/djmd
.. _`mirror`: https://github.com/nezirus/djmd
.. _`download area`: https://bitbucket.org/nezirus/djmd/downloads
