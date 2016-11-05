#!/bin/bash
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

#### RUN THIS FROM BOAT -- part 1 ###

echo 'query for polygon objects and write to file'
read -s -p "enter mysql password" sqlpwd
mysql -u root -p -h shore xgds_basalt --password=$sqlpwd < ./writePolygonsToFile.sql
echo 'finished writing to file'

echo 'copy files from shore'
scp irg@shore:/tmp/groundoverlay.sql /tmp/.
scp irg@shore:/tmp/polygon.sql /tmp/.
scp irg@shore:/tmp/point.sql /tmp/.
scp irg@shore:/tmp/linestring.sql /tmp/.

ssh irg@shore 'rm /tmp/groundoverlay.sql'
ssh irg@shore 'rm /tmp/polygon.sql'
ssh irg@shore 'rm /tmp/point.sql'
ssh irg@shore 'rm /tmp/linestring.sql'
echo 'finished copying files from shore'