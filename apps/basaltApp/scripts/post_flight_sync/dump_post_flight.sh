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

echo 'clearing old dump'
rm -rf /tmp/boat_old
mv /tmp/boat /tmp/boat_old
mkdir /tmp/boat
cp load_post_flight.* /tmp/boat
chmod ugo+rw /tmp/boat

echo 'dumping'
read -s -p "enter mysql password" sqlpwd
mysql -u root -p pavilion_lake --password=$sqlpwd < ./dump_post_flight.sql
echo 'done dumping'

echo 'tarring'
cd /tmp
tar -czvf ./boat/boat.tar.gz boat/*.s*
echo 'done'
