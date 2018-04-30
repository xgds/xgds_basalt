#! /usr/bin/env python

import django
from datetime import datetime
import pytz
django.setup()
from basaltApp.models import BasaltImageSet, BasaltSingleImage, BasaltVehicle
from geocamTrack.utils import getClosestPosition

hawaiiStandardTime = pytz.timezone('US/Hawaii')
startTime = datetime(2016, 11, 8, 0, 0, 0, tzinfo=hawaiiStandardTime)
endTime = datetime(2016, 11, 9, 0, 0, 0, tzinfo=hawaiiStandardTime)
ev1Vehicle = BasaltVehicle.objects.get(name="EV1")

imgList = BasaltImageSet.objects.filter(acquisition_time__gte=startTime).filter(acquisition_time__lte=endTime)

print "Found %d images." % imgList.count()

for img in imgList:
    position = getClosestPosition(vehicle=ev1Vehicle, timestamp=img.acquisition_time)
    if img.flight:
        print "F: %s, N: %s, P: %s" % (img.flight.name, img.name, position)
        singleImages = img.images
        print "  Images:"
        for si in singleImages.all():
            print "    Thumb: %s (%s x %s)" % (si.thumbnail, si.width, si.height)
    else:
        position = getClosestPosition(vehicle=ev1Vehicle, timestamp=img.acquisition_time)
        print "F: %s, N: %s, P: %s" % ("<none>", img.name, position)
        singleImages = img.images
        print "  Images:"
        for si in singleImages.all():
            print "    Thumb: %s (%s x %s)" % (si.thumbnail, si.width, si.height)
