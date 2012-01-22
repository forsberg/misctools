#!/usr/bin/python2.4

# A script for migrating content from Plone to Django. Used with
# success in migration of http://efod.se/.  
# Script Author: Erik Forsberg <forsberg (at) efod (dot) se>

# Variables/hardcodings that most probably need to be modified because
# they are extremely specific to my setup of Plone and Django are
# marked with MODIFY. A lot of other things are specific to my
# Plone/Django products/applications as well, so this script is
# probably best as an example of how to do a migration, it should not
# be seen as a "turn-key solution".

# Note: We must run python 2.4 as Zope 2.9.6 which our Plone
# instance is running on doesn't support python 2.5


import os
import sys
import time
import datetime

from efod_se import PUBLISHED_STATUS, PRIVATE_STATUS, TYPE_REST, TYPE_HTML
from efod_se.efodblog.models import BlogEntry
from efod_se.tags.models import Tag
from efod_se.efodcms.models import Page
from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.conf import settings
from django.db import connection

# MODIFY: Folders we don't want to migrate.
folder_blacklist = ("/copy_of_images", "/images",)

for evar in ['INSTANCE_HOME', 'SOFTWARE_HOME']:
    if evar not in os.environ:
        print evar, "is missing from environment"
        print "Easiest way to get all environment variables is to modify a zopectl" 
        print "script, removing the last 'exec' line, then source it before running this script"
        sys.exit(1)

software_home = os.getenv("SOFTWARE_HOME")
instance_home = os.getenv("INSTANCE_HOME")

# MODIFY
sys.path = sys.path + [software_home, "/home/forsberg/dev/django/efod_se"]
    
from ZODB import FileStorage, DB
from Acquisition import aq_base

# Helper function for cases where acquisition does not, for some reason, work.
def findobject(parent, parts):
    if [] == parts:
        return parent
    return findobject(parent[parts[0]], parts[1:])

def settags(keywords, blogentry):
    for kw in keywords:
        existing = Tag.objects.filter(tag=kw)
        if 0 < len(existing):
            blogentry.tags.add(existing[0])
        else:
            tag = Tag(tag=kw)
            tag.save()
            blogentry.tags.add(tag)

    blogentry.save()

def main():
    
    # Set the environment variable DJANGO_SETTINGS_MODULE before
    # running this script, or you'll get a nasty exception. Example:
    # export DJANGO_SETTINGS_MODULE=efod_se.settings
    
    storage = FileStorage.FileStorage(os.path.join(instance_home, 
                                                   "var", "Data.fs"))
    db = DB(storage)
    connection = db.open()
    root = connection.root()
    app = root['Application']

    # MODIFY. Set this variable to match the name of your plone root in ZODB.
    ploneroot = app.efod_drift
    
    migrate_blogentries(app, ploneroot)
    
    migrate_plonefolder(app, None, ploneroot)

def migrate_plonefolder(app, parent, folder):
    # The correct way of doing this would be to run getDefaultPage on
    # the object, but that method requires a request parameter !=
    # None, and I don't know how to construct such an object. Let's
    # cheat by checking if there's a default_page property on the
    # folder.
    default_page = None
    try:
        default_page = aq_base(folder).default_page
    except AttributeError:
        pass

    if not default_page:
        default_page = "index.html"
    
    try:
        default_page = folder[default_page]
    except KeyError:
        default_page = None

    path = folder.absolute_url()[len(folder.portal_url()):]
    print "migrate_plonefolder", path, default_page

    if path in folder_blacklist:
        return

    page = create_page(parent, folder, content_obj=default_page)

    contents = folder.listFolderContents()
    for c in contents:
        if c == default_page:
            continue

        if c.portal_type == 'Folder':
            migrate_plonefolder(app, page, c)
        elif c.portal_type == 'Document':
            print "\t", c.absolute_url()
            create_page(page, c)
        else:
            print "**", c.absolute_url(), c.portal_type

            

def create_page(parent, obj, content_obj=None):
    path = obj.absolute_url()[len(obj.portal_url()):]
    portal_workflow = obj.portal_workflow
    
    status = PUBLISHED_STATUS
    if "" != path and (portal_workflow.getStatusOf("folder_workflow", obj) \
                          and portal_workflow.getStatusOf("folder_workflow", obj)["review_state"] == "private"):
        status = PRIVATE_STATUS

    contenttype = TYPE_REST
    if not content_obj:
        content_obj = obj

    content = None
    if content_obj.getField('text'):
        if content_obj.getField('text').getContentType(content_obj) == "text/html":
            contenttype = TYPE_HTML
        content = content_obj.getRawText()        
        content = content.replace("<p><br/></p>", "").replace("<p></p>", "")
    
    publish_date = obj.EffectiveDate()
    if 'None' == publish_date: # @!$%&!!
        publish_date = obj.created().strftime("%Y-%m-%d %H:%M:%S")

    print "publish_date", publish_date
        
    page = Page(slug=obj.id, title=obj.Title(),
                content = content,
                parent = parent,
                last_modified = obj.modified().strftime("%Y-%m-%d %H:%M:%S"),
                creationdate = obj.created().strftime("%Y-%m-%d %H:%M:%S)"),
                publish_date = publish_date,
                status = status,
                contenttype = contenttype)
    page.save()
    return page

def getDiscussion(obj, replies, counter):
    rs = obj.portal_discussion.getDiscussionFor(obj).getReplies()
    rs.sort(lambda x, y: cmp(x.modification_date, y.modification_date))
    for r in rs:
        replies.append({"depth":counter, "object":r})
        getDiscussion(r, replies, counter=counter+1)
    

def migrate_blogentries(app, ploneroot):
    # Migrate weblog entries.
    
    blogbrains = ploneroot.portal_catalog.searchResults(portal_type="WeblogEntry")

    for br in blogbrains:
        print "Handling", br.getId
        # Normally, I would have done this:
        # obj = br.getObject()
        # For some reason, this doesn't work with Quills Blog(!)  So,
        # instead, we recurse down to the real object. Slow, but seems
        # to work. Ah, the wonderful mystery of the ZODB and Plone!
        splitpath = br.getPath().split("/")[1:] # Skip the first, empty, string
        obj = findobject(app, splitpath)
        
        status = PUBLISHED_STATUS
        if "private" == br.review_state:
            status = PRIVATE_STATUS

        if obj.getField('text').getContentType(obj) == "text/html":
            contenttype = TYPE_HTML
        else:
            contenttype = TYPE_REST

        keywords = obj.Subject()

        content = obj.getRawText()
        content = content.replace("<p><br/></p>", "").replace("<p></p>", "")

        print obj.modified(), obj.created(), obj.EffectiveDate()
        blogentry = BlogEntry(slug=obj.id, title=obj.Title(), 
                              content=content, 
                              last_modified = obj.modified().strftime("%Y-%m-%d %H:%M:%S"),
                              creationdate = obj.created().strftime("%Y-%m-%d %H:%M:%S"),
                              publish_date = obj.EffectiveDate(),
                              status = status,
                              contenttype = contenttype)



        # Must save before updating many-to-many relationship in settags.
        blogentry.save()

        settags(keywords, blogentry)

        discussion_items = []
        getDiscussion(obj, discussion_items, 0)

        for item in discussion_items:
            print "\t"*item["depth"], item["object"].title

            object = item['object']
            
            # Note: object.email only seems to exist if you have used
            # qPloneComments.
            email = ""
            if hasattr(object, "email"):
                email = object.email

            # We're on Python 2.4, where datetime.datetime.strptime doesn't exist
            t = time.strptime(object.CreationDate(), 
                              '%Y-%m-%d %H:%M:%S') 
            # Not sure about the timezone here, but I don't care.
            submit_date = datetime.datetime.fromtimestamp(time.mktime(t))
                
            c = Comment(content_type=ContentType.objects.get_for_model(blogentry),
                        object_pk=force_unicode(blogentry._get_pk_val()),
                        user_name = object.Creator(),
                        user_email = email,
                        submit_date=submit_date,
                        comment = object.text,
                        site_id = settings.SITE_ID,
                        is_public = True,
                        is_removed = False,
                        )
            c.save()


if "__main__" == __name__:
    main()



