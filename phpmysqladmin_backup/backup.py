#!/usr/bin/env python

import re
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
    br.find_control(name="sql_drop").get(id="checkbox_sql_drop").selected = True
    br.find_control(name="asfile").get("sendit").selected = True

    br.find_control(name="compression").get(id="radio_compression_bzip").selected = True

    ret = br.submit()
    open(destination, 'w').write(ret.read())
    

    
 
