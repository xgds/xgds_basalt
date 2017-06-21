#! /usr/bin/env python

import django
from datetime import datetime
import pytz
django.setup()
from basaltApp.models import BasaltImageSet, BasaltSingleImage
from geocamTrack.utils import getClosestPosition

hawaiiStandardTime = pytz.timezone('US/Hawaii')
startTime = datetime(2016, 11, 8, 0, 0, 0, tzinfo=hawaiiStandardTime)
endTime = datetime(2016, 11, 9, 0, 0, 0, tzinfo=hawaiiStandardTime)

imgList = BasaltImageSet.objects.filter(creation_time__gte=startTime).filter(creation_time__lte=endTime)

print "Found %d images." % imgList.count()

for img in imgList:
    if img.flight:
        print img.flight.name
        singleImages = img.images
        print "  Images:"
        for si in singleImages.all():
            print "    Thumb: %s (%s x %s)" % (si.thumbnail, si.width, si.height)
    else:
        print "<none>"
