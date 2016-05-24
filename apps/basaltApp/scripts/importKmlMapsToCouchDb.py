#!/usr/bin/env python

# Run me from a directory filled with KML files you want to load into CouchDB
import glob
from datetime import datetime
import couchdb

flist = glob.glob("*.kml")
import couchdb
s = couchdb.Server()
db = s["basalt-file-store"]

for f in flist:
    print "Importing:", f
    fpath = "xgds_map_server/%s" % f
    db[fpath] = {"category":"xgds_map_server", "basename":f, "name":fpath,
                 "creation_time":datetime.utcnow().isoformat()}
    newDoc = db[fpath]
    content = open(f,"rb").read()
    db.put_attachment(newDoc, content, filename=f)
