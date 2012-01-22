#!/usr/bin/python

# A script that reads efodcms and efodblog entries and replaces
# references to images with new URLs under the /media/ directory of
# the new django-based site.
# Should be run after plone2efod_django.py.
# Script Author: Erik Forsberg <forsberg (at) efod (dot) se>.


import re
import os
import sys
import urllib
from HTMLParser import HTMLParser
from httplib import HTTPConnection, HTTP_PORT

OLDHOST="efod.se"
OLDPORT=HTTP_PORT

# a html parser that finds img tags and a tags referring to images and
# adds the URLs to a list which will then be used later on.
class FindIMG(HTMLParser):
    def __init__(self, content):
        HTMLParser.__init__(self)
        self.imgurls = []
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        if "img" == tag:
            for a, v in attrs:
                if u'src' == a:
                    self.imgurls.append(v)
        if "a" == tag:
            for a, v in attrs:
                if u'href' == a and (v.endswith(".jpg") or 
                                     v.endswith(".pdf") or 
                                     v.endswith(".txt") or 
                                     v.endswith(".tar.gz") or 
                                     v.endswith(".conf") or 
                                     v.endswith(".gpg")):
                    self.imgurls.append(v)


from efod_se.efodblog.models import BlogEntry
from efod_se.efodcms.models import Page
from efod_se.tags.models import Tag
from efod_se import settings, TYPE_HTML, TYPE_REST

from django.template import Template


htmlentries = list(BlogEntry.objects.filter(contenttype=TYPE_HTML)) + \
    list(Page.objects.filter(contenttype=TYPE_HTML))
restentries = list(BlogEntry.objects.filter(contenttype=TYPE_REST)) + \
    list(Page.objects.filter(contenttype=TYPE_REST))

conn = HTTPConnection(OLDHOST, OLDPORT)

def fiximg(url, entry):
    print "fiximg", url, entry
    if url.startswith("http://"):
        return

    entrydir = os.path.dirname(entry.get_absolute_url())
    path = os.path.normpath(os.path.join(entrydir, url)) 

    conn.request("HEAD", path)
    resp = conn.getresponse()
    resp.read() # Must read whole respone before making new request

    if 200 != resp.status:
        print path, resp.status, "\"%s\"" % resp.getheader("content-type", "NO CONTENT TYPE")
        return

    imgpath = os.path.join(settings.MEDIA_ROOT, "migrated", path[1:].replace("/", "-")).strip()
    if not os.path.exists(os.path.dirname(imgpath)):
        os.makedirs(os.path.dirname(imgpath))

    if not os.path.exists(imgpath):
        print "Getting", imgpath, "from", OLDHOST
        urllib.urlretrieve("http://%s:%d%s" % (OLDHOST, OLDPORT, path),
                           imgpath)
    
    newurl = imgpath[len(settings.MEDIA_ROOT):]
    e.content = e.content.replace(url, "{{ MEDIA_URL }}" + newurl)

# First, we'll loop through all html entries, and parse them with FindIMG.
for e in htmlentries:
    for url in FindIMG(e.content).imgurls:
        fiximg(url, e)
    e.save()

# Then, loop through all reStructured text entries.
for e in restentries:
    if None == e.content: 
        continue
    all = re.findall('image::\s+([^\n]+)', e.content)
    if not all:
        continue
    for url in all:
        fiximg(url, e)
    e.save()



