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
from django.conf import settings
from django.shortcuts import render_to_response, redirect, render
from django.core.urlresolvers import reverse

from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404,  HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _

from forms import EVForm
from models import EV
import pextantHarness
from geocamUtil.loader import LazyGetModelByName
from xgds_notes2 import views as xgds_notes2_views
from xgds_planner2.utils import getFlight

import datetime
from subprocess import Popen, PIPE
from time import sleep as time_sleep
import re


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


def callPextantAjax(request, planId):
    """ Call Pextant over Ajax and either return the modified plan with success message,
    or return error message.
    """
    PLAN_MODEL = LazyGetModelByName(settings.XGDS_PLANNER2_PLAN_MODEL)
    response = {}
    try:
        plan = PLAN_MODEL.get().objects.get(pk=planId)
        plan = pextantHarness.clearSegmentGeometry(plan)
        response["plan"]= plan.jsonPlan
        optimize = str(request.POST['optimize'])
        resolution = float(request.POST['resolution'])
        maxSlope = float(request.POST['slope'])
        plan = pextantHarness.callPextant(request, plan, optimize, resolution, maxSlope)
        response["plan"]= plan.jsonPlan
        response["msg"]= "Sextant has calculated a new route."
        response["status"] = True
        status = 200
    except Exception, e:
        response["msg"] = e.args[0]
        response["status"] = False
        status = 406
    return HttpResponse(json.dumps(response), content_type='application/json',
                        status=status)
    
    
def showSubsystemStatus(request):
    # Status timestamp in UTC:
    statusTimestamp = datetime.datetime.utcnow()
    
    # load averages
    def statusColor(val,yellowThresh,redThresh):
        if val > redThresh:
            return '#ff0000'
        if val > yellowThresh:
            return '#ffff00'
        return '#00ff00'
    
    loadStatus = {}
    proc = Popen('uptime',stdout=PIPE)
    (status,retval) = proc.communicate()
    pattern = '(?P<time>\S+)\sup\s?(?P<updays>\d+)?(\sday)?(.+)?\s(?P<uphms>\S+),\s+(?P<users>\d+)\suser.*,\s+load average: (?P<load1m>[\.\d]+), (?P<load5m>[\.\d]+), (?P<load15m>[\.\d]+)'
    match = re.search(pattern,status)
    if match:
        loadStatus = match.groupdict()
        if not match.group('updays'):
            loadStatus['updays'] = 0
        loadStatus['load1m'] = float(loadStatus['load1m'])
        loadStatus['load5m'] = float(loadStatus['load5m'])
        loadStatus['load15m'] = float(loadStatus['load15m'])
        loadStatus['load1mColor'] = statusColor(loadStatus['load1m'],1,3)
        loadStatus['load5mColor'] = statusColor(loadStatus['load5m'],1,3)
        loadStatus['load15mColor'] = statusColor(loadStatus['load15m'],1,3)
    
#     # subsystem status
#     status = {}
#     status['domain'] = 'GPS'
#     status['state'] = 'Running'
#     status['timestamp'] = datetime.datetime.now()
#     statuses = [status]
    return render_to_response("basaltApp/subsystemStatus.html",
                              {'load_status': loadStatus,
#                                'statuses': statuses, 
                               'status_timestamp': statusTimestamp,
                               'BASALT_APP_SUBSYSTEM_STATUS_URL': reverse('basaltApp_subsystemStatusJson')},
                              context_instance=RequestContext(request))


def subsystemStatusJson(request):
    status = {}
    status['domain'] = 'TEST DOMAIN'
    status['state'] = 'TEST STATUS'
    status['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    statuses = [status]
    return HttpResponse(json.dumps(statuses, indent=4, sort_keys=True),
                        content_type='application/json')
    


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
    
    # look up the flight
    resource = None
    if 'resource' in data:
        resource = data['resource']
        data.pop('resource')
    data['flight'] = getFlight(data['event_time'], resource)

    return data, tags, errors