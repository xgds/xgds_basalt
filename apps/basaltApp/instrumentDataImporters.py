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
import traceback
import json
import datetime
import csv
from collections import deque
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from cStringIO import StringIO
import pytz

import spc  # library for reading SPC format spectra
from django.conf import settings
from geocamUtil.TimeUtil import timeZoneToUtc
from geocamTrack.utils import getClosestPosition
from xgds_core.flightUtils import getFlight
from basaltApp.models import FtirDataProduct, AsdDataProduct, Element, PxrfDataProduct, PxrfSample, PxrfElement, FtirSample, ScienceInstrument, BasaltTrack, AsdSample
from xgds_instrument.views import editInstrumentDataPosition

FTIR = "ftir"
ASD = "asd"
PXRF = "pxrf"


def lookupFlightInfo(utcStamp, timezone, vehicle, defaultTrackName):
    #
    # Get flight and track info and find location of sample if available
    #
    flight = None
    try:
        flight = getFlight(utcStamp, vehicle.vehicle)
        if flight:
            trackName = flight.name
        elif vehicle:
            trackName = vehicle.name
        else:
            trackName = defaultTrackName
        track = BasaltTrack.getTrackByName(trackName)
        if not track:
            if trackName == defaultTrackName:
                track = BasaltTrack(name=defaultTrackName)
            else:
                track = BasaltTrack(name=defaultTrackName,
                                    vehicle=vehicle,
                                    timezone=timezone)
        sampleLocation = getClosestPosition(track=track,
                                            timestamp=utcStamp,
                                            vehicle=vehicle)
    except:
        sampleLocation = None
    return (flight, sampleLocation)


def pxrfDataImporter(instrument, portableDataFile, manufacturerDataFile, elementResultsCsvFile,
                     utcStamp, timezone, vehicle, name, description, minerals=None, user=None,
                     latitude=None, longitude=None, altitude=None, collector=None, object_id=None):
    try:
        instrument = ScienceInstrument.getInstrument(PXRF)
        (flight, sampleLocation) = lookupFlightInfo(utcStamp, timezone, vehicle, PXRF)
        
        if not user:
            user = User.objects.get(username='pxrf')
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
                    'vehicle':vehicle,
                    'creator':user,
                    'collector': collector,
                    'name':name,
                    'description':description,
                    'elements':minerals,
                    'pk':object_id}
    
        dataProduct = PxrfDataProduct(**metadata)
        
        if manufacturerDataFile:
            dataProduct.fileNumber = extractPxrfMfgFileNumber(manufacturerDataFile)
        
        if latitude or longitude or altitude:
            editInstrumentDataPosition(dataProduct, latitude, longitude, altitude)
    
        dataProduct.save()
        
        pxrfLoadPortableSampleData(portableDataFile, dataProduct)
        pxrfParseElementResults(elementResultsCsvFile, dataProduct, timezone)
        
        return {'status': 'success', 
                'pk': dataProduct.pk,
                'modelName': 'pXRF'}
    except Exception, e:
        traceback.print_exc()
        return {'status': 'error', 'message': str(e)}

        

def pxrfLoadPortableSampleData(portableDataFile, dataProduct):
    """ Read the portable sample data, create records and set attributes
        Clears out and overrides any old data.
    """
    if portableDataFile:
        metadata = {}
        
        # clear out any old data
        samples = PxrfSample.objects.filter(dataProduct=dataProduct)
        samples.all().delete()
    
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
#         portableDataFile.close()
        
        for key, value in metadata.iteritems():
            setattr(portableDataFile, key, value)
        dataProduct.save()


def getLastRow(reader):
        try:
            lastrow = deque(reader, 1)[0]
        except IndexError:  # empty file
            lastrow = None
        
        return lastrow
    
def getRowByFileNumber(reader, fileNumber):
    for row in reader:
        try:
            if int(row[0]) == fileNumber:
                return row
        except:
            pass
        
    return getLastRow(reader)


def extractPxrfMfgFileNumber(mdf):
    #'ANALYZE_EMP-47.pdz'
    try:
        if mdf:
            splits = mdf.name.split('-')
            if len(splits) > 1:
                ending = splits[1].split('.')
                try:
                    seekNumber = int(ending[0])
                except:
                    # might have django file duplication stuff, eg
                    # ANALYZE_EMP-2_gsN7BQx.pdz
                    substring = ending[0].split('_')
                    seekNumber = int(substring[0])
                return seekNumber
    except:
        traceback.print_exc()
        pass
    return None
    

def pxrfProcessElementResultsRow(firstrow, lastrow, dataProduct=None, timezone=settings.TIME_ZONE, metadata=None, clearFound=False):
    if firstrow and lastrow:
        dictionary = dict(zip([f.strip() for f in firstrow], lastrow))
        fileNumber = int(dictionary['File #'])
        readDateTime = datetime.datetime.strptime(dictionary['DateTime'], '%m-%d-%Y %H:%M')
        localRowTime = timezone.localize(readDateTime)
        newDataProduct = False
        try:
            if not dataProduct:
                # look it up
                mintime = localRowTime - datetime.timedelta(hours=12)
                foundProducts = PxrfDataProduct.objects.filter(fileNumber=fileNumber, acquisition_time__gte=mintime)
                if foundProducts:
                    if clearFound:
                        dataProduct = foundProducts.last()
                    else:
                        return None
                else:
                    metadata['fileNumber'] = fileNumber
                    dataProduct = PxrfDataProduct(**metadata)
                    dataProduct.save()
                    newDataProduct = True

            if dataProduct:
                if dataProduct.pxrfelement_set.exists():
                    dataProduct.pxrfelement_set.all().delete()
                    dataProduct.elementPercentsTotal = 0
                if not dataProduct.acquisition_time:
                    dataProduct.acquisition_time = localRowTime
        
                dataProduct.fileNumber = fileNumber
                dataProduct.mode = dictionary['Mode']
                dataProduct.pxrfType = dictionary['Type']
                dataProduct.elapsedTime = dictionary['ElapsedTime']
                dataProduct.alloy1 = dictionary['Alloy 1']
                dataProduct.matchQuality1 = dictionary['Match Qual 1']
                dataProduct.alloy2 = dictionary['Alloy 2']
                dataProduct.matchQuality2 = dictionary['Match Qual 2']
                dataProduct.alloy3 = dictionary['Alloy 3']
                dataProduct.matchQuality3 = dictionary['Match Qual 3']
        except:
            traceback.print_exc()
            pass
        
        percentTotal = 0
        for key in firstrow[15:]:
            elementPercent = dictionary[key]
            if elementPercent:
                errorKey = key + ' Err'
                try:
                    if 'Err' not in key:
                        percentTotal += float(elementPercent)
                except:
                    pass
                if errorKey in dictionary:
                    elementError = dictionary[errorKey]
                    try:
                        pe = PxrfElement(dataProduct=dataProduct, 
                                         element=Element.objects.get(symbol=key), 
                                         percent=elementPercent, 
                                         error=elementError)
                        pe.save()
                    except Exception, e:
                        traceback.print_exc()
                        pass
        dataProduct.elementPercentsTotal = percentTotal
        if newDataProduct:
            (flight, sampleLocation) = lookupFlightInfo(dataProduct.acquisition_time, timezone, dataProduct.vehicle, PXRF)
            dataProduct.flight = flight
            dataProduct.track_position = sampleLocation
        dataProduct.save()
        return dataProduct

def pxrfParseElementResults(elementResultsCsvFile, dataProduct, timezone):
    """ Read the element results.  For now, just read the latest time.
    """
    if elementResultsCsvFile:
        try:
            reader = csv.reader(elementResultsCsvFile, delimiter=',')
            firstrow = next(reader)
            if dataProduct.fileNumber >= 0:
                lastrow = getRowByFileNumber(reader, dataProduct.fileNumber)
            else:
                lastrow = getLastRow(reader)
#             elementResultsCsvFile.close()
            
            pxrfProcessElementResultsRow(firstrow, lastrow, dataProduct, timezone)
                
        except:
            pass
#         elementResultsCsvFile.close()
        
            
def asdDataImporter(instrument, portableDataFile, manufacturerDataFile, utcStamp, 
                    timezone, vehicle, name, description, minerals, user=None,
                    latitude=None, longitude=None, altitude=None, collector=None, object_id=None):
    try:
        instrument = ScienceInstrument.getInstrument(ASD)
    
        (flight, sampleLocation) = lookupFlightInfo(utcStamp, timezone, vehicle, ASD)
        
        if not user:
            user = User.objects.get(username='asd')

        dataProduct = AsdDataProduct(
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
            vehicle = vehicle,
            creator=user,
            collector=collector,
            name = name,
            description = description,
            minerals = minerals,
            pk=object_id
        )
        
        if latitude or longitude or altitude:
            editInstrumentDataPosition(dataProduct, latitude, longitude, altitude)
        
        dataProduct.save()
        if portableDataFile:
            asdLoadPortableSampleData(portableDataFile, dataProduct)
            dataProduct.portable_data_file = portableDataFile
            dataProduct.save()

        return {'status': 'success', 
                'pk': dataProduct.pk,
                'modelName': 'ASD'}
    except Exception, e:
        traceback.print_exc()
        return {'status': 'error', 'message': str(e)}


def asdLoadPortableSampleData(portableDataFile, dataProduct):
    # clear out any old data
    samples = AsdSample.objects.filter(dataProduct=dataProduct)
    samples.all().delete()
        
    if portableDataFile:
        instrumentData = spc.File(portableDataFile)
        # Take slice b/c data has trailing tab
        dataTable = [r.split("\t")[0:2] for r in instrumentData.data_txt().split("\n") if r != '']
        
        for wl, ab in dataTable[1:]:  # Slice starting @ 1 because 1 line is header
            sample = AsdSample(
                dataProduct = dataProduct,
                wavelength = wl,
                absorbance = ab)
            sample.save()
    
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

def loadPortableFtirData(portableDataFile, dataProduct):
    if portableDataFile:
        if (portableDataFile.name.lower().endswith(".spc")):
            dataTable = readSpcFtirData(portableDataFile)
            portableFileFormat = "SPC"
        if (portableDataFile.name.lower().endswith(".asp")):
            dataTable = readAsciiFtirData(portableDataFile)
            portableFileFormat = "ASP"
        for wn, rf in dataTable:
            sample = FtirSample(
                dataProduct = dataProduct,
                wavenumber = wn,
                reflectance = rf)
            sample.save()
        dataProduct.portable_file_format_name = portableFileFormat
        dataProduct.save()

def ftirDataImporter(instrument, portableDataFile, manufacturerDataFile,
                     utcStamp, timezone, vehicle, name, description, minerals,
                     user=None, latitude=None, longitude=None, altitude=None,
                     collector=None, object_id=None):
    try:
        instrument = ScienceInstrument.getInstrument(FTIR)
        (flight, sampleLocation) = lookupFlightInfo(utcStamp, timezone, vehicle, FTIR)
        
        if not user:
            user = User.objects.get(username='ftir')

        dataProduct = FtirDataProduct(
            portable_mime_type = "application/octet-stream",
            acquisition_time = utcStamp,
            acquisition_timezone = timezone.zone,
            creation_time = datetime.datetime.now(pytz.utc),
            manufacturer_data_file = manufacturerDataFile,
            manufacturer_mime_type = "application/octet-stream",
            instrument = instrument,
            track_position = sampleLocation,
            flight = flight,
            vehicle = vehicle,
            creator=user,
            collector=collector,
            name = name,
            description = description,
            minerals = minerals,
            pk=object_id
        )
        dataProduct.save()
        if latitude or longitude or altitude:
            editInstrumentDataPosition(dataProduct, latitude, longitude, altitude)
        
        if portableDataFile:
            loadPortableFtirData(portableDataFile, dataProduct)
            dataProduct.portable_data_file = portableDataFile
            dataProduct.save()

        return {'status': 'success', 
                'pk': dataProduct.pk,
                'modelName': 'FTIR'}
    except Exception, e:
        traceback.print_exc()
        return {'status': 'error', 'message': str(e)}

