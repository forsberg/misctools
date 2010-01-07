#!/usr/bin/python
# coding: utf-8
# This is a stupid little script I use to help my partner generate a
# list of the dates on which she and her friends have Knitting
# Cafés. One week it's Wednesday, the other it's Friday. And so on.
# Not very useful for anyone except me, but can be used as an example
# of some of the datetime module's features. I use this script as an
# example myself, that's why I keep it on github :-).

import os
import sys
import locale
import datetime

# Set LC_TIME to "the user's default settings", which seems to be
# what's in the script's environment. Python does not automatically use what's in the environment.
# We want the weekdays to be correct in the call to strftime() below.
locale.setlocale(locale.LC_TIME, "")

if len(sys.argv) < 3:
    sys.exit("Usage: %s <start date (YYYY-MM-DD)> <# of weeks>" % sys.argv[0])

startdate = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d")
numweeks = int(sys.argv[2])

week = datetime.timedelta(days=7)
twodays = datetime.timedelta(days=2)
startdate-=week # Compensate for the first week number being 1, below

for weeknum in range(1,numweeks):
    d = startdate + weeknum * week
    if not weeknum % 2:
        d+= twodays

    s = d.strftime("%A %d %b")

    if not weeknum % 2:
        s+=", Waynes"
    else:
        s+=", Espresso House"

    print s
    
    



