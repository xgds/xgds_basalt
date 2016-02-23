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
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from geocamTrack import models as geocamTrackModels
from xgds_planner2 import models as plannerModels
from xgds_sample.models import AbstractSample, Region, SampleType
from __builtin__ import classmethod
from geocamUtil.loader import LazyGetModelByName

LOCATION_MODEL = LazyGetModelByName(settings.GEOCAM_TRACK_PAST_POSITION_MODEL)



def getNewDataFileName(instance, filename):
    return settings.XGDS_IMAGE_DATA_SUBDIRECTORY + filename


class BasaltResource(geocamTrackModels.AbstractResource):
    resourceId = models.IntegerField()
    vehicle = models.ForeignKey(plannerModels.Vehicle, blank=True, null=True)

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


class BasaltSample(AbstractSample):
    number = models.IntegerField(null=True)
    triplicate = models.CharField(max_length = 2, null=True) 
    year = models.PositiveSmallIntegerField(null=True)
    
    def buildName(self, inputName):
        name = self.region.shortName + self.year + self.type.value + '-' + self.number + self.triplicates
        return name
    
    def updateSampleFromName(self, name):
        dataDict = {}
        dataDict['region'] = name[:2]
        dataDict['year'] = name[2:4]
        dataDict['type'] = name[4:5]
        dataDict['number'] = name[6:9] 
        dataDict['triplicate'] = name[9:10]
 
        self.region = Region.objects.get(shortName = dataDict['region'])
        self.type = SampleType.objects.get(value = dataDict['type'])
        self.number = ("%03d" % (int(dataDict['number']),))
        self.triplicate = dataDict['triplicate']
        self.year = int(dataDict['year']) 
        self.save()
         
    def updateSampleFromForm(self, form):
        name = form['region'] + \
               form['year'] + \
               form['type'] + "-" + \
               ("%03d" % (sampleNum,)) + \
               form['triplicate']
        
        self.name = Name
        self.region = Region.objects.get(shortName = form['region'])
        self.type = sampleType
        self.number = form['number']
        self.triplicate = form['triplicate'] 
        self.type = SampleType.objects.get(value = form['type'])
        self.year = int(form['year'])
        self.save()
        

class FieldDataProduct(models.Model):
    """ 
    A data product from a field instrument which may be an image or raw data from
    e.g. a spectrometer
    """
    file = models.FileField(upload_to=getNewDataFileName, max_length=255)
    creation_time = models.DateTimeField(blank=True, default=datetime.datetime.utcnow(),
                                         editable=False)
    mimeType = models.CharField(max_length=128, blank=True, null=True)
    instrumentName = models.CharField(max_length=128, blank=True, null=True)

    def __unicode__(self):
        return "%s: %s, %s" % (self.creation_time, self.instrumentName, self.mimeType)
