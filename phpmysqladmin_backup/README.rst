backup.py is a script that automatically logs on to a phpMyAdmin_
site, gets its export page, then downloads a bzip2-compressed database
dump of a specific database by submitting the form. 

This is useful in situations where the only access to the database is
via a phpMyAdmin, and there are no other ways to get a SQL dump for
backup purposes, for example at low-cost webhosting companies. 

Requirements: Python and its `mechanize package`_ (available as
``python-mechanize`` on Debian and Ubuntu).

Run ./backup.py --help for usage. 

Related blog post `here <https://efod.se/blog/archive/2010/02/06/phpmyadmin-sql-dump>`_

.. _phpMyAdmin: http://www.phpmyadmin.net/home_page/index.php
.. _mechanize package: http://wwwsearch.sourceforge.net/mechanize/
