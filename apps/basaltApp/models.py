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

from django.db import models
from django.contrib.auth.models import User

from geocamTrack import models as geocamTrackModels
from xgds_planner2 import models as plannerModels

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
    
    def __unicode__(self):
        return self.user.first_name + ' ' + self.user.last_name
    
class BasaltPlanExecution(plannerModels.AbstractPlanExecution):
    ev = models.ForeignKey(EV)
