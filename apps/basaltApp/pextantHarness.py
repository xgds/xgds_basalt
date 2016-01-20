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
# import pydevd
import logging
import json
import os
from django.conf import settings
from django.shortcuts import render_to_response, redirect, render
from django.core.urlresolvers import reverse

from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404,  HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _

from pextant.api import Pathfinder
from pextant.ExplorerModel import *
from pextant.ExplorationObjective import *
from pextant.EnvironmentalModel import loadElevationMap
from apps.pextant.EnvironmentalModel import EnvironmentalModel

def getMap(site):
    site_frame = site['name']
    dem_name = site_frame.replace(' ', '_')+'.tif'
    fullPath = os.path.join(settings.STATIC_ROOT, 'basaltApp', 'dem', dem_name)
    if os.path.isfile(fullPath): 
        zone=site['alternateCrs']['properties']['zone']
        zoneLetter=site['alternateCrs']['properties']['zoneLetter']
        #TODO limit based on bounds of plan
        dem = loadElevationMap(fullPath, zone=zone, zoneLetter=zoneLetter, desiredRes=0.3)
        return dem
    return None

def testJsonSegments(plan):
    prevStation = None
    
    for index, entry in enumerate(plan.jsonPlan.sequence):
        if entry['type'] == 'Station':
            prevStation = entry['geometry']['coordinates']
        elif entry['type'] == 'Segment':
            nextStation = plan.jsonPlan.sequence[index+1]['geometry']['coordinates']
            allCoords = [prevStation, nextStation]
            entry['geometry'] = {"coordinates": allCoords,
                                 "type": "LineString"}
            prevStation = nextStation
    return plan
    
def callPextant(request, plan):
    print 'Called Pextant post save Python'
    executions = plan.executions
    if not executions:
        logging.warning('Plan %s not scheduled could not call Pextant', plan.name)
        return plan
    
    if not executions[0].ev:
        logging.warning('No EV associated with plan %s could not call Pextant', plan.name)
        return plan

    explorer = BASALTExplorer(executions[0].ev.mass)
    
#     start_time = executions[0].planned_start_time
    site = plan.jsonPlan['site']

# CANNOT build map due to bugs in pextant
    dem = getMap(site)
    if not dem:
        logging.warning('Could not load DEM while calling Pextant for ' + site['name'])
#      
    pathFinder = Pathfinder(explorer, dem)
#     pydevd.settrace('192.168.1.64')
    sequence = plan.jsonPlan.sequence
    jsonSequence = json.dumps(sequence)
    print jsonSequence
    try:
        result = pathFinder.completeSearchFromJSON(str(plan.jsonPlan.optimization), jsonSequence)
        print result
    except:
        pass
    
    #TODO append new sequence into old json

#     plan = testJsonSegments(plan)
    print 'old plan'
    print plan.jsonPlan
#     plan.save()
    return plan

    
