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

DEFAULT_HOST = '10.10.91.5'  # this is for in the field
DEFAULT_HOST = '127.0.0.1'

DEFAULT_PORT = 30000  # this is for in the field
DEFAULT_PORT = 50000


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


def zmqPublish(opts, q):
    p = ZmqPublisher(**ZmqPublisher.getOptionValues(opts))
    p.start()
    for line in q:
        msg = 'traclink:' + line
        logging.debug('publishing: %s', msg)
        p.pubStream.send(msg)


def tracLinkListener(opts):
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
                      help='TCP port where TracLink server listens [%default]')
    parser.add_option('-o', '--host',
                      default=DEFAULT_HOST,
                      help='TCP host where TracLink server listens [%default]')
    opts, _args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

#     if ':' in opts.port:
#         opts.host, opts.port = opts.port.split(':', 1)
#         opts.port = int(opts.port)
#     else:
#         opts.host = '127.0.0.1'
#         opts.port = int(opts.port)
    if not opts.host:
        opts.host = DEFAULT_HOST
        print 'host is %s' % opts.host
    if not opts.port:
        opts.port = DEFAULT_PORT
        print 'port is %d' % opts.port

    tracLinkListener(opts)


if __name__ == '__main__':
    main()
