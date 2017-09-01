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

# TODO: Add args for network port, baud rate, and serial device

import socket
import serial

port = 40001

def broadcastCompassUdp(hostPortList, serialDevice, baudRate):
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Open serial connection to compass
    ser = serial.Serial()
    ser.baudrate = baudRate
    ser.port = serialDevice
    ser.open()

    print "Connected to compass at %s, speed: %d" % (serialDevice, baudRate)
    print "Sending compass serial data via UDP to:", hostPortList
    while True:
        l = ser.readline()
        for hostInfo in hostPortList:
            udpSocket.sendto(l, (hostInfo['hostname'], hostInfo['port']))
        print l,


def parseHostListStr(hostStr):
    hostPortInfo = []
    hostAndPortList = hostStr.split(",")
    for hostPlusPort in hostAndPortList:
        host, port = hostPlusPort.split(":")
        hostPortInfo.append({'hostname':host, 'port':int(port)})

    return hostPortInfo


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog --hostList <host1:port1, host2:port2...> ' +
                                   '--serialDevice <pathToSerialDevice> ' +
                                   '--baudRate <serialBaudRate>')
    parser.add_option('--hostList', dest="hostListStr",
                      help='list of hosts to send UDP compass data')
    parser.add_option('--serialDevice', dest="serialDevice",
                      help='path to serial device file')
    parser.add_option('--baudRate', dest="baudRate",
                      help='baud rate for serial device')
    opts, args = parser.parse_args()
    if len(args) != 0:
        parser.error('expected no arguments')
    if (not opts.hostListStr) or (not opts.serialDevice) or (not opts.baudRate):
        parser.error("All options are required")

    hostList = parseHostListStr(opts.hostListStr)
    print "Serial Dev: %s, Baud Rate: %s" % (opts.serialDevice, opts.baudRate)
    print "Parsed host info: %s" % hostList
    broadcastCompassUdp(hostList, opts.serialDevice, int(opts.baudRate))

if __name__ == '__main__':
    main()
