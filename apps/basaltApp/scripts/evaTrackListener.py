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

import logging

from zmq.eventloop import ioloop
ioloop.install()

import gevent
from gevent import socket
from gevent.queue import Queue

from geocamUtil.zmqUtil.publisher import ZmqPublisher
from geocamUtil.zmqUtil.util import zmqLoop
from django.core.cache import cache   
import datetime
import os

DEFAULT_HOST = '10.10.91.5'  # this is for in the field
DEFAULT_HOST = '127.0.0.1'

DEFAULT_PORT = 30000  # this is for in the field
DEFAULT_PORT = 50000

#subsystem status markers
OKAY = 1
WARNING = 2
ERROR = 3

#import django
#django.setup()

#from xgds_core.models import Constant

def socketListen(opts, q):
    logging.info('constructing socket')
    s = socket.socket()
    logging.info('connecting to server at host %s port %s',
                 opts.host, opts.port)
    s.connect((opts.host, opts.port))
    logging.info('connection established')

    buf = ''
    while True:
        buf += s.recv(4096)
        while '\n' in buf:
            line, buf = buf.split('\n', 1)
            q.put(line)


def setGpsDataQuality(msg):
    '''
    Sets 'GpsDataQuality' field in the memcache for subsystem status board
    '''
    dataQuality = msg.split(',')[2]
    if dataQuality == 'A':
        dataQuality = OKAY
    else: # dataQuality == 'V'
        dataQuality = ERROR
    logging.debug('Data Quality is : %s', dataQuality)
    # get the EV number from msg
    evNum = msg.split(':')[1]
    logging.debug('EVA NUM is : %s', evNum)
    if evNum == '1':
        cache.set('gpsDataQuality1', dataQuality)
    else: # Ev2
        cache.set('gpsDataQuality2', dataQuality)


def setSubsystemStatus(subsystemHostnames):
    for subsystem in subsystemHostnames:
        response = os.system("ping -c 1 " + subsystemHostnames[subsystem])
        if response == 0: # hostname is up
            logging.debug('SAVING %s', subsystem)
            logging.debug(datetime.datetime.utcnow())
            cache.set(subsystem, datetime.datetime.utcnow())
            

def zmqPublish(opts, q):
    p = ZmqPublisher(**ZmqPublisher.getOptionValues(opts))
    p.start()
    for line in q:
        msg = 'gpsposition:%s:%s:' % (opts.evaNumber, opts.trackName) + line
        logging.debug('publishing: %s', msg)
        
        # hostnames of subsystem for the status board.
        #subsystemHostnames = {}
        #subsystemHostnames['gpsController1'] = Constant.objects.get(name="EV1_TRACKING_IP").value
        #subsystemHostnames['gpsController2'] = Constant.objects.get(name="EV2_TRACKING_IP").value
        #subsystemHostnames['saCamera'] = Constant.objects.get(name="SA_TRACKING_IP").value
        #subsystemHostnames['redCamera'] = "10.10.24.75"
        
        #setSubsystemStatus(subsystemHostnames)
        #setGpsDataQuality(msg)
        p.pubStream.send(msg)


def evaTrackListener(opts):
    q = Queue()
    jobs = []
    try:
        jobs.append(gevent.spawn(socketListen, opts, q))
        jobs.append(gevent.spawn(zmqPublish, opts, q))
        jobs.append(gevent.spawn(zmqLoop))
        timer = ioloop.PeriodicCallback(lambda: gevent.sleep(0.1), 0.1)
        timer.start()
        gevent.joinall(jobs)
    finally:
        gevent.killall(jobs)


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog')
    ZmqPublisher.addOptions(parser, 'tracLinkListener')
    parser.add_option('-p', '--port',
                      default=DEFAULT_PORT,
                      help='TCP port where EVA track server listens [%default]')
    parser.add_option('-o', '--host',
                      default=DEFAULT_HOST,
                      help='TCP host where EVA track server listens [%default]')
    parser.add_option('-n', '--evaNumber',
                      default=1,
                      help=\
                      'EVA identifier for multi-EVA ops. e.g. 1,2... [%default]')
    parser.add_option('-t', '--trackName',
                      default="",
                      help=\
                'Track name to store GPS points. If blank will use active flight then EVA #')
    opts, _args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    if not opts.host:
        opts.host = DEFAULT_HOST
        print 'host is %s' % opts.host
    if not opts.port:
        opts.port = DEFAULT_PORT
        print 'port is %d' % opts.port

    evaTrackListener(opts)


if __name__ == '__main__':
    main()
