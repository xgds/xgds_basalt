import django
django.setup()

from basaltApp.models import BasaltSample

allSamples = BasaltSample.objects.all().order_by('collection_time')
numbers = [sample.number for sample in allSamples]
numbers.sort()
sampleNumber = numbers[-1]

for sample in allSamples:
    if sample.station_number == None:
        if sample.name:
            print "updating legacy sample pk=%d" % sample.pk
            # move the number field to station number.
            # generate a unique sample number
            # generate a new sample name.
            station_number = sample.number
            sampleNumber = sampleNumber + 1
            number = sampleNumber
            sample.station_number = station_number
            sample.number = number
            try: 
                sample.name = sample.buildName()
            except:
                pass
            sample.save()            