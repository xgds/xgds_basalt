#!/usr/bin/env python

# Run me from a directory filled with KML files you want to load into CouchDB
import glob
import sys
from datetime import datetime
import couchdb
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def get_exif_data(image):
    """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]

                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value

    return exif_data

dataFile = open(sys.argv[1],"r")
flist = dataFile.readlines()
import couchdb
s = couchdb.Server()
db = s["basalt-file-store"]
flist = [f.rstrip() for f in flist]

for f in flist:
    print "Importing:", f
    try:
        img = Image.open(f)
    except:
        print "No file"
        img = None
        pass
    try:
      exifData = get_exif_data(img)
      print "  Time: %s" % exifData.get("DateTimeOriginal", None)
    except:
      print "  No EXIF?"
    # fpath = "xgds_map_server/%s" % f
    # db[fpath] = {"category":"xgds_map_server", "basename":f, "name":fpath,
    #              "creation_time":datetime.utcnow().isoformat()}
    # newDoc = db[fpath]
    # content = open(f,"rb").read()
    # db.put_attachment(newDoc, content, filename=f)
