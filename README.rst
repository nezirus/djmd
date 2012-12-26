Don't Judge Mail
================

Don't Judge Mail (DJM for short) is a daemon which implements
`Postfix Policy Delegation Protocol`_. It implements TCP server
which communicates with Postfix mail server.

All decision making is delegated to the policy plugins, which implement
desired functionality such as greylisting, quota/rate limiting.

DJM is licensed under the terms of GNU GPL v3 or later license,
see LICENSE for license text.

REQUIREMENTS
------------

DJM requires Python 2.6 or later 2.x version. As soon as Gevent supports
Python 3, we will support it too (though only Python 3.2 or later)

The following additional Python libraries are required:

 * Gevent 1.0 or later
 * python-daemon 1.5 or later
 * psycopg2 2.4.2 or later

DJM also requires a database where it will store runtime data. Currently we
support PostgreSQL_ database, support for other databases might be available
in the future.

We also recommend running connection pooling software for your database.
e.g. PgBouncer_ for PostgreSQL.

You should install them using your system package manager or you could
configure Python virtualenv for DJM.

For detailed installation and configuration instructions see INSTALL file.


.. _`Postfix Policy Delegation Protocol`: http://www.postfix.org/SMTPD_POLICY_README.html
.. _PostgreSQL: http://www.postgresql.org
.. _PgBouncer: http://wiki.postgresql.org/wiki/PgBouncer
