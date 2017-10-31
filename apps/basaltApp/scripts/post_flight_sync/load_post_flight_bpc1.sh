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

today=$(date +"%Y-%m-%d")
# WE ONLY LOAD DATA FROM BOAT, EVER
hostname='bpc1'
rootdir=~/video_dumps

echo $today

path=$rootdir/$hostname/

echo 'dumping first'
/home/irg/xgds_basalt/apps/basaltApp/scripts/post_flight_sync/dump_post_flight.sh

echo 'renaming sql files for loading for $hostname'

episodeFilename=${path}${hostname}_video_episode_${today}.sql
episodeNewFilename=${path}${hostname}_video_episode.sql
cp ${episodeFilename} ${episodeNewFilename}

segmentFilename=${path}${hostname}_video_segment_${today}.sql
segmentNewFilename=${path}${hostname}_video_segment.sql
cp ${segmentFilename} ${segmentNewFilename}

trackFilename=${path}${hostname}_track_${today}.sql
trackNewFilename=${path}${hostname}_track.sql
cp ${trackFilename} ${trackNewFilename}

positionFilename=${path}${hostname}_position_${today}.sql
positionNewFilename=${path}${hostname}_position.sql
cp ${positionFilename} ${positionNewFilename}

sudo chown mysql:mysql ${path}*.sql

echo 'loading data from boat'
read -s -p "enter mysql password" sqlpwd
mysql -u root -p xgds_basalt --password=$sqlpwd < ./load_post_flight_$hostname.sql
echo ''
echo 'done loading'
