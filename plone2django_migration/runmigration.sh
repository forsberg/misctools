#!/bin/bash


export INSTANCE_HOME=/var/lib/zope2.9/instance/efod.se-p2.5.1/
export SOFTWARE_HOME=/opt/Zope-2.9.6/lib/python/
export PYTHONPATH=$PYTHONPATH:~/dev/django/:~/dev/django/django-trunk/
export DJANGO_SETTINGS_MODULE=efod_se.settings

./plone2efod_django.py
./getimages.py
