import django
django.setup()

from basaltApp.models import *
from geocamTrack.utils import getClosestPosition

samples = BasaltSample.objects.all()
for sample in samples:
    if sample.resource is None:
        sample.resource = BasaltResource.objects.get(name=settings.XGDS_SAMPLE_DEFAULT_COLLECTOR)
        sample.track_position = getClosestPosition(timestamp=sample.collection_time, resource=sample.resource)
        sample.save()