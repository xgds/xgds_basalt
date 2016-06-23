#! /usr/bin/env python
# __BEGIN_LICENSE__
#Copyright (c) 2015, United States Government, as represented by the 
#Administrator of the National Aeronautics and Space Administration. 
#All rights reserved.
#
#The xGDS platform is licensed under the Apache License, Version 2.0 
#(the "License"); you may not use this file except in compliance with the License. 
#You may obtain a copy of the License at 
#http://www.apache.org/licenses/LICENSE-2.0.
#
#Unless required by applicable law or agreed to in writing, software distributed 
#under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR 
#CONDITIONS OF ANY KIND, either express or implied. See the License for the 
#specific language governing permissions and limitations under the License.
# __END_LICENSE__

from glob import glob
from datetime import datetime
import re
import os
import m3u8
import pytz
import optparse
import time
import django
django.setup()

from django.conf import settings
from basaltApp.models import BasaltFlight
from xgds_video.models import VideoSegment

FLIGHT_BASE = settings.DATA_ROOT

def getCreateTimeFromFilename(imageFilename):
    nameMatch = re.match("([0-9]{4})([0-9]{2})([0-9]{2})([A-Z])_"\
                         "([0-9]{2})_([0-9]{2})_([0-9]{2})", imageFilename)
    if nameMatch:
        flightName = "%s%s%s%s" % (nameMatch.group(1), nameMatch.group(2),
                                   nameMatch.group(3), nameMatch.group(4))
        timestamp = datetime.datetime(int(nameMatch.group(1)),
                                      int(nameMatch.group(2)),
                                      int(nameMatch.group(3)),
                                      int(nameMatch.group(5)),
                                      int(nameMatch.group(6)),
                                      int(nameMatch.group(7)))
        return (flightName, timestamp)


parser = optparse.OptionParser('usage: %prog')
parser.add_option('-f', '--flight', dest="flight",
                  help='flight name [%default]')
opts, args = parser.parse_args()

print "Searching for flight:", opts.flight

flightObj = BasaltFlight.objects.get(name=opts.flight)
print "Got flight %s(%s)" % (flightObj.name, flightObj.uuid)
print "Segment path: %s/%s/Video/Recordings/Segment*" % (FLIGHT_BASE, opts.flight)
segmentDirs = glob("%s/%s/Video/Recordings/Segment*" % (FLIGHT_BASE, opts.flight))
segmentDirs = sorted(segmentDirs)

print "Found %d Segment directories" % len(segmentDirs)

for i, dir in enumerate(segmentDirs):
    videoChunks = glob("%s/*.ts" % dir)
    videoChunks = sorted(videoChunks, key = lambda chunk: int(re.sub(".+prog_index-(\d+).ts", "\\1", chunk)))
    if len(videoChunks) > 0:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(videoChunks[1])
        index = m3u8.load('%s/%s' % (dir, 'prog_index.m3u8'))
        m3u8segment = index.segments[0]
        duration = m3u8segment.duration
        startTime = mtime - duration
        startDT = datetime.fromtimestamp(startTime, pytz.utc)
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(videoChunks[-1])
        endTime = mtime
        endDT = datetime.fromtimestamp(endTime, pytz.utc)
        print "Segment%03d: Start: %s End: %s" % (i, startDT, endDT)
