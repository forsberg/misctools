#!/usr/bin/env python

import re
import sys
import datetime
import netrc
import getopt
import urlparse
from mechanize import Browser

def backup_database(url, username, password, database, destination):
    if not url.endswith("/"):
        url+="/"
    br = Browser()
    br.open(url)

    br.select_form(name="login_form")
    br["pma_username"] = username
    br["pma_password"] = password

    login_response = br.submit()

    resp = br.follow_link(url_regex=re.compile("^main\.php.*"))
    resp = br.follow_link(url_regex=re.compile("\./server_export\.php.*"))

    br.select_form(name="dump")
    # Select SQL export
    br.find_control(name="what").get(id="radio_plugin_sql").selected = True
    # Select database to export
    br.find_control(name="db_select[]").get(name=database).selected = True
    # Add SQL DROP statements to export
    br.find_control(name="sql_drop").get(id="checkbox_sql_drop").selected = True
    # Send as file
    br.find_control(name="asfile").get("sendit").selected = True

    # Compress file with bzip
    br.find_control(name="compression").get(id="radio_compression_bzip").selected = True

    ret = br.submit()
    open(destination, 'w').write(ret.read())

def usage():
    print >> sys.stderr, """Usage: %s [OPTION] <phpmysql url> <database name> <output filename>

Options:
--user=USERNAME      Database user name.
--password=PASSWORD  Database password.
--verbose            Print out some extra info.
--dryrun             Do nothing except read configuration. Use with --verbose

A better alternative to providing username and password on the commandline
where they will be exposed to other users through the process list, is to
store the information in ~/.netrc, where it will be read by this script.

<output filename> is run through datetime.datetime.now().strftime(). The following strings can
also be part of the filename and are subsituted accordingly:

  %%(dbname)s      database name as given on command line
  %%(netloc)s      netloc part of phpmysql url
""" % sys.argv[0]
    sys.exit(1)
    
if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "", ["user=", "password=", "verbose", "dryrun", "help"])
    user = None
    password = None
    verbose = False
    dryrun = False

    if len(args) < 3:
        usage()

    url = args[0]
    dbname = args[1]
    output = args[2]
    
    for opt, optarg in opts:
        if "--user" == opt:
            user = optarg
        if "--password" == opt:
            password = optarg
        if "--dryrun" == opt:
            dryrun = True
        if "--verbose" == opt:
            verbose = True
        if "--help" == opt:
            usage()

    u = urlparse.urlparse(url)
    netloc = u.netloc

    if not user:
        n = netrc.netrc()
        info = n.authenticators(netloc)
        if not info:
            print >> sys.stderr, "--user not provided and info not found in ~/.netrc file"
            print >> sys.stderr
            usage()
        (user, password) = (info[0], info[2])

    if verbose:
        print >> sys.stderr, "Fetching database %(dbname)s from %(url)s, connecting as %(user)s" % locals()

    output = datetime.datetime.now().strftime(output) % locals()

    if verbose:
        print >> sys.stderr, "Writing saved SQL to %(output)s" % locals()

    if not dryrun:
        backup_database(url, user, password, dbname, output)
