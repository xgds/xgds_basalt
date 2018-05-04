import django
django.setup()

import datetime
import pytz

from basaltApp.models import *
from xgds_planner2.models import Vehicle
from geocamTrack.utils import getClosestPosition

missingPositionSampleList = []
startTime = datetime.datetime(2016,6,14,0,6,0,tzinfo=pytz.utc)
samples = BasaltSample.objects.filter(collection_time__gte = startTime).order_by("collection_time")
sampleCount = 0
missingFlightCount = 0
missingFlightList = []
for sample in samples:
    if sample.flight is None:
        print "**** Processing: %s ****" % sample.name
        vehicle = Vehicle.objects.get(name=sample.vehicle.name)
        flight = BasaltFlight.objects.filter(start_time__lte = sample.collection_time).filter(end_time__gte = sample.collection_time).filter(vehicle=vehicle)
        if flight.count() == 0:
            print "  No flight found!  Hopefully this was out of sim sample"
            missingFlightList.append(sample.name)
        if flight.count() > 1:
            print "  Found more that one flight for this sample!"
        if flight.count() == 1:
            print "  Flight: %s" % flight[0].name
            sample.flight = flight[0]
            sample.save()

print "Processed %d samples. %d of them were missing flight info" % (sampleCount, missingFlightCount)
f = open("SamplesMissingFlights.txt", "w")
for s in missingFlightList:
    print >>f, s
f.close()
