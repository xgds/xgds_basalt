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

import socket
import serial

port = 40001

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("", port))

ser = serial.Serial()
ser.baudrate=19200
ser.port = '/dev/ttyS0'
ser.open()

print "send compass serial data:", port
while 1:
    l = ser.readline()
    s.sendto(l, 'localhost')
    print l,
