#__BEGIN_LICENSE__
# Copyright (c) 2015, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# The xGDS platform is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#__END_LICENSE__

import json
import datetime
import csv
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

from cStringIO import StringIO
import pytz

import spc  # library for reading SPC format spectra
from geocamUtil.TimeUtil import timeZoneToUtc
from geocamTrack.utils import getClosestPosition
from xgds_planner2.utils import getFlight
from basaltApp.models import FtirDataProduct, AsdDataProduct, PxrfDataProduct, PxrfSample, FtirSample, ScienceInstrument, BasaltTrack, AsdSample
from xgds_instrument.views import editInstrumentDataPosition

FTIR = "ftir"
ASD = "asd"
PXRF = "pxrf"

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


def pxrfDataImporter(instrument, portableDataFile, manufacturerDataFile, elementResultsCsvFile,
                     utcStamp, timezone, resource, name, description, minerals=None, user=None,
                     latitude=None, longitude=None, altitude=None):
    try:
        instrument = ScienceInstrument.getInstrument(PXRF)
        (flight, sampleLocation) = lookupFlightInfo(utcStamp, timezone, resource, PXRF)
        
        metadata = {'portable_data_file':portableDataFile,
                    'elementResultsCsvFile': elementResultsCsvFile,
                    'portable_file_format_name':"csv",
                    'portable_mime_type':"application/csv",
                    'acquisition_time':utcStamp,
                    'acquisition_timezone':timezone.zone,
                    'creation_time':datetime.datetime.now(pytz.utc),
                    'manufacturer_data_file':manufacturerDataFile,
                    'manufacturer_mime_type':"application/octet-stream",
                    'instrument':instrument,
                    'track_position':sampleLocation,
                    'flight':flight,
                    'resource':resource,
                    'creator':user,
                    'name':name,
                    'description':description,
                    'elements':minerals}
    
        dataProduct = PxrfDataProduct(**metadata)
        dataProduct.save()
        if latitude or longitude or altitude:
            editInstrumentDataPosition(dataProduct, latitude, longitude, altitude)
    
        if portableDataFile:
            csvreader = csv.reader(portableDataFile, delimiter=',')
            for row in csvreader:
                if len(row) == 2:
                    label, value = row
                    label = label.replace(' ','')
                    label = label[:1].lower() + label[1:]
                    try:
                        value = int(value)
                        metadata[label] = value
                    except ValueError:
                        try:
                            value = float(value)
                            metadata[label]=value
                        except:
                            # string case
                            if label == 'label':
                                metadata[label]=value
                            if label == 'channel#':
                                break
        
            for row in csvreader:
                if len(row) == 2:
                    sample = PxrfSample(dataProduct=dataProduct, channelNumber=int(row[0]), intensity=int(row[1]))
                    sample.save()
            portableDataFile.close()
        
        return {'status': 'success', 
                'pk': dataProduct.pk,
                'modelName': 'pXRF'}
    except Exception, e:
        return {'status': 'error', 'message': str(e)}

        

def asdDataImporter(instrument, portableDataFile, manufacturerDataFile, utcStamp, 
                    timezone, resource, name, description, minerals, user=None,
                    latitude=None, longitude=None, altitude=None):
    try:
        instrumentData = spc.File(portableDataFile)
        # Take slice b/c data has trailing tab
        dataTable = [r.split("\t")[0:2] for r in instrumentData.data_txt().split("\n") if r != '']
        instrument = ScienceInstrument.getInstrument(ASD)
    
        (flight, sampleLocation) = lookupFlightInfo(utcStamp, timezone, resource, ASD)
        
        dataProduct = AsdDataProduct(
            portable_data_file = portableDataFile,
            portable_file_format_name = "SPC",
            portable_mime_type = "application/octet-stream",
            acquisition_time = utcStamp,
            acquisition_timezone = timezone.zone,
            creation_time = datetime.datetime.now(pytz.utc),
            manufacturer_data_file = manufacturerDataFile,
            manufacturer_mime_type = "application/octet-stream",
            instrument = instrument,
            track_position = sampleLocation,
            flight = flight,
            resource = resource,
            creator=user,
            name = name,
            description = description,
            minerals = minerals
        )
        dataProduct.save()
        if latitude or longitude or altitude:
            editInstrumentDataPosition(dataProduct, latitude, longitude, altitude)
    
        for wl, ab in dataTable[1:]:  # Slice starting @ 1 because 1 line is header
            sample = AsdSample(
                dataProduct = dataProduct,
                wavelength = wl,
                absorbance = ab)
            sample.save()

        return {'status': 'success', 
                'pk': dataProduct.pk,
                'modelName': 'ASD'}
    except Exception, e:
        return {'status': 'error', 'message': str(e)}

def readAsciiFtirData(aspFile):
    pointCount = int(aspFile.readline().rstrip())
    pointCountM1 = pointCount - 1
    maxWaveNum = float(aspFile.readline().rstrip())
    minWaveNum = float(aspFile.readline().rstrip())
    waveDelta = (maxWaveNum-minWaveNum)/pointCountM1
    # Now read and dump the next 3 lines, which we don't understand...
    aspFile.readline()
    aspFile.readline()
    aspFile.readline()
    spectrumData = [((pointCountM1-i)*waveDelta+minWaveNum, 
                     float(aspFile.readline().rstrip()))
                    for i in range(pointCount)]
    return spectrumData

def readSpcFtirData(spcFile):
    instrumentData = spc.File(spcFile)
    # Take slice b/c data has trailing tab
    dataTable = [r.split("\t")[0:2]
                 for r in instrumentData.data_txt().split("\n") if r != '']
    # First line is headers, so we drop it
    dataTable = dataTable[1:]
    return dataTable

def ftirDataImporter(instrument, portableDataFile, manufacturerDataFile,
                     utcStamp, timezone, resource, name, description, minerals,
                     user=None, latitude=None, longitude=None, altitude=None):
    try:
        if (portableDataFile.name.lower().endswith(".spc")):
            dataTable = readSpcFtirData(portableDataFile)
            portableFileFormat = "SPC"
        if (portableDataFile.name.lower().endswith(".asp")):
            dataTable = readAsciiFtirData(portableDataFile)
            portableFileFormat = "ASP"
        instrument = ScienceInstrument.getInstrument(FTIR)
        (flight, sampleLocation) = lookupFlightInfo(utcStamp, timezone, resource, FTIR)
        
        dataProduct = FtirDataProduct(
            portable_data_file = portableDataFile,
            portable_file_format_name = portableFileFormat,
            portable_mime_type = "application/octet-stream",
            acquisition_time = utcStamp,
            acquisition_timezone = timezone.zone,
            creation_time = datetime.datetime.now(pytz.utc),
            manufacturer_data_file = manufacturerDataFile,
            manufacturer_mime_type = "application/octet-stream",
            instrument = instrument,
            track_position = sampleLocation,
            flight = flight,
            resource = resource,
            creator=user,
            name = name,
            description = description,
            minerals = minerals
        )
        dataProduct.save()
        if latitude or longitude or altitude:
            editInstrumentDataPosition(dataProduct, latitude, longitude, altitude)
        
        for wn, rf in dataTable:
            sample = FtirSample(
                dataProduct = dataProduct,
                wavenumber = wn,
                reflectance = rf)
            sample.save()

        return {'status': 'success', 
                'pk': dataProduct.pk,
                'modelName': 'FTIR'}
    except Exception, e:
        return {'status': 'error', 'message': str(e)}

