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
from django.core.urlresolvers import reverse

from taggit.managers import TaggableManager

from geocamTrack import models as geocamTrackModels
from geocamTrack.utils import getClosestPosition

from geocamUtil.models.AbstractEnum import AbstractEnumModel
from xgds_planner2 import models as plannerModels
from xgds_sample import models as xgds_sample_models
from __builtin__ import classmethod
from geocamUtil.loader import LazyGetModelByName
from xgds_core.models import Constant
from xgds_notes2.models import AbstractLocatedNote, AbstractUserSession, AbstractTaggedNote, Location
from xgds_image import models as xgds_image_models
from xgds_planner2.utils import getFlight
from xgds_instrument.models import ScienceInstrument, AbstractInstrumentDataProduct

from geocamPycroraptor2.views import getPyraptordClient, stopPyraptordServiceIfRunning


LOCATION_MODEL = LazyGetModelByName(settings.GEOCAM_TRACK_PAST_POSITION_MODEL)


class BasaltResource(geocamTrackModels.AbstractResource):
    resourceId = models.IntegerField(null=True, blank=True) # analagous to beacon id, identifier for track inputs
    vehicle = models.OneToOneField(plannerModels.Vehicle, blank=True, null=True)
    port = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.name
    

class DataType(models.Model):
    name = models.CharField(max_length=32)
    notes = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class BasaltTrack(geocamTrackModels.AbstractTrack):
    # set foreign key fields required by parent model to correct types for this site
    resource = models.ForeignKey(BasaltResource,
                                 related_name='%(app_label)s_%(class)s_related',
                                 verbose_name='Asset', blank=True, null=True)
    iconStyle = geocamTrackModels.DEFAULT_ICON_STYLE_FIELD()
    lineStyle = geocamTrackModels.DEFAULT_LINE_STYLE_FIELD()

    dataType = models.ForeignKey(DataType, null=True, blank=True)
    timezone = models.CharField(max_length=128, default=settings.TIME_ZONE)

    @classmethod
    def getTrackByName(cls, trackName):
        try:
            track = cls.objects.get(name=trackName)
        except cls.DoesNotExist:
            track = None
        return track

    def getTimezone(self):
        return pytz.timezone(self.timezone)
    
    def toMapDict(self):
        result = geocamTrackModels.AbstractTrack.toMapDict(self)
        result['type'] = 'Track'
        return result
    
    def __unicode__(self):
        return '%s %s' % (self.__class__.__name__, self.name)


class AbstractBasaltPosition(geocamTrackModels.AltitudeResourcePositionNoUuid):
    # set foreign key fields required by parent model to correct types for this site
    track = models.ForeignKey(BasaltTrack, db_index=True, null=True, blank=True)

    serverTimestamp = models.DateTimeField(db_index=True)

    class Meta:
        abstract = True


class CurrentPosition(AbstractBasaltPosition):
    pass


class PastPosition(AbstractBasaltPosition):
    pass


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
    # set foreign key fields required by parent model to correct types for this site
    vehicle = plannerModels.DEFAULT_VEHICLE_FIELD()
    group = plannerModels.DEFAULT_GROUP_FLIGHT_FIELD()

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
                    self.timezone = timezone
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
            scriptPath = os.path.join(settings.PROJ_ROOT, 'apps', 'basaltApp', 'scripts', 'evaTrackListener.py')
            command = "%s -o 127.0.0.1 -p %d -n %s -t %s" % (scriptPath, resource.port, self.vehicle.name[-1:], self.name)
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
    
    def getTreeJsonChildren(self):
        children = super(BasaltFlight, self).getTreeJsonChildren()
        children.append({"title": "Notes", 
                         "selected": False, 
                         "tooltip": "Notes for " + self.name, 
                         "key": self.uuid + "_notes", 
                         "data": {"json": reverse('xgds_map_server_objectsJson', kwargs={'object_name':'XGDS_NOTES_NOTE_MODEL',
                                                                                         'filter': 'flight__pk:'+str(self.pk)}),
                                 "sseUrl": "", 
                                 "type": 'MapLink', 
                                 }
                         })
        children.append({"title": "Images", 
                         "selected": False, 
                         "tooltip": "Images for " + self.name, 
                         "key": self.uuid + "_images", 
                         "data": {"json": reverse('xgds_map_server_objectsJson', kwargs={'object_name':'XGDS_IMAGE_IMAGE_SET_MODEL',
                                                                                         'filter': 'flight__pk:'+str(self.pk)}),
                                 "sseUrl": "", 
                                 "type": 'MapLink', 
                                 }
                         })
        children.append({"title": "Samples", 
                         "selected": False, 
                         "tooltip": "Samples for " + self.name, 
                         "key": self.uuid + "_samples", 
                         "data": {"json": reverse('xgds_map_server_objectsJson', kwargs={'object_name':'XGDS_SAMPLE_SAMPLE_MODEL',
                                                                                         'filter': 'flight__pk:'+str(self.pk)}),
                                 "sseUrl": "", 
                                 "type": 'MapLink', 
                                 }
                         })
        return children


class BasaltPlanExecution(plannerModels.AbstractPlanExecution):
    ''' 
    A Plan Execution that also includes an EV
    '''
    # set foreign key fields required by parent model to correct types for this site
    flight = models.ForeignKey(BasaltFlight, null=True, blank=True)
    plan = plannerModels.DEFAULT_PLAN_FIELD()

    ev = models.ForeignKey(EV)
    
    def toSimpleDict(self):
        result = super(BasaltPlanExecution, self).toSimpleDict()
        if self.ev:
            result['ev'] = self.ev.pk
        else:
            result['ev'] = None
        return result


class BasaltActiveFlight(plannerModels.AbstractActiveFlight):
    flight = models.OneToOneField(BasaltFlight, related_name="active")
    
class Triplicate(AbstractEnumModel):
    def __unicode__(self):
        return u'%s' % (self.display_name)


class BasaltSample(xgds_sample_models.AbstractSample):
    # set foreign key fields required by parent model to correct types for this site
    resource = models.ForeignKey(BasaltResource, null=True, blank=True)
    track_position = models.ForeignKey(PastPosition, null=True, blank=True)
    user_position = models.ForeignKey(PastPosition, null=True, blank=True, related_name="sample_user_set" )

    number = models.IntegerField(null=True)
    triplicate = models.ForeignKey(Triplicate, null=True)
    year = models.PositiveSmallIntegerField(null=True, default=int(timezone.now().strftime("%y")))
    flight = models.ForeignKey(BasaltFlight, null=True, blank=True)
    
    def buildName(self):
        number = ("%03d" % (int(self.number),))
        name = self.region.shortName + str(self.year) + self.type.value + '-' + str(number) + str(self.triplicate.value)
        return name
    
    def finish_initialization(self, request):
        self.flight = getFlight(self.collection_time, self.resource.vehicle)
        
    def updateSampleFromName(self, name):
        assert name
        
        dataDict = {}
        dataDict['region'] = name[:2]
        dataDict['year'] = name[2:4]
        dataDict['type'] = name[4:5]
        dataDict['number'] = name[6:9] 
        dataDict['triplicate'] = name[9:10]
         
        if not self.region:
            self.region = xgds_sample_models.Region.objects.get(shortName = dataDict['region'])
        if not self.type:
            self.type = xgds_sample_models.SampleType.objects.get(value = dataDict['type'])
        if not self.number:
            self.number = ("%03d" % (int(dataDict['number']),))
        if not self.triplicate:
            self.triplicate = Triplicate.objects.get(value=dataDict['triplicate'])
        if not self.year:
            self.year = int(dataDict['year']) 
        self.save()
    
    def toMapDict(self):
        result = xgds_sample_models.AbstractSample.toMapDict(self)
        result['type'] = 'Sample'
        if result['flight']:
            result['flight'] = self.flight.name
        if self.triplicate:
            result['triplicate'] = self.triplicate.display_name
        return result
    

class BasaltInstrumentDataProduct(AbstractInstrumentDataProduct):
    flight = models.ForeignKey(BasaltFlight, null=True, blank=True)
    resource = models.ForeignKey(BasaltResource, null=True, blank=True)
    
    def __unicode__(self):
        return "%s: %s, %s, %s, %s (portable), %s (mfg)" % (self.flight, self.resource, 
                                       self.acquisition_time, self.instrument.shortName,
                                       self.portable_mime_type, self.manufacturer_mime_type)


class FtirSample(models.Model):
    dataProduct = models.ForeignKey(BasaltInstrumentDataProduct)
    wavenumber = models.FloatField(db_index=True)
    reflectance = models.FloatField(db_index=True)

    class Meta:
        ordering = ['dataProduct', '-wavenumber']
        
    def __unicode__(self):
        return "%s: (%f, %f)" % (self.dataProduct.acquisition_time,
                           self.wavenumber, self.reflectance)


class AsdSample(models.Model):
    dataProduct = models.ForeignKey(BasaltInstrumentDataProduct)
    wavelength = models.FloatField(db_index=True)
    absorbance = models.FloatField(db_index=True)

    class Meta:
        ordering = ['dataProduct', 'wavelength']
        
    def __unicode__(self):
        return "%s: (%f, %f)" % (self.dataProduct.acquisition_time,
                                 self.wavelength, self.absorbance)
    

class BasaltUserSession(AbstractUserSession):
    location = models.ForeignKey(Location)
    resource = models.ForeignKey(plannerModels.Vehicle)
    
    @classmethod
    def getFormFields(cls):
        return ['role',
                'location',
                'resource']
    

class BasaltTaggedNote(AbstractTaggedNote):
    # set foreign key fields required by parent model to correct types for this site
    content_object = models.ForeignKey('BasaltNote')


class BasaltNote(AbstractLocatedNote):
    # set foreign key fields and manager required by parent model to correct types for this site
    position = models.ForeignKey(PastPosition, null=True, blank=True)
    tags = TaggableManager(through=BasaltTaggedNote, blank=True)

    flight = models.ForeignKey(BasaltFlight, null=True, blank=True)
    
    def calculateDelayedEventTime(self, event_time):
        if self.flight:
            return event_time - datetime.timedelta(seconds=self.flight.delaySeconds)
            
        return self.event_time

    def toMapDict(self):
        """
        Return a reduced dictionary that will be turned to JSON for rendering in a map
        """
        result = AbstractLocatedNote.toMapDict(self)
        result['type'] = 'Note'
        if self.flight:
            result['flight'] = self.flight.name
        else:
            result['flight'] = ''
        return result
    
    def getPosition(self):
        # IMPORTANT this should not be used across multitudes of notes, it is designed to be used during construction.
        if not self.position:
            self.position = getClosestPosition(timestamp=self.event_time, resource=self.flight.vehicle.basaltresource)
        return self.position


class BasaltImageSet(xgds_image_models.AbstractImageSet):
    # set foreign key fields from parent model to point to correct types
    camera = xgds_image_models.DEFAULT_CAMERA_FIELD()
    track_position = models.ForeignKey(PastPosition, null=True, blank=True )
    exif_position = models.ForeignKey(PastPosition, null=True, blank=True, related_name="%(app_label)s_%(class)s_image_exif_set" )
    user_position = models.ForeignKey(PastPosition, null=True, blank=True, related_name="%(app_label)s_%(class)s_image_user_set" )
    resource = models.ForeignKey(BasaltResource, null=True, blank=True)

    flight = models.ForeignKey(BasaltFlight, null=True, blank=True)
    
    def finish_initialization(self, request):
	vehicle = None
	if self.resource:
	    vehicle = self.resource.vehicle
        self.flight = getFlight(self.acquisition_time, vehicle)
        
    def toMapDict(self):
        """
        Return a reduced dictionary that will be turned to JSON for rendering in a map
        """
        result = xgds_image_models.AbstractImageSet.toMapDict(self)
        result['type'] = 'ImageSet'
        if self.flight:
            result['flight'] = self.flight.name
        else:
            result['flight'] = ''
        return result


class BasaltSingleImage(xgds_image_models.AbstractSingleImage):
    """ This can be used for screenshots or non geolocated images 
    """

    # set foreign key fields from parent model to point to correct types
    imageSet = models.ForeignKey(BasaltImageSet, null=True, related_name="images")
