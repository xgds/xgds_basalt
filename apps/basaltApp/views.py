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
import pytz
from django.conf import settings
from django.shortcuts import render_to_response, redirect, render
from django import forms

from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404,  HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib import messages 
from django.core.urlresolvers import reverse

from forms import EVForm, BasaltInstrumentDataForm, PxrfInstrumentDataForm
from models import *
import pextantHarness
from geocamUtil.loader import LazyGetModelByName
from xgds_core.models import Constant

from xgds_notes2 import views as xgds_notes2_views
from xgds_planner2.utils import getFlight
from xgds_planner2.views import getActiveFlights, getTodaysGroupFlights
from xgds_map_server.views import viewMultiLast
from xgds_video.util import getSegmentPath
from geocamUtil.KmlUtil import wrapKmlForDownload, buildNetworkLink
from xgds_instrument.views import lookupImportFunctionByName, editInstrumentDataPosition

from geocamUtil.TimeUtil import utcToTimeZone, timeZoneToUtc
from apps.geocamUtil.datetimeJsonEncoder import DatetimeJsonEncoder


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
            resolution = float(request.POST['resolution'])
            maxSlope = float(request.POST['slope'])
            post_extent = request.POST['extent']
            if post_extent:
                extent = [float(val) for val in (str(post_extent).split(','))]
            plan = pextantHarness.callPextant(request, plan, optimize, resolution, maxSlope, extent)
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
    
    
def getTodaysPlans(request):
    letters = []
    plankmls = []
    groupFlights = getTodaysGroupFlights()
    if groupFlights:
        for gf in groupFlights.all():
            letter = gf.name[-1]
            for flight in gf.flights.all():
                if flight.plans:
                    plan = flight.plans.last().plan
                    if letter not in letters:
                        letters.append(letter)
                        plankmls.append(plan.getExportUrl('.kml') )
        
    if not letters:
        messages.error(request, "No Planned Traverses found for today. Tell team to schedule in xGDS.")
        return None
    else:
        return zip(letters, plankmls)


def wrist(request):
    found = getTodaysPlans(request)
    return render_to_response("basaltApp/kmlWrist.html",
                              {'letter_plans': found},
                              context_instance=RequestContext(request))


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


def getIndexFileSuffix(flightName, sourceShortName, segmentNumber):
    """ get path to video for PLRP """
    if flightName.endswith(sourceShortName):
        return '%s/prog_index.m3u8' % getSegmentPath(flightName, None, segmentNumber)
    else:
        return '%s/prog_index.m3u8' % getSegmentPath(flightName, sourceShortName, segmentNumber)


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
        if settings.HOSTNAME == 'basalt':
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
    return render_to_response('xgds_instrument/importBasaltInstrumentData.html',
                              RequestContext(request, {'form': form,
                                                       'errors': errors,
                                                       'instrumentDataImportUrl': instrumentDataImportUrl,
                                                       'instrumentType': instrumentName})
                              )      

def getPxrfDataImportPage(request):
    form = PxrfInstrumentDataForm()
    instrumentName = 'pxrf'
    instrument = ScienceInstrument.getInstrument(instrumentName)
    form.fields['instrument'].initial = instrument.id
    errors = ""
         
    instrumentDataImportUrl = reverse('save_pxrf_data')
    return render_to_response('xgds_instrument/importBasaltInstrumentData.html',
                              RequestContext(request, {'form': form,
                                                       'errors': errors,
                                                       'instrumentDataImportUrl': instrumentDataImportUrl,
                                                       'instrumentType': instrumentName})
                              )      
    
    
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


def saveNewInstrumentData(request, instrumentName):
    if request.method == 'POST':
        form = BasaltInstrumentDataForm(request.POST, request.FILES)
        if form.is_valid():
            instrument = form.cleaned_data["instrument"]
            messages.success(request, 'Instrument data is successfully saved.' )
            importFxn = lookupImportFunctionByName(settings.XGDS_INSTRUMENT_IMPORT_MODULE_PATH, 
                                                   instrument.dataImportFunctionName)
            
            return importFxn(instrument, 
                             request.FILES["portableDataFile"],
                             request.FILES.get("manufacturerDataFile", None),
                             form.cleaned_data["dataCollectionTime"], 
                             form.getTimezone(), 
                             form.getResource(),
                             form.cleaned_data['name'],
                             form.cleaned_data['description'],
                             form.cleaned_data['minerals'],
                             request.user,
                             form.cleaned_data['lat'],
                             form.cleaned_data['lon'],
                             form.cleaned_data['alt'])
        else: 
            messages.error(request, 'Form errors %s' % form.errors)
        return render_to_response('xgds_instrument/importBasaltInstrumentData.html',
                          RequestContext(request, {'form': form,
                                                   'errors': form.errors,
                                                   'instrumentDataImportUrl': reverse('save_instrument_data', kwargs={'instrumentName': instrumentName}),
                                                   'instrumentType': instrumentName})
                          )      


def saveNewPxrfData(request):
    if request.method == 'POST':
        form = PxrfInstrumentDataForm(request.POST, request.FILES)
        if form.is_valid():
            instrument = form.cleaned_data["instrument"]
            messages.success(request, 'Instrument data is successfully saved.' )
            importFxn = lookupImportFunctionByName(settings.XGDS_INSTRUMENT_IMPORT_MODULE_PATH, 
                                                   instrument.dataImportFunctionName)
            
            return importFxn(instrument, 
                             request.FILES["portableDataFile"],
                             request.FILES.get("manufacturerDataFile", None),
                             request.FILES.get("elementResultsCsvFile", None),
                             form.cleaned_data["dataCollectionTime"], 
                             form.getTimezone(), 
                             form.getResource(),
                             form.cleaned_data['name'],
                             form.cleaned_data['description'],
                             form.cleaned_data['minerals'],
                             request.user,
                             form.cleaned_data['lat'],
                             form.cleaned_data['lon'],
                             form.cleaned_data['alt'])
        else: 
            messages.error(request, 'Form errors %s' % form.errors)
        return render_to_response('xgds_instrument/importBasaltInstrumentData.html',
                          RequestContext(request, {'form': form,
                                                   'errors': form.errors,
                                                   'instrumentDataImportUrl': reverse('save_pxrf_data'),
                                                   'instrumentType': 'pxrf'})
                          )      

def saveUpdatedInstrumentData(request, instrument_name, pk):
    """
    Updates instrument data on save.
    """
    InstrumentDataProductModel = BasaltInstrumentDataProduct.getDataForm(instrument_name)
    dataProduct = InstrumentDataProductModel.objects.get(pk = pk)
    if request.method == 'POST':
        # save the update info into the model.
        postDict = request.POST.dict()
        dataProduct.name = postDict['name'] 
        dataProduct.description = postDict['description']
        dataProduct.minerals = postDict['minerals']
        resourceId = postDict['resource']
        if resourceId:
            resource = BasaltResource.objects.get(id=resourceId)
            dataProduct.resource = resource
        
        # get timezone
        dataProduct.acquisition_timezone = postDict['timezone']
        tz = pytz.timezone(postDict['timezone'])
        
        # convert to timezone-aware datetime
        timezoneTimeStr = postDict['dataCollectionTime']
        timezoneTime = stringToDateTime(timezoneTimeStr, tz)        
        
        # convert to utc time
        utcTime = timeZoneToUtc(timezoneTime)
        dataProduct.acquisition_time = utcTime
        
        if (('lat' in postDict) and ('lon' in postDict)) or ('alt' in postDict):
            editInstrumentDataPosition(dataProduct, postDict['lat'], postDict['lon'], postDict['alt'])
        dataProduct.save()
        
        messages.success(request, 'Instrument data successfully saved!')

        return HttpResponseRedirect(reverse('search_map_single_object', kwargs={'modelPK': pk,
                                                                                'modelName': instrument_name}))
        
        
        
def editInstrumentData(request, instrument_name, pk):
    """
    Renders instrument data edit page -- if data exists, displays the existing data.
    """
    InstrumentDataProductModel = BasaltInstrumentDataProduct.getDataForm(instrument_name)
    dataProduct = InstrumentDataProductModel.objects.get(pk = pk)
    jsonDict = dataProduct.toMapDict()
    
    # get existing data. 
    form = BasaltInstrumentDataForm(initial=jsonDict)
    
    # convert to local time. 
    utcTime = dataProduct.acquisition_time
    timezone = dataProduct.acquisition_timezone
    acquisitionTime = utcToTimeZone(utcTime, timezone)
    acquisitionTime = acquisitionTime.strftime('%m/%d/%Y %H:%M')
    
    form.fields['dataCollectionTime'].initial = acquisitionTime
    form.fields['timezone'].initial = timezone
    
    # hide the two file fields
    form.fields['portableDataFile'].widget = forms.HiddenInput()
    form.fields['manufacturerDataFile'].widget = forms.HiddenInput()
    
    updateInstrumentDataUrl = reverse('instrument_data_update', kwargs={'instrument_name': instrument_name, 'pk': pk})
    return render(
        request,
        'xgds_instrument/editInstrumentData.html',
        {
            'form': form, 
            'instrument_name': instrument_name,
            'dataProductJson': json.dumps(jsonDict, cls=DatetimeJsonEncoder), 
            'updateInstrumentDataUrl': updateInstrumentDataUrl, 
            'manufacturer_data_file_url': jsonDict['manufacturer_data_file_url'],
            'portable_data_file_url': jsonDict['portable_data_file_url']
        },
    )

def check_forward(request, *args, **kwargs):
    return HttpResponse(request.META.get('HTTP_X_FORWARDED_FOR', 'None: ' + request.META['REMOTE_ADDR']))
