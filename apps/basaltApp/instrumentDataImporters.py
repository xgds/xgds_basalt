from django.http import HttpResponse
from cStringIO import StringIO

import spc  # library for reading SPC format spectra
from geocamUtil.TimeUtil import timeZoneToUtc

def pxrfDataImporter(instrument, dataFile, timestamp, timezone, resource):
    instrumentData = dataFile.read()
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
         dataFile.name,
         timestamp,
         utcStamp,
         timezone,
         resource,
         instrumentData)

    return HttpResponse(importSummary, content_type="text/plain")

def asdDataImporter(instrument, dataFile, timestamp, timezone, resource):
    instrumentData = dataFile.read()
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
         dataFile.name,
         timestamp,
         utcStamp,
         timezone,
         resource,
         instrumentData)

    return HttpResponse(importSummary, content_type="text/plain")

def ftirDataImporter(instrument, dataFile, timestamp, timezone, resource):
    instrumentData = spc.File(dataFile)
    utcStamp = timeZoneToUtc(timezone.localize(timestamp))
    # Take slice b/c data has trailing tab
    dataTable = [r.split("\t")[0:2] for r in instrumentData.data_txt().split("\n") if r != '']
    myData = StringIO()
    for c1,c2 in dataTable:
        myData.write("%s - %s\r\n" % (c1,c2))
    importSummary = """Import from %s
Uploaded filename: %s
Timestamp (Orig): %s
Timestamp (UTC): %s
Original Timezone: %s
Tracking resource: %s\n
INSTRUMENT DATA
%s""" % (instrument["displayName"],
         dataFile.name,
         timestamp,
         utcStamp,
         timezone,
         resource,
         myData.getvalue())

    return HttpResponse(importSummary, content_type="text/plain")
