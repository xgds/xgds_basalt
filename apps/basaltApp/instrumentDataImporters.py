import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

from cStringIO import StringIO
import pytz

import spc  # library for reading SPC format spectra
from geocamUtil.TimeUtil import timeZoneToUtc
from geocamTrack.utils import getClosestPosition
from xgds_planner2.utils import getFlight
from basaltApp.models import FtirDataProduct, AsdDataProduct, PxrfDataProduct, FtirSample, ScienceInstrument, BasaltTrack

FTIR = "ftir"

def lookupFlightInfo(utcStamp, timezone, resource, defaultTrackName):
    #
    # Get flight and track info and find location of sample if available
    #
    flight = None
    try:
        flight = getFlight(utcStamp, resource.vehicle)
        if flight:
            trackName = flight.name
        elif resource:
            trackName = resource.name
        else:
            trackName = defaultTrackName
        track = BasaltTrack.getTrackByName(trackName)
        if not track:
            if trackName == defaultTrackName:
                track = BasaltTrack(name=defaultTrackName)
            else:
                track = BasaltTrack(name=defaultTrackName,
                                    resource=resource,
                                    timezone=timezone)
        sampleLocation = getClosestPosition(track=track, 
                                            timestamp=utcStamp,
                                            resource=resource)
    except:
        sampleLocation = None
    return (flight, sampleLocation)


def pxrfDataImporter(instrument, portableDataFile, manufacturerDataFile,
                     timestamp, timezone, resource, user=None):
    instrumentData = portableDataFile.read()
    instrumentData = instrumentData.translate(None, "\x00")
    utcStamp = timeZoneToUtc(timezone.localize(timestamp))
    importSummary = """Import from %s
Uploaded filename: %s
Timestamp (Orig): %s
Timestamp (UTC): %s
Original Timezone: %s
Tracking resource: %s\n
INSTRUMENT DATA
%s""" % (instrument["displayName"],
         portableDataFile.name,
         timestamp,
         utcStamp,
         timezone,
         resource,
         instrumentData)

    return HttpResponse(importSummary, content_type="text/plain")

def asdDataImporter(instrument, portableDataFile, manufacturerDataFile, timestamp, 
                    timezone, resource, user=None):
    instrumentData = portableDataFile.read()
    instrumentData = instrumentData.translate(None, "\x00")
    utcStamp = timeZoneToUtc(timezone.localize(timestamp))
    importSummary = """Import from %s
Uploaded filename: %s
Timestamp (Orig): %s
Timestamp (UTC): %s
Original Timezone: %s
Tracking resource: %s\n
INSTRUMENT DATA
%s""" % (instrument["displayName"],
         portableDataFile.name,
         timestamp,
         utcStamp,
         timezone,
         resource,
         instrumentData)

    #TODO need to get raw files and write this importer

    return HttpResponse(importSummary, content_type="text/plain")

def ftirDataImporter(instrument, portableDataFile, manufacturerDataFile,
                     utcStamp, timezone, resource, user=None):
    instrumentData = spc.File(portableDataFile)
    # Take slice b/c data has trailing tab
    dataTable = [r.split("\t")[0:2] for r in instrumentData.data_txt().split("\n") if r != '']
    instrument = ScienceInstrument.getInstrument(FTIR)

    (flight, sampleLocation) = lookupFlightInfo(utcStamp, timezone, resource, FTIR)
    
    dataProduct = FtirDataProduct(
        portable_data_file = portableDataFile,
        portable_file_format_name = "SPC",
        portable_mime_type = "application/octet-stream",
        acquisition_time = utcStamp,
        acquisition_timezone = timezone.zone,
        creation_time = datetime.datetime.now(pytz.utc),
        manufacturer_data_file = manufacturerDataFile,
        manufacturer_mime_type = "application/octet-stream",
        instrument = instrument,
        location = sampleLocation,
        flight = flight,
        resource = resource,
        creator=user
    )
    dataProduct.save()
    for wn, rf in dataTable[1:]:  # Slice starting @ 1 because 1 line is header
        sample = FtirSample(
            dataProduct = dataProduct,
            wavenumber = wn,
            reflectance = rf)
        sample.save()

    return HttpResponseRedirect(reverse('search_map_single_object', kwargs={'modelPK':dataProduct.pk,
                                                                            'modelName':'FTIR'}))

