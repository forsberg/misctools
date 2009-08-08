#!/usr/bin/env python

import S3
import os
import sys

if not os.environ.has_key("AWS_ACCESS_KEY_ID") or not os.environ.has_key("AWS_SECRET_ACCESS_KEY"):
    sys.exit("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables before running this script")

access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]

conn = S3.AWSAuthConnection(access_key_id, secret_access_key)

if len(sys.argv) < 2: # No bucket specified on command line, list buckets
    print "Available buckets for this AWS access key id:"
    for bucket in conn.list_all_my_buckets().entries:
        print bucket.name, bucket.creation_date
else:
    bucket_name = sys.argv[1]
    resp = conn.list_bucket(bucket_name)
    if resp.http_response.status != 200:
        sys.exit("No such bucket (or not your bucket) %s" % bucket_name)
    i=1
    if not os.environ.has_key("ACTUALLY_DELETE"):
        sys.exit("Not deleting entries in bucket %s. Set environment variable ACTUALLY_DELETE=1 to actually delete" % (bucket_name))

    while True:
        for listentry in resp.entries:
            print "Deleting entry %s (#%d)" % (listentry.key, i)
            print conn.delete(bucket_name, listentry.key).message
            i+=1
        resp = conn.list_bucket(bucket_name)
        if resp.entries == []:
            break
        print "Re-fetched list of objects, got list of %d objects" % len(resp.entries)
    print "Deleting bucket %s" % bucket_name
    print conn.delete_bucket(bucket_name).message



    

    

