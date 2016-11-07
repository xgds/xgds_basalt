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


#### RUN THIS FROM BOAT -- part 2 ####

echo 'inserting polygons into database'
read -s -p "enter mysql password" sqlpwd
mysql -u root -p xgds_basalt --password=$sqlpwd < ./insertPolygonsToDB.sql
echo 'done inserting to database'

echo 'deleting temporary files'
sudo rm -rf /tmp/tempSql/groundoverlay.sql
sudo rm -rf /tmp/tempSql/polygon.sql
sudo rm -rf /tmp/tempSql/linestring.sql
sudo rm -rf /tmp/tempSql/point.sql
echo 'done deleting temp files' 
