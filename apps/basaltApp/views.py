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

from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404,  HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _

from forms import EVForm
from models import EV, BasaltActiveFlight
import pextantHarness
from geocamUtil.loader import LazyGetModelByName
from xgds_notes2 import views as xgds_notes2_views
from xgds_planner2.utils import getFlight


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


def getActiveEpisode(flightName):
    '''
    This gets called from xgds_video to get the active episodes
    '''
    
    activeFlights = BasaltActiveFlight.objects.all()
    for active in activeFlights:
        if active.flight.group:
            if active.flight.group.videoEpisode:
                return active.flight.group.videoEpisode
    return None
