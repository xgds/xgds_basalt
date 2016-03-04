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

import pytz
import os
import datetime
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from geocamTrack import models as geocamTrackModels
from geocamUtil.models.AbstractEnum import AbstractEnumModel
from xgds_planner2 import models as plannerModels
from xgds_sample.models import AbstractSample, Region, SampleType
from __builtin__ import classmethod
from geocamUtil.loader import LazyGetModelByName
from xgds_core.models import Constant
from xgds_notes2.models import AbstractNote, AbstractUserSession, Location

from geocamPycroraptor2.views import getPyraptordClient, stopPyraptordServiceIfRunning
from logilab.common.registry import ObjectNotFound

LOCATION_MODEL = LazyGetModelByName(settings.GEOCAM_TRACK_PAST_POSITION_MODEL)


def getNewDataFileName(instance, filename):
    return settings.XGDS_IMAGE_DATA_SUBDIRECTORY + filename


class BasaltResource(geocamTrackModels.AbstractResource):
    resourceId = models.IntegerField()
    vehicle = models.ForeignKey(plannerModels.Vehicle, blank=True, null=True)
    port = models.IntegerField()

    def __unicode__(self):
        return self.name
    

class DataType(models.Model):
    name = models.CharField(max_length=32)
    notes = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class CurrentPosition(geocamTrackModels.AltitudeResourcePositionNoUuid):
    serverTimestamp = models.DateTimeField(db_index=True)
    pass


class PastPosition(geocamTrackModels.AltitudeResourcePositionNoUuid):
    serverTimestamp = models.DateTimeField(db_index=True)
    pass


class BasaltTrack(geocamTrackModels.AbstractTrack):
    dataType = models.ForeignKey(DataType, null=True, blank=True)
    timezone = models.CharField(max_length=128)

    def getTimezone(self):
        return pytz.timezone(self.timezone)
    
    def toMapDict(self):
        result = geocamTrackModels.AbstractTrack.toMapDict(self)
        result['type'] = 'BasaltTrack'
        return result
    
    def __unicode__(self):
        return '%s %s' % (self.__class__.__name__, self.name)


class EV(models.Model):
    '''
    An EV is a user who can execute a plan.  Information must be provided to Pextant
    about the user to correctly model the path
    ''' 
    mass = models.FloatField()
    user = models.OneToOneField(User)
    
    def toSimpleDict(self):
        result = {}
        result['mass'] = self.mass
        result['name'] = self.user.first_name + ' ' + self.user.last_name
        result['pk'] = self.pk
        return result
    
    def __unicode__(self):
        return self.user.first_name + ' ' + self.user.last_name


class BasaltFlight(plannerModels.AbstractFlight):
    ''' A Basalt Flight for storing delay and handling start and stop functions '''
    delaySeconds = models.IntegerField(default=0)
    track = models.OneToOneField(BasaltTrack, null=True, blank=True)
    
    def startFlightExtras(self, request):
        delayConstant = Constant.objects.get(name="delay")
        self.delaySeconds = int(delayConstant.value)
        resource=BasaltResource.objects.get(vehicle=self.vehicle)
        #Create the track if it does not exist
        if not self.track:
            try:
                track = BasaltTrack.objects.get(name=self.name)
            except ObjectDoesNotExist:
                timezone = settings.TIME_ZONE
                if self.plans:
                    timezone=str(self.plans[0].plan.jsonPlan.site.alternateCrs.properties.timezone)
                track = BasaltTrack(name=self.name,
                                    resource=resource,
                                    timezone=timezone,
                                    lineStyle=geocamTrackModels.LineStyle.objects.get(uuid=resource.name),
#                                     lineStyle=DEFAULT_LINE_STYLE,
                                    dataType=DataType.objects.get(name="RawGPSLocation"))
                track.save()
                self.track = track
                self.save()
        
        #start the eva track listener
        if settings.PYRAPTORD_SERVICE is True:
            pyraptord = getPyraptordClient()
            serviceName = self.vehicle.name + "TrackListener"
            print serviceName
            scriptPath = os.path.join(settings.PROJ_ROOT, 'apps', 'basaltApp', 'scripts', 'evaTrackListener.py')
            command = "%s -o 127.0.0.1 -p %d -n %s -t %s" % (scriptPath, resource.port, self.vehicle.name[-1:], self.name)
            print command
            stopPyraptordServiceIfRunning(pyraptord, serviceName)
            pyraptord.updateServiceConfig(serviceName,
                                          {'command': command})
            pyraptord.startService(serviceName)
        pass

    def stopFlightExtras(self, request):
        #stop the eva track listener
        if settings.PYRAPTORD_SERVICE is True:
            pyraptord = getPyraptordClient()
            serviceName = self.vehicle.name + "TrackListener"
            stopPyraptordServiceIfRunning(pyraptord, serviceName)
        #TODO remove the current position for that track
        pass
    
class BasaltPlanExecution(plannerModels.PlanExecution):
    ''' 
    A Plan Execution that also includes an EV
    '''
    ev = models.ForeignKey(EV)
    
    def toSimpleDict(self):
        result = super(BasaltPlanExecution, self).toSimpleDict()
        if self.ev:
            result['ev'] = self.ev.pk
        else:
            result['ev'] = None
        return result


class Triplicate(AbstractEnumModel):
    pass


class BasaltSample(AbstractSample):
    number = models.IntegerField(null=True)
    triplicate = models.ForeignKey(Triplicate, null=True)
    year = models.PositiveSmallIntegerField(null=True)
    
    def buildName(self):
        number = ("%03d" % (int(self.number),))
        name = self.region.shortName + str(self.year) + self.type.value + '-' + str(number) + str(self.triplicate.value)
        return name
    
    def updateSampleFromName(self, name):
        assert name
        
        dataDict = {}
        dataDict['region'] = name[:2]
        dataDict['year'] = name[2:4]
        dataDict['type'] = name[4:5]
        dataDict['number'] = name[6:9] 
        dataDict['triplicate'] = name[9:10]
         
        if not self.region:
            self.region = Region.objects.get(shortName = dataDict['region'])
        if not self.type:
            self.type = SampleType.objects.get(value = dataDict['type'])
        if not self.number:
            self.number = ("%03d" % (int(dataDict['number']),))
        if not self.triplicate:
            self.triplicate = Triplicate.objects.get(value=dataDict['triplicate'])
        if not self.year:
            self.year = int(dataDict['year']) 
        self.save()
        

class FieldDataProduct(models.Model):
    """ 
    A data product from a field instrument which may be an image or raw data from
    e.g. a spectrometer
    """
    file = models.FileField(upload_to=getNewDataFileName, max_length=255)
    creation_time = models.DateTimeField(blank=True, default=timezone.now, editable=False)
    mimeType = models.CharField(max_length=128, blank=True, null=True)
    instrumentName = models.CharField(max_length=128, blank=True, null=True)

    def __unicode__(self):
        return "%s: %s, %s" % (self.creation_time, self.instrumentName, self.mimeType)
    

class BasaltUserSession(AbstractUserSession):
    location = models.ForeignKey(Location)
    resource = models.ForeignKey(plannerModels.Vehicle)
    
    @classmethod
    def getFormFields(cls):
        return ['role',
                'location',
                'resource']
    

class BasaltNote(AbstractNote):
    flight = models.ForeignKey(settings.XGDS_PLANNER2_FLIGHT_MODEL, null=True, blank=True)
    
    def calculateDelayedEventTime(self, event_time):
        if self.flight:
            return event_time - datetime.timedelta(seconds=self.flight.delaySeconds)
            
        return self.event_time

