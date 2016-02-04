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

from geocamTrack import models as geocamTrackModels
from xgds_planner2 import models as plannerModels
from xgds_sample.models import AbstractSample

def getNewDataFileName(instance, filename):
    return settings.XGDS_IMAGE_DATA_SUBDIRECTORY + filename


def getNewDataFileName(instance, filename):
    return settings.XGDS_IMAGE_DATA_SUBDIRECTORY + filename


class BasaltResource(geocamTrackModels.AbstractResource):
    vehicle = models.ForeignKey(plannerModels.Vehicle, blank=True, null=True)

    def __unicode__(self):
        return self.name
    

class CurrentPosition(geocamTrackModels.AltitudeResourcePositionNoUuid):
    pass


class PastPosition(geocamTrackModels.AltitudeResourcePositionNoUuid):
    pass


class EV(models.Model):
    '''
    An EV is a user who can execute a plan.  Information must be provided to Pextant
    about the user to correctly model the path
    ''' 
    mass = models.FloatField()
    user = models.ForeignKey(User, unique=True)
    
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
    number = models.IntegerField()
    triplicate = models.CharField(max_length = 2) # single character
    year = models.PositiveSmallIntegerField()
    
    def buildName(self, inputName):
        name = self.region.shortName + self.year + self.type.value + '-' + self.number + self.triplicates
        return name


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
