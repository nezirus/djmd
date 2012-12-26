Installation
============

DJM requires Python 2.6 or later 2.x version. As soon as Gevent supports
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

You should install them using your system package manager or you could
configure Python virtualenv for DJM (see `Local installation`)

System wide installation
------------------------

In the future, we hope that it will be possible to install DJM from your
distribution software repository. For now, you'll need to download the
source tarball, unpack it, and run installation (as root):

  # python setup.py install

Edit configuration file (``/etc/djmd.conf``) to your needs.
Please make sure that data in ``database:default`` configuration section
is correct. (Database should exists, and database user should have "owner"
privileges)

Run database installation script with:

  # djmd --init-database

That's it, you should be able to run DJM with:

  # djmd

or
  
  # djmd --conf-file /path/to/conf


Check system log and mail log for any error messages.


Local installation
------------------

You can also install and run DJM using virtualenv and pip:

  * Checkout DJM from source repository
  * Run ``.bootstrap/install.sh`` which will prepare virtualenv
  * Prepare startup script (see ``scripts/rc.djmd``)
  * Edit configuration file (``src/djmd.conf``)
  * Run database installation script:
      $ scripts/rc.djmd init-database
  * Run djmd
      $ scripts/rc.djmd start


Configuring Postfix
-------------------

TODO

Configuring PostgreSQL
----------------------

TODO

.. _`Postfix Policy Delegation Protocol`: http://www.postfix.org/SMTPD_POLICY_README.html
.. _PostgreSQL: http://www.postgresql.org
.. _PgBouncer: http://wiki.postgresql.org/wiki/PgBouncer
.. _Gevent: http://www.gevent.org/
.. _python-daemon: http://pypi.python.org/pypi/python-daemon/
.. _psycopg2: http://initd.org/psycopg/
.. _argparse: http://code.google.com/p/argparse
