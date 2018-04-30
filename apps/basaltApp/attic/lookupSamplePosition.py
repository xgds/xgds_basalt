import django
django.setup()

import datetime
import pytz

from basaltApp.models import *
from geocamTrack.utils import getClosestPosition

missingPositionSampleList = []
startTime = datetime.datetime(2016,10,30,0,6,0,tzinfo=pytz.utc)
samples = BasaltSample.objects.filter(collection_time__gte = startTime).order_by("collection_time")
sampleCount = 0
missingPositionCount = 0
for sample in samples:
    if (not sample.track_position) and (not sample.user_position):
        if sample.vehicle:
            print "**** Processing: %s ****" % sample.name
            sample.track_position = getClosestPosition(timestamp=sample.collection_time, vehicle=sample.vehicle)
            if not sample.track_position:
                sample.track_position = getClosestPosition(timestamp=sample.collection_time, vehicle=sample.vehicle)
            if not sample.track_position:
                print "  No location found - adding to list of samples w/o position"
                missingPositionSampleList.append(sample.name)
                missingPositionCount += 1
            print "  Date: %s, vehicle: %s, Location: %s\n" % (sample.collection_time, sample.vehicle, sample.track_position)
            sample.save()
            sampleCount += 1
#     if sample.vehicle is None:
#         print "**** Processing: %s ****" % sample.name
#         sample.vehicle = BasaltVehicle.objects.get(name=settings.XGDS_SAMPLE_DEFAULT_COLLECTOR)
#         sample.track_position = getClosestPosition(timestamp=sample.collection_time, vehicle=sample.vehicle)
#         if not sample.track_position:
#             sample.track_position = getClosestPosition(timestamp=sample.collection_time, vehicle=BasaltVehicle.objects.get(name="EV1"))
#         if not sample.track_position:
#             print "  No location found - adding to list of samples w/o position"
#             missingPositionSampleList.append(sample.name)
#             missingPositionCount += 1
#         print "  Date: %s, vehicle: %s, Location: %s\n" % (sample.collection_time, sample.vehicle, sample.track_position)
#         sample.save()
#         sampleCount += 1

print "Processed %d samples. %d of them were missing position info" % (sampleCount, missingPositionCount)
f = open("SamplesMissingPositions.txt", "w")
for s in missingPositionSampleList:
    print >>f, s
f.close()
