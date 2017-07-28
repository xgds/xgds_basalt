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
import csv
import traceback
import json
import datetime
import time
import pytz
import httplib
from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django import forms

from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404,  HttpResponse, JsonResponse
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib import messages 
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from forms import EVForm, BasaltInstrumentDataForm, PxrfInstrumentDataForm, SearchBasaltNoteForm
from models import *
import pextantHarness
from geocamUtil.loader import LazyGetModelByName, getFormByName, getModelByName
from xgds_core.models import Constant
from xgds_core.views import addRelay, getConditionActiveJSON
from xgds_core.util import addPort, deletePostKey

from xgds_notes2 import views as xgds_notes2_views
from xgds_planner2.utils import getFlight
from xgds_planner2.views import getActiveFlights, getTodaysGroupFlights, getActiveFlightFlights, getTodaysPlans, getTodaysPlanFiles
from xgds_planner2.models import Vehicle
from xgds_map_server.views import viewMultiLast
from xgds_video.util import getSegmentPath
from geocamUtil.KmlUtil import wrapKmlForDownload, buildNetworkLink, djangoResponse
from xgds_instrument.views import lookupImportFunctionByName, editInstrumentDataPosition

from geocamUtil.TimeUtil import utcToTimeZone, timeZoneToUtc
from geocamUtil.datetimeJsonEncoder import DatetimeJsonEncoder
from basaltApp.hvnp_air_quality import hvnp_kml_generator
from basaltApp.instrumentDataImporters import extractPxrfMfgFileNumber, pxrfProcessElementResultsRow, lookupFlightInfo
from django.forms.models import model_to_dict


def editEV(request, pk=None):
    ''' Create or edit an EV definition.  Shows list of all existing EVs.
    '''
    if request.method == 'POST':
        if pk:
            instance = EV.objects.get(pk=pk)
            form = EVForm(request.POST, instance=instance)
        else:
            form = EVForm(request.POST)
        if form.is_valid():
            form.save()
            form = EVForm()
            return HttpResponseRedirect(reverse('planner2_edit_ev')) 
    else:
        if not pk:
            form = EVForm()
        else:
            instance = EV.objects.get(pk=pk)
            form = EVForm(instance=instance)
    return render(
        request,
        'basaltApp/editEV.html',
        {
            'form': form,
            'evList': EV.objects.all(),
            'pk': pk
        },
    )
    

def addToPlannerContext(context):
    ''' Add a list of EVs for the scheduling part of the plan editor
    '''
    evList = []
    for ev in EV.objects.all():
        evList.append(ev.toSimpleDict())
        
    context['extras'] = json.dumps({"evList":evList})
    return context


def addEVToPlanExecution(request, pe):
    if 'ev' in request.POST.keys():
        evPK = request.POST['ev']
        pe.ev = EV.objects.get(pk=evPK)
    return pe


def callPextantAjax(request, planId, clear=0):
    """ Call Pextant over Ajax and either return the modified plan with success message,
    or return error message.
    """
    PLAN_MODEL = LazyGetModelByName(settings.XGDS_PLANNER2_PLAN_MODEL)
    response = {}
    try:
        plan = PLAN_MODEL.get().objects.get(pk=planId)
        plan = pextantHarness.clearSegmentGeometry(plan)
        response["plan"]= plan.jsonPlan
        if clear:
            response["msg"]= "Sextant route cleared."
            response["status"] = True
            status = 200
        else:
            optimize = str(request.POST['optimize'])

            maxSlope = float(request.POST['slope'])
            post_extent = request.POST['extent']
            if post_extent:
                extent = [float(val) for val in (str(post_extent).split(','))]
            plan = pextantHarness.callPextant(request, plan, optimize, maxSlope, extent)
            response["plan"]= plan.jsonPlan
            response["msg"]= "Sextant has calculated a new route."
            response["status"] = True
            status = 200
    except Exception, e:
        traceback.print_exc()
        response["msg"] = str(e)
        response["status"] = False
        status = 406
    return HttpResponse(json.dumps(response), content_type='application/json',
                        status=status)
        

def storeFieldData(request):
    if request.method == 'POST':
        postData = request.POST
        fileData = request.FILES
        headers = request.META
#        return HttpResponse("Data processed:\n  Instrument: %s\n  Data Type: %s\n" % 
#                            (postData["instrumentName"], headers["CONTENT_TYPE"]),
#                            content_type="text/plain")
        return HttpResponse("Data processed:\n  %s\n" % fileData,
                            content_type="text/plain")
    else:
        return HttpResponse("No data posted\n", content_type="text/plain")


def populateNoteData(request, form):
    data, tags, errors = xgds_notes2_views.populateNoteData(request, form)
    
    if 'flight_id' in data:
        flight = BasaltFlight.objects.get(id=data['flight_id'])
        data.pop('flight_id')
        data['flight'] = flight
        try:
            data.pop('resource')
        except:
            pass
    
    # look up the flight
    elif 'resource' in data:
        resource = None
        resource = data['resource']
        data.pop('resource')
        flight = getFlight(data['event_time'], resource)
        if flight:
            data['flight'] = flight 
    
    return data, tags, errors


def getActivePlan(request, vehicleName, wrist=True):
    foundFlights = BasaltActiveFlight.objects.filter(flight__vehicle__name=vehicleName)
    if foundFlights:
        flight = foundFlights.first().flight
        if flight.plans:
            plan = flight.plans.first().plan
            relUrl = plan.getExportUrl('.kml')
            return redirect(relUrl)
    messages.error(request, "No Planned Traverse found for " + vehicleName + ". Tell team to schedule it.")
    if not wrist:
        return redirect(reverse('error'))
    else:
        return redirect(reverse('wrist'))

        
def wrist(request, fileFormat):
    found = getTodaysPlanFiles(request, fileFormat)
    return render(request,
                  "basaltApp/kmlWrist.html",
                  {'letter_plans': found},
                  )


def wristKmlTrack(request):
    
    found = {}
    activeFlights = getActiveFlights()
    for af in activeFlights:
        if "_EV" in af.flight.name:
            # build the kml for that ev
            found['%s Current' % af.flight.name]=request.build_absolute_uri('/track/tracks.kml?track=%s&line=0' % af.flight.name)
            found['%s Recent' % af.flight.name]=request.build_absolute_uri('/track/recent/tracks.kml?track=%s&recent=900&icon=0' % af.flight.name)
    found['Notes'] = request.build_absolute_uri('/notes/notesFeed.kml')

    kmlContent = ''
    for name, url in found.iteritems():
        url = addPort(url, settings.GEOCAM_TRACK_URL_PORT)
        kmlContent += buildNetworkLink(url, name)
    return wrapKmlForDownload(kmlContent)
    
    
def getActiveEpisode():
    '''
    This gets called from xgds_video to get the active episode
    '''
    activeFlights = BasaltActiveFlight.objects.all()
    for active in activeFlights:
        if active.flight.group:
            if active.flight.group.videoEpisode:
                return active.flight.group.videoEpisode
    return None


def getEpisodeFromName(flightName):
    '''
    This gets called from xgds_video to get the episode from a flight name
    '''
    try: 
        flight = BasaltFlight.objects.get(name=flightName)
        return flight.group.videoEpisode
    except:
        # Maybe we are looking for a group
        group = BasaltGroupFlight.objects.get(name=flightName)
        return group.videoEpisode


# def getIndexFileSuffix(flightName, sourceShortName, segmentNumber):
#     """ get path to video for PLRP """
#     if flightName.endswith(sourceShortName):
#         return '%s/prog_index.m3u8' % getSegmentPath(flightName, None, segmentNumber)
#     else:
#         return '%s/prog_index.m3u8' % getSegmentPath(flightName, sourceShortName, segmentNumber)


def getDelaySeconds(flightName):
    try:
        # see if this flight is active and then look up the current delay
        foundActive = BasaltActiveFlight.objects.all()
        for af in foundActive:
            if af.flight.name.startswith(flightName):
                delayConstant = Constant.objects.get(name="delay")
                return int(delayConstant.value)
    except:
        pass
    return 0


def getLiveIndex(request):
    activeFlights = getActiveFlights()
    if activeFlights:
        firstFlight =activeFlights.first().flight
        if settings.HOSTNAME == 'boat':
            return HttpResponseRedirect(reverse('xgds_video_live'))
        else: 
            return HttpResponseRedirect(reverse('xgds_video_recorded', kwargs={'flightName':firstFlight.group.name})) 
    else:
        return HttpResponseRedirect(reverse('index')) 


def getLiveObjects(request):
    return viewMultiLast(request, ['Photo'])


def getNoteExtras(episodes, source, request):
    result = {'source':source}
    if episodes:
        episode_names = []
        for e in episodes:
            episode_names.append(e.shortName)
        groups = BasaltGroupFlight.objects.filter(name__in=episode_names)
        if groups:
            # this assumes only one group
            flights = BasaltFlight.objects.filter(group=groups[0], vehicle__name=source.name)
            if flights:
                flight = flights[0]
                extras = {}
#                 extras['flight_uuid'] = flight.uuid
#                 extras['flightName'] = flight.name
                extras['flight_id'] = flight.id
                result['extras'] = extras
                
                result['app_label'] = 'basaltApp'
                result['model_type'] = 'BasaltFlight'
                result['object_id'] = flight.id
                result['event_timezone'] = flight.timezone
    return result


def getInstrumentDataImportPage(request, instrumentName):
    form = BasaltInstrumentDataForm()
    instrument = ScienceInstrument.getInstrument(instrumentName)
    form.fields['instrument'].initial = instrument.id
    errors = ""
         
    instrumentDataImportUrl = reverse('save_instrument_data', kwargs={'instrumentName': instrumentName})
    return render(request,
                  'xgds_instrument/importBasaltInstrumentData.html',
                  {'form': form,
                   'errors': errors,
                   'instrumentDataImportUrl': instrumentDataImportUrl,
                   'instrumentType': instrumentName})

def getPxrfDataImportPage(request):
    form = PxrfInstrumentDataForm()
    instrumentName = 'pxrf'
    instrument = ScienceInstrument.getInstrument(instrumentName)
    form.fields['instrument'].initial = instrument.id
    errors = ""
         
    instrumentDataImportUrl = reverse('save_pxrf_data')
    return render(request,
                  'xgds_instrument/importBasaltInstrumentData.html',
                   {'form': form,
                    'errors': errors,
                    'instrumentDataImportUrl': instrumentDataImportUrl,
                    'instrumentType': instrumentName})
    
def stringToDateTime(datetimeStr, timezone):
    date_formats = list(forms.DateTimeField.input_formats) + [
    '%Y/%m/%d %H:%M:%S',
    '%Y-%m-%d %H:%M:%S',
    '%m/%d/%Y %H:%M'
    ]
    datetimeObj = None
    for date_format in date_formats:
        try:
            datetimeObj = datetime.datetime.strptime(datetimeStr, date_format)
        except ValueError:
            pass
        else:
            break
    datetimeObj = timezone.localize(datetimeObj)
    return datetimeObj


def saveNewInstrumentData(request, instrumentName, jsonResult=False):
    errors = None
    if request.method == 'POST':
        form = BasaltInstrumentDataForm(request.POST, request.FILES)
        if form.is_valid():
            if request.user.is_authenticated():
                user = request.user
            else:
                user = None
            instrument = form.cleaned_data["instrument"]
            messages.success(request, 'Instrument data is successfully saved.' )
            importFxn = lookupImportFunctionByName(settings.XGDS_INSTRUMENT_IMPORT_MODULE_PATH, 
                                                   instrument.dataImportFunctionName)
            object_id = None
            if 'object_id' in request.POST:
                object_id = int(request.POST['object_id'])
            result = importFxn(instrument=instrument, 
                               portableDataFile=request.FILES.get("portableDataFile", None),
                               manufacturerDataFile=request.FILES.get("manufacturerDataFile", None),
                               utcStamp=form.cleaned_data["dataCollectionTime"], 
                               timezone=form.getTimezone(), 
                               resource=form.getResource(),
                               name=form.cleaned_data['name'],
                               description=form.cleaned_data['description'],
                               minerals=form.cleaned_data['minerals'],
                               user=user,
                               latitude=form.cleaned_data['lat'],
                               longitude=form.cleaned_data['lon'],
                               altitude=form.cleaned_data['alt'],
                               collector=form.cleaned_data['collector'],
                               object_id=object_id)
            if result['status'] == 'success':
                if 'relay' in request.POST:
                    theModel = getModelByName(settings.XGDS_MAP_SERVER_JS_MAP[result['modelName']]['model'])
                    theInstance = theModel.objects.get(pk=result['pk'])
                    deletePostKey(request.POST, 'relay')
                    addRelay(theInstance, request.FILES, json.dumps(request.POST), request.get_full_path())

                if jsonResult:
                    return HttpResponse(json.dumps(result), content_type='application/json')
                else:
                    return HttpResponseRedirect(reverse('search_map_single_object', kwargs={'modelPK':result['pk'],
                                                                                            'modelName':result['modelName']}))
            else:
                errors = result['message']
        else:
            errors = str(form.errors)
            print 'form errors in receiving instrument data'
        
        if jsonResult:
            return HttpResponse(json.dumps({'status': 'error', 'message': errors}), content_type='application/json', status=httplib.NOT_ACCEPTABLE)
        else:
            messages.error(request, 'Errors %s' % errors)
            return render(request,
                          'xgds_instrument/importBasaltInstrumentData.html',
                          {'form': form,
                           'errors': form.errors,
                           'instrumentDataImportUrl': reverse('save_instrument_data', kwargs={'instrumentName': instrumentName}),
                           'instrumentType': instrumentName},
                          status=httplib.NOT_ACCEPTABLE)      


def savePxrfMfgFile(request):
    seekNumber=None
    mintime = None
    print "*** savePxrfMfgFile POST: %s" % request.POST
    # coming from the LUA on pxrf, look up the pxrfData with the same fileNumber
    try:
        mdf = request.FILES.get('manufacturerDataFile', None)
        if mdf:
            seekNumber = extractPxrfMfgFileNumber(mdf)
            if seekNumber:
                mintime = pytz.utc.localize(datetime.datetime.utcnow()) - datetime.timedelta(hours=12)
                found = PxrfDataProduct.objects.filter(fileNumber=seekNumber, acquisition_time__gte=mintime)
                if found:
                    dataProduct = found.last()
                    dataProduct.manufacturer_data_file = mdf
                    dataProduct.save()
                    
                    # this method is only called by data push from instrument / lua script
                    broadcast = dataProduct.manufacturer_data_file and dataProduct.elementResultsCsvFile
                    if broadcast:
                        pxrfDict = buildPxrfRelayDict(dataProduct)
                        addRelay(dataProduct, request.FILES, json.dumps(pxrfDict, cls=DatetimeJsonEncoder), '/basaltApp/relaySavePxrfData', broadcast=broadcast)

                    return HttpResponse(json.dumps({'status': 'success'}), content_type='application/json')
                else:
                    print "*** PXRF Returning 406 from savePxrfMfgFile: SEQ # not found!  ***"
                    return HttpResponse(json.dumps({'status': 'error', 'message': 'No PXRF record for ' + str(seekNumber), 'seekNumber': seekNumber, 'mintime': str(mintime) }), content_type='application/json', status=406)
    except Exception, e:
        print "*** PXRF Returning 406 from savePxrfMfgFile: exception in lookup!  ***"
        traceback.print_exc()
        return HttpResponse(json.dumps({'status': 'error', 'message': str(e), 'seekNumber': seekNumber, 'mintime': str(mintime) }), content_type='application/json', status=406)
    
    print "*** PXRF Returning 406 from savePxrfMfgFile: something was missing!  ***"
    return HttpResponse(json.dumps({'status': 'error', 'message': 'Something was missing', 'seekNumber': seekNumber, 'mintime': str(mintime)}), content_type='application/json', status=406)


def buildPxrfRelayDict(pxrf):
    result = model_to_dict(pxrf)
    elementset = pxrf.pxrfelement_set.all()
    elementsetList = []
    for e in elementset:
        elementsetList.append(model_to_dict(e, exclude=['dataProduct']))
    result['elementset'] = elementsetList
    
    del result['manufacturer_data_file']
    del result['portable_data_file']
    del result['elementResultsCsvFile']
    del result['track_position']
    del result['user_position']
    
    return result


def relaySavePxrfData(request):
    """ Receive relay data about a pXRF including manufacture data file """
    try:
        print 'receive pxrf relay' 
        pxrfData = request.POST.get('serialized_form')
        pxrfDict = json.loads(pxrfData)
        elementset = pxrfDict['elementset']
        del pxrfDict['elementset']
        newPxrf = PxrfDataProduct(**pxrfDict)
        print 'built new pxrf'
        mdf = request.FILES.get('manufacturerDataFile', None)
        newPxrf.manufacturer_data_file = mdf
        
        print 'looking up position'
        try:
            (flight, foundlocation) = lookupFlightInfo(newPxrf.acquisition_time, timezone, newPxrf.resource, 'pxrf')
            newPxrf.flight = flight
            newPxrf.track_position = foundlocation
        except:
            print 'could not find the location'
            pass
        print 'about to save pxrf'
        newPxrf.save()
        print 'saved pxrf object %d' % newPxrf.pk
        
        for element in elementset:
            pe_dict = json.loads(element)
            pe = PxrfElement(**pe_dict)
            pe.dataProduct = newPxrf
            pe.save()
        print 'built elements'
        return JsonResponse({'status': 'success', 'object_id': newPxrf.pk})
    except Exception, e:
        traceback.print_exc()
        return JsonResponse({'status': 'fail', 'exception': str(e)}, status=406)
     
    
def buildPxrfMetadata(request):
    
    if request.user.is_authenticated():
        user = request.user
    else:
        user = User.objects.get(username='pxrf')
    
    metadata = {'elementResultsCsvFile': request.FILES.get('elementResultsCsvFile', None),
                'portable_file_format_name':"csv",
                'portable_mime_type':"application/csv",
                'acquisition_timezone':request.POST.get('timezone', settings.TIME_ZONE),
                'creation_time':datetime.datetime.now(pytz.utc),
                'manufacturer_data_file':request.FILES.get('manufacturerDataFile', None),
                'manufacturer_mime_type':"application/octet-stream",
                'instrument':ScienceInstrument.getInstrument('pXRF'),
                'creator':user,
                'resource_id':request.POST.get('resource',1),
                'name':request.POST.get('name',None),
                }
    return metadata

def buildPxrfDataProductsFromResultsFile(request):
    # coming from the LUA on pxrf, read through all the results and build dataproduct records
    updatedRecords = []
    status=406
    try:
        elementResultsCsvFile = request.FILES.get('elementResultsCsvFile', None)
        metadata = buildPxrfMetadata(request)
        timezone = pytz.timezone(metadata['acquisition_timezone'])
    except:
        result= {'status': 'error', 
                 'message': 'Did not receive element results csv file' }
        print "*** PXRF buildPxrfDataProductsFromResultsFile: did not receive CSV file! ***"
        print "POST: %s" % request.POST
        return HttpResponse(json.dumps(result), content_type='application/json', status=status)
    
    try:
        if elementResultsCsvFile:
            reader = csv.reader(elementResultsCsvFile, delimiter=',')
            firstrow = next(reader)
            for row in reader:
                #call function in instrument data importers
                foundProduct = pxrfProcessElementResultsRow(firstrow, row, dataProduct=None, timezone=timezone, metadata=metadata)
                if foundProduct:
                    updatedRecords.append(foundProduct.fileNumber)
                    # this method is only called by data push from instrument / lua script
                    # we only broadcast when we get the manufacturer data file
#                     broadcast = foundProduct.manufacturer_data_file and foundProduct.elementResultsCsvFile
#                     deletePostKey(request.POST, 'relay')
#                     addRelay(foundProduct, request.FILES, json.dumps(request.POST), request.get_full_path(), broadcast=broadcast)

            result= {'status': 'success', 
                     'updated': updatedRecords,
                     'modelName': 'pXRF'}
            status=200
    except:
        print "*** PXRF buildPxrfDataProductsFromResultsFile: exception catch! ***"
        print "POST: %s" % request.POST
        traceback.print_exc()
        result= {'status': 'error', 
                 'updated': updatedRecords,
                 'message': 'Problem with csv file' }
#     finally:
#         elementResultsCsvFile.close()

    return HttpResponse(json.dumps(result), content_type='application/json', status=status)


def saveNewPxrfData(request, jsonResult=False):
    errors = None
    if request.method == 'POST':
        form = PxrfInstrumentDataForm(request.POST, request.FILES)
        if form.is_valid():
            if request.user.is_authenticated():
                user = request.user
            else:
                user = User.objects.get(username='pxrf')
            instrument = form.cleaned_data["instrument"]
            messages.success(request, 'Instrument data is successfully saved.' )
            object_id = None
            if 'object_id' in request.POST:
                object_id = int(request.POST['object_id'])
            importFxn = lookupImportFunctionByName(settings.XGDS_INSTRUMENT_IMPORT_MODULE_PATH, 
                                                   instrument.dataImportFunctionName)
            
            result = importFxn(instrument=instrument, 
                               portableDataFile=request.FILES.get("portableDataFile", None),
                               manufacturerDataFile=request.FILES.get("manufacturerDataFile", None),
                               elementResultsCsvFile=request.FILES.get("elementResultsCsvFile", None),
                               utcStamp=form.cleaned_data["dataCollectionTime"], 
                               timezone=form.getTimezone(), 
                               resource=form.getResource(),
                               name=form.cleaned_data['name'],
                               description=form.cleaned_data['description'],
                               minerals=form.cleaned_data['minerals'],
                               user=user,
                               latitude=form.cleaned_data['lat'],
                               longitude=form.cleaned_data['lon'],
                               altitude=form.cleaned_data['alt'],
                               collector=form.cleaned_data['collector'],
                               object_id=object_id)
            if result['status'] == 'success':
                # relay if needed
                if 'relay' in request.POST:
                    theModel = getModelByName(settings.XGDS_MAP_SERVER_JS_MAP[result['modelName']]['model'])
                    theInstance = theModel.objects.get(pk=result['pk'])
                    deletePostKey(request.POST, 'relay')
                    addRelay(theInstance, request.FILES, json.dumps(request.POST), request.get_full_path())
                    
                if jsonResult:
                    return HttpResponse(json.dumps(result), content_type='application/json')
                else:
                    return HttpResponseRedirect(reverse('search_map_single_object', kwargs={'modelPK':result['pk'],
                                                                                            'modelName': result['modelName']}))
            else:
                errors = result['message']
        else:
            errors = str(form.errors)
        
        if jsonResult:
            return HttpResponse(json.dumps({'status': 'error', 'message': errors}), content_type='application/json', status=406)
        else:
            messages.error(request, 'Errors %s' % errors)
            return render(request,
                          'xgds_instrument/importBasaltInstrumentData.html',
                          {'form': form,
                           'errors': form.errors,
                           'instrumentDataImportUrl': reverse('save_pxrf_data'),
                           'instrumentType': 'pxrf'})

def saveUpdatedInstrumentData(request, instrument_name, pk):
    """
    Updates instrument data on save.
    """
    
    if request.method == 'POST':
        mapDict = settings.XGDS_MAP_SERVER_JS_MAP[instrument_name]
        INSTRUMENT_MODEL = LazyGetModelByName(mapDict['model'])
        dataProduct = INSTRUMENT_MODEL.get().objects.get(pk=pk)
        
        # get existing data. 
        if 'edit_form_class' in mapDict:
            form = getFormByName(mapDict['edit_form_class'])(request.POST, request.FILES)
        else:
            form = BasaltInstrumentDataForm(request.POST, request.FILES)
    
        try:
            form.is_valid()
        except:
            pass
        
        for key in form.changed_data:
            value = form.cleaned_data[key]
            if not hasattr(value, 'read'):
                if not isinstance(value, datetime.datetime):
                    setattr(dataProduct, key, value)
            else:
                form.handleFileUpdate(dataProduct, key)
        # save the update info into the model.
#         postDict = request.POST.dict()
#         dataProduct.name = postDict['name'] 
#         dataProduct.description = postDict['description']
#         dataProduct.minerals = postDict['minerals']
#         resourceId = postDict['resource']
#         if resourceId:
#             resource = BasaltResource.objects.get(id=resourceId)
#             dataProduct.resource = resource
        
        dataProduct.acquisition_time = form.cleaned_data['dataCollectionTime']
        
        if (('lat' in form.cleaned_data) and ('lon' in form.cleaned_data)) or ('alt' in form.cleaned_data):
            editInstrumentDataPosition(dataProduct, form.cleaned_data['lat'], form.cleaned_data['lon'], form.cleaned_data['alt'])
        dataProduct.save()
        
        messages.success(request, 'Instrument data successfully saved!')

        return HttpResponseRedirect(reverse('search_map_single_object', kwargs={'modelPK': pk,
                                                                                'modelName': instrument_name}))
        
        
        
def editInstrumentData(request, instrument_name, pk):
    
    """
    Renders instrument data edit page -- if data exists, displays the existing data.
    """
    mapDict = settings.XGDS_MAP_SERVER_JS_MAP[instrument_name]
    INSTRUMENT_MODEL = LazyGetModelByName(mapDict['model'])
    dataProduct = INSTRUMENT_MODEL.get().objects.get(pk=pk)
    jsonDict = dataProduct.toMapDict()
    
    # get existing data. 
    if 'edit_form_class' in mapDict:
        form = getFormByName(mapDict['edit_form_class'])(initial=jsonDict)
    else:
        form = BasaltInstrumentDataForm(initial=jsonDict)
    
    form.editingSetup(dataProduct)
    
    # convert to local time. 
    utcTime = dataProduct.acquisition_time
    timezone = dataProduct.acquisition_timezone
    acquisitionTime = utcToTimeZone(utcTime, timezone)
    acquisitionTime = acquisitionTime.strftime('%m/%d/%Y %H:%M')
     
    form.fields['dataCollectionTime'].initial = acquisitionTime
    form.fields['timezone'].initial = timezone
    
    
    
    # hide the two file fields
#     form.fields['portableDataFile'].widget = forms.HiddenInput()
#     form.fields['manufacturerDataFile'].widget = forms.HiddenInput()
#     
    updateInstrumentDataUrl = reverse('instrument_data_update', kwargs={'instrument_name': instrument_name, 'pk': pk})
    return render(
        request,
        'xgds_instrument/editInstrumentData.html',
        {
            'form': form, 
            'instrument_name': instrument_name,
            'dataProductJson': json.dumps(jsonDict, cls=DatetimeJsonEncoder), 
            'updateInstrumentDataUrl': updateInstrumentDataUrl, 
            'manufacturer_data_file_url': dataProduct.manufacturer_data_file_url,
            'portable_data_file_url': dataProduct.portable_data_file_url
        },
    )

def getPxrfDataJson(request, pk):
    dataProduct = get_object_or_404(PxrfDataProduct, pk=pk)
    sampleList = dataProduct.samples
    elementPercentList = dataProduct.element_percents
    return HttpResponse(json.dumps({'samples':sampleList, 'elements':elementPercentList}), content_type='application/json')

def check_forward(request, *args, **kwargs):
    return HttpResponse(request.META.get('HTTP_X_FORWARDED_FOR', 'None: ' + request.META['REMOTE_ADDR']))

def getCurrentTimeWithDelayCorrection():
    delayRecord = Constant.objects.get(name="delay")
    currentTimeCorrected = time.time() - int(delayRecord.value)

    return currentTimeCorrected

def buildNotesForm(args):
    theForm = SearchBasaltNoteForm()
    
    if args['flight__group_name']:
        group = BasaltGroupFlight.objects.get(name=args['flight__group_name'])
        theForm.fields['flight__group'].initial = group.id
    if args['vehicle__name']:
        vehicle = Vehicle.objects.get(name=args['vehicle__name'])
        theForm.fields['flight__vehicle'].initial = vehicle.id
    
    return theForm

def getTimezoneFromFlightName(flightName):
    try:
        group = BasaltGroupFlight.objects.get(name=flightName)
        return group.flights[0].timezone
    except:
        try:
            flight = BasaltFlight.objects.get(name=flightName)
            return flight.timezone
        except:
            return settings.TIME_ZONE

def getHvnpKml(request):
    document = hvnp_kml_generator.getCurrentStateKml(request.scheme + '://' + request.META['HTTP_HOST'])
    response = djangoResponse(document)
    response['Content-disposition'] = 'attachment; filename=%s' % 'hvnp_so2.kml'
    return response

def getHvnpNetworkLink(request):
    response = wrapKmlForDownload(buildNetworkLink(request.build_absolute_uri(reverse('hvnp_so2')),'HVNP SO2',900), 'hvnp_so2_link.kml')
    return response


def getActiveFlightConditionJSON(request):
    activeFlights = getActiveFlightFlights()
    filterDict = {'condition__flight__in': activeFlights}
    return getConditionActiveJSON(request, filterDict=filterDict)

def noteFilterFunction(episode, sourceShortName):
    group = BasaltGroupFlight.objects.get(name=episode.shortName)
    #filter = {'flight__group_name':episode.shortName} # this does not work.  Register a function to be able to look up a more useful pk
    theFilter = {'flight__group': group.pk}
    if sourceShortName:
        vehicles = Vehicle.objects.filter(name=sourceShortName)
        theFilter['flight__vehicle'] = vehicles.first
    return theFilter
