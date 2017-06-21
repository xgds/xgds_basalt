#! /usr/bin/env python

import django
from datetime import datetime
import pytz
django.setup()
from basaltApp.models import BasaltImageSet, BasaltSingleImage

hawaiiStandardTime = pytz.timezone('US/Hawaii')
startTime = datetime(2016, 11, 8, 0, 0, 0, tzinfo=hawaiiStandardTime)
endTime = datetime(2016, 11, 9, 0, 0, 0, tzinfo=hawaiiStandardTime)

imgList = BasaltImageSet.objects.filter(creation_time__gte=startTime).filter(creation_time__lte=endTime)

print "Found %d images." % imgList.count()

for img in imgList:
    if img.flight:
        print img.flight.name
    else:
        print "<none>"
