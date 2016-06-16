#!/usr/bin/env python
# __BEGIN_LICENSE__
#Copyright (c) 2015, United States Government, as represented by the 
#Administrator of the National Aeronautics and Space Administration. 
#All rights reserved.
#
#The xGDS platform is licensed under the Apache License, Version 2.0 
#(the "License"); you may not use this file except in compliance with the License. 
#You may obtain a copy of the License at 
#http://www.apache.org/licenses/LICENSE-2.0.
#
#Unless required by applicable law or agreed to in writing, software distributed 
#under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR 
#CONDITIONS OF ANY KIND, either express or implied. See the License for the 
#specific language governing permissions and limitations under the License.
# __END_LICENSE__

import pickle
import re
import logging
import atexit
import datetime
import traceback
import pytz
from uuid import uuid4

from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist

import django
django.setup()

from geocamUtil.zmqUtil.subscriber import ZmqSubscriber
from geocamUtil.zmqUtil.publisher import ZmqPublisher
from geocamUtil.zmqUtil.util import zmqLoop
from geocamTrack.models import (IconStyle, LineStyle)

from basaltApp.models import (BasaltActiveFlight,
                              BasaltResource,
                              CurrentPosition,
                              BasaltTrack,
                              PastPosition,
                              DataType)

cache = caches['default']

DM_REGEX = re.compile(r'(?P<degrees>\d+)(?P<minutes>\d\d\.\d+)')
DEFAULT_ICON_STYLE = IconStyle.objects.get(name='default')
DEFAULT_LINE_STYLE = LineStyle.objects.get(name='default')
RAW_DATA_TYPE = DataType.objects.get(name="RawGPSLocation") 
TRACK_CACHE_TIMEOUT = 30

def parseTracLinkDM(dm, hemi):
    m = DM_REGEX.match(dm.strip())
    assert m
    sign = -1 if ((hemi == "W") or (hemi == "S")) else 1
    degrees = int(m.group('degrees'))
    minutes = float(m.group('minutes'))
    return sign * (degrees + minutes / 60.0)


class GpsTelemetryCleanup(object):
    def __init__(self, opts):
        self.opts = opts
        self.subscriber = ZmqSubscriber(**ZmqSubscriber.getOptionValues(self.opts))
        self.publisher = ZmqPublisher(**ZmqPublisher.getOptionValues(self.opts))

    def start(self):
        self.publisher.start()
        self.subscriber.start()
        topics = ['gpsposition']
        for topic in topics:
            self.subscriber.subscribeRaw(topic + ':', getattr(self, 'handle_' + topic))

    def flush(self):
        # flush bulk saves to db if needed. currently no-op.
        pass

    def handle_gpsposition(self, topic, body):
        try:
            self.handle_gpsposition0(topic, body)
        except:  # pylint: disable=W0702
            logging.warning('%s', traceback.format_exc())
            logging.warning('exception caught, continuing')

    def handle_gpsposition0(self, topic, body):
        # example: 2:$GPMRC,225030.00,A,3725.1974462,N,12203.8994696,W,,,220216,0.0,E,A*2B

        serverTimestamp = datetime.datetime.now(pytz.utc)

        if body == 'NO DATA':
            logging.info('NO DATA')
            return

        # parse record
        resourceIdStr, trackName, content = body.split(":")
        resourceId = int(resourceIdStr)
        sentenceType, utcTime, activeVoid, lat, latHemi, lon,\
            lonHemi, speed, heading, date, declination, declinationDir,\
            modeAndChecksum = content.split(",")
        sourceTimestamp = datetime.datetime.strptime('%s %s' % (date, utcTime),
                                                     '%d%m%y %H%M%S.%f')
        sourceTimestamp = sourceTimestamp.replace(tzinfo=pytz.utc)
        lat = parseTracLinkDM(lat, latHemi)
        lon = parseTracLinkDM(lon, lonHemi)
        
        # save subsystem time for status
        cache.set('telemetryCleanup', datetime.datetime.utcnow())
        
        # calculate which track record belongs to
        cacheKey = 'gpstrack.%s' % resourceId
        pickledTrack = cache.get(cacheKey)
        if pickledTrack:
            # cache hit, great
            track = pickle.loads(pickledTrack)
        else:
            # check db for a track matching this resourceId
            try:
                basaltResource = BasaltResource.objects.get(resourceId=resourceId)
            except ObjectDoesNotExist:
                logging.warning('%s', traceback.format_exc())
                raise KeyError('Received GPS position for the EV with id %s. Please ensure there is a vehicle with that id in the BasaltResource table.' % resourceId)

            # Check for track name.  We use explicit name if specified, otherwise
            # we check for an active flight and finally use the resourceId
            if len(trackName):
                logging.info("Using track name from listener: %s" % trackName)
            if len(trackName) == 0:  # I.e. we were not given a name for track already
                try:
                    activeFlight = BasaltActiveFlight.objects.get(flight__vehicle__basaltresource=basaltResource)
                    trackName = activeFlight.flight.name
                    logging.info("Using track name from BasaltActiveFlight: %s" % trackName)
                except ObjectDoesNotExist:
                    trackName = basaltResource.name
                    logging.info("Using track name from EV arg: %s" % trackName)
                
            tracks = BasaltTrack.objects.filter(name=trackName)
            assert len(tracks) in (0, 1)
            if tracks:
                # we already have a valid track, use that
                track = tracks[0]
            else:
                # must start a new track
                track = BasaltTrack(name=trackName,
                              resource=basaltResource,
                              iconStyle=DEFAULT_ICON_STYLE,
                              lineStyle=DEFAULT_LINE_STYLE,
                              dataType=RAW_DATA_TYPE)
                track.save()

            # set cache for next time
            pickledTrack = pickle.dumps(track, pickle.HIGHEST_PROTOCOL)
            cache.set(cacheKey, pickledTrack, TRACK_CACHE_TIMEOUT)

        ######################################################################
        # asset position
        ######################################################################

        # create a NewAssetPosition row
        params = {
            'track': track,
            'timestamp': sourceTimestamp,
            'serverTimestamp': serverTimestamp,
            'latitude': lat,
            'longitude': lon,
             # may not have heading, but we'll try...
            'heading': float(heading) if len(heading) else None, 
            'altitude': None,
        }
        pos = PastPosition(**params)
        pos.save()  # note: could queue for bulk save instead

        cpos = CurrentPosition(**params)
        cpos.saveCurrent()
        self.publisher.sendDjango(cpos)


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    ZmqSubscriber.addOptions(parser, 'gpsTelemetryCleanup')
    ZmqPublisher.addOptions(parser, 'gpsTelemetryCleanup')
    opts, args = parser.parse_args()
    if args:
        parser.error('expected no args')

    logging.basicConfig(level=logging.DEBUG)
    d = GpsTelemetryCleanup(opts)
    d.start()
    atexit.register(d.flush)
    zmqLoop()

if __name__ == '__main__':
    main()
