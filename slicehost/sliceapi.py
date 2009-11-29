#!/usr/bin/env python

# Put your slicehost API password in one of the following files:
# "slicehost_api_password" in current working directory
# ~/.slicehost_api_password
# /etc/slicehost_api_password

import os
import sys
import pwd

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from pyactiveresource.activeresource import ActiveResource

class Zone(ActiveResource): pass

class Record(ActiveResource): pass

class SliceAPIException(Exception): pass
class SliceAPINoPasswordException(SliceAPIException): pass
class SliceAPINoSuchZone(SliceAPIException): pass
    

class SliceDNS(object):
    def __init__(self, origin):
        self.api_site = "https://%s@api.slicehost.com/" % self.find_api_password()
        Zone.set_site(self.api_site)
        Record.set_site(self.api_site)
        self.zone = None
        self.origin = origin

    def find_api_password(self):
        user = pwd.getpwuid(os.getuid())
        trypaths = [os.path.join(os.getcwd(), "slicehost_api_password"),
                    os.path.join(user.pw_dir, ".slicehost_api_password"),
                    "/etc/slicehost_api_password"]
        for p in trypaths:
            if os.path.exists(p):
                return file(p).read().strip()
        else:
            raise SliceAPINoPasswordException("No Slicehost API password found. Tried to read it from the following files:\n * %s" %
                               "\n * ".join(trypaths))

    def get_zone(self):
        if self.zone != None:
            return
        self.zone = Zone.find(origin = self.origin)
        if self.zone == []:
            raise SliceAPINoSuchZone("No zone with origin %s\n" % self.origin)
        self.zone = self.zone[0]

    def update_record(self, name, data, replace = True):
        self.get_zone()

        record = Record()
        if replace:
            records = Record.find(name=name, zone_id=str(self.zone.id))
            if len(records) > 1:
                for record in records[1:]:
                    record.destroy()
            if len(records) > 0:
                record = records[0]

        for (name, value) in data.items():
            setattr(record, name, value)

        record.zone_id = self.zone.id
        return record.save()

if "__main__" == __name__:

    if len(sys.argv) < 5:

        sys.exit("Usage: %s <origin> <record> <record type> <data> [ttl]" % sys.argv[0])

    (origin, record, record_type, data) = sys.argv[1:5]

    ttl = None
    if len(sys.argv) > 5:
        ttl = sys.argv[5]

    data = {"record_type":record_type, "data":data}
    if ttl:
        data["ttl"] = int(ttl)

    sd = SliceDNS(origin)
    sd.update_record(record, data)
    
    
    
    
