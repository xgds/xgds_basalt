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

./dump_post_flight.sh

today=$(date +"%Y-%m-%d")
hostname=$(hostname)
rootdir=~/video_dumps

# make sure we have directories
mkdir $rootdir/$hostname
chmod ugo+rw $rootdir/$hostname

echo 'clearing old database dumps'
rm $rootdir/$hostname/*.s*
cp load_post_flight_$hostname.* $rootdir/$hostname/hostname
cp dump_post_flight.* $rootdir/$hostname/hostname

echo 'dumping'
read -s -p "enter mysql password" sqlpwd
mysql -u root -p xgds_basalt --password=$sqlpwd < ./dump_post_flight.sql
echo 'done dumping'

echo 'tarring'
cd $rootdir
tar -czvf ./$hostname/$hostname$today.tar.gz $hostname/*$today.sql $hostname/load_post_flight_$hostname.* $hostname/dump_post_flight.*
echo 'done'
