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
import pytz
import traceback
from uuid import uuid4

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

from geocamUtil.zmqUtil.subscriber import ZmqSubscriber
from geocamUtil.zmqUtil.publisher import ZmqPublisher
from geocamUtil.zmqUtil.util import zmqLoop
from geocamTrack.models import (IconStyle,
                                LineStyle)

from plrpExplorer.models import (NewFlight,
                                 Beacon,
                                 ActiveFlight,
                                 Track,
                                 DataType,
                                 NewAssetPosition,
                                 NewAssetCurrentPosition,
                                 NewAssetPositionTracLink)

import django
django.setup()

from plrpExplorer import settings

DM_REGEX = re.compile(r'(?P<sign>-?)(?P<degrees>\d+)(?P<minutes>\d\d\.\d+)')
DEFAULT_ICON_STYLE = IconStyle.objects.get(name='default')
DEFAULT_LINE_STYLE = LineStyle.objects.get(name='default')
RAW_DATA_TYPE = DataType.objects.get(id=1)  # hard-coded elsewhere
BOAT_FLIGHT, _ = NewFlight.objects.get_or_create(name='boat',
                                                 defaults={'uuid': uuid4()})
BOAT_TRACK, _ = Track.objects.get_or_create(name='boat',
                                            defaults={'resource': BOAT_FLIGHT,
                                                      'iconStyle': DEFAULT_ICON_STYLE,
                                                      'lineStyle': DEFAULT_LINE_STYLE,
                                                      'dataType': RAW_DATA_TYPE})


def parseTracLinkDM(dm):
    m = DM_REGEX.match(dm.strip())
    assert m
    sign = -1 if m.group('sign') == '-' else 1
    degrees = int(m.group('degrees'))
    minutes = float(m.group('minutes'))
    return sign * (degrees + minutes / 60.0)


class TracLinkTelemetryCleanup(object):
    def __init__(self, opts):
        self.opts = opts
        self.subscriber = ZmqSubscriber(**ZmqSubscriber.getOptionValues(self.opts))
        self.publisher = ZmqPublisher(**ZmqPublisher.getOptionValues(self.opts))

    def start(self):
        self.publisher.start()
        self.subscriber.start()
        topics = ['traclink']
        for topic in topics:
            self.subscriber.subscribeRaw(topic + ':', getattr(self, 'handle_' + topic))

    def flush(self):
        # flush bulk saves to db if needed. currently no-op.
        pass

    def handle_traclink(self, topic, body):
        try:
            self.handle_traclink0(topic, body)
        except:  # pylint: disable=W0702
            logging.warning('%s', traceback.format_exc())
            logging.warning('exception caught, continuing')

    def handle_traclink0(self, topic, body):
        # example: 13,09/19/2013,05:17:39,  2831.3070, -8038.8460,  2831.3068, -8038.8459,205.2,   0.9

        serverTimestamp = datetime.datetime.now(pytz.utc)

        if body == 'NO DATA':
            logging.info('NO DATA')
            return

        # parse record
        targetId, d, t, shipLat, shipLon, lat, lon, shipHeading, depth = body.split(',')
        targetId = int(targetId)
        sourceTimestamp = datetime.datetime.strptime('%s %s' % (d, t), '%m/%d/%y %H:%M:%S')
        lat = parseTracLinkDM(lat)
        lon = parseTracLinkDM(lon)
        shipLat = parseTracLinkDM(shipLat)
        shipLon = parseTracLinkDM(shipLon)
        shipHeading = float(shipHeading)
        depth = float(depth)

        # calculate which track record belongs to
        cacheKey = 'traclink.track.%s' % targetId
        pickledTrack = cache.get(cacheKey)
        if pickledTrack:
            # cache hit, great
            track = pickle.loads(pickledTrack)
        else:
            # check db for a track matching this targetId
            try:
                beacon = Beacon.objects.get(targetId=targetId)
            except ObjectDoesNotExist:
                logging.warning('%s', traceback.format_exc())
                raise KeyError('Received TracLink position for the beacon with targetId %s. Please ensure there is a beacon with that targetId in the plrpExplorer Beacon table.' % targetId)

            try:
                activeFlight = ActiveFlight.objects.get(flight__beacon=beacon)
            except ObjectDoesNotExist:
                raise KeyError('Received TracLink position for the beacon with targetId %s (named "%s"). Please ensure there is an active flight using that beacon in the plrpExplorer NewFlight table.' % (targetId, beacon.name))

            flight = activeFlight.flight
            tracks = Track.objects.filter(resource=flight)
            assert len(tracks) in (0, 1)
            if tracks:
                # we already have a valid track, use that
                track = tracks[0]
            else:
                # must start a new track
                track = Track(name=flight.name,
                              resource=flight,
                              iconStyle=DEFAULT_ICON_STYLE,
                              lineStyle=DEFAULT_LINE_STYLE,
                              dataType=RAW_DATA_TYPE)
                track.save()

            # set cache for next time
            pickledTrack = pickle.dumps(track, pickle.HIGHEST_PROTOCOL)
            cache.set(cacheKey, pickledTrack,
                      settings.PLRP_TRACK_CACHE_TIMEOUT_SECONDS)

        ######################################################################
        # asset position
        ######################################################################

        # create a NewAssetPosition row
        params = {
            'track': track,
            'timestamp': serverTimestamp,
            'latitude': lat,
            'longitude': lon,
            'heading': None,  # traclink doesn't provide heading for tracked object
            'depthMeters': depth,
            'sourceTimestamp': sourceTimestamp,
            'serverTimestamp': serverTimestamp,
        }
        pos = NewAssetPosition(**params)
        pos.save()  # note: could queue for bulk save instead

        cpos = NewAssetCurrentPosition(**params)
        cpos.saveCurrent()
        self.publisher.sendDjango(cpos)

        # add fields to create a NewAssetPositionTracLink row
        params.update({
            'summary': pos,
            'targetId': targetId,
            'shipLatitude': shipLat,
            'shipLongitude': shipLon,
            'shipHeading': shipHeading,
        })
        posTracLink = NewAssetPositionTracLink(**params)
        posTracLink.save()  # note: could queue for bulk save instead

        ######################################################################
        # boat position
        ######################################################################

        params = {
            'track': BOAT_TRACK,
            'timestamp': serverTimestamp,
            'latitude': shipLat,
            'longitude': shipLon,
            'heading': shipHeading,
            'depthMeters': 0.0,
            'sourceTimestamp': sourceTimestamp,
            'serverTimestamp': serverTimestamp,
        }
        boatPos = NewAssetPosition(**params)
        boatPos.save()

        boatCPos = NewAssetCurrentPosition(**params)
        boatCPos.saveCurrent()
        self.publisher.sendDjango(boatCPos)


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    ZmqSubscriber.addOptions(parser, 'tracLinkTelemetryCleanup')
    ZmqPublisher.addOptions(parser, 'tracLinkTelemetryCleanup')
    opts, args = parser.parse_args()
    if args:
        parser.error('expected no args')

    logging.basicConfig(level=logging.DEBUG)
    d = TracLinkTelemetryCleanup(opts)
    d.start()
    atexit.register(d.flush)
    zmqLoop()

if __name__ == '__main__':
    main()
