# only load data from @hostname that is in @rootdir/@hostname
set @rootdir='/home/irg/video_dumps/';
set FOREIGN_KEY_CHECKS=0;
set @hostname='bpc2';
set @prefix='_video_';
set @today=DATE(NOW());

# LOOK UP EPISODE(S) FROM TODAY THAT MATCH EPISODE(S) THAT ARE BEING IMPORTED BY shortName
# GET THEIR PRIMARY KEY(S)
# UPDATE THE NEW SEGMENTS TO POINT TO THESE FOUND EXISTING EPISODES
# UPDATE EXISTING EPISODE START END TIMES IF NECESSARY
# IF THERE ARE NO MATCHING EPISODES THEN GO AHEAD AND IMPORT THE ONES FROM THE FILE

# Clear out and create a temp table to hold the incoming episodes
DROP TEMPORARY TABLE IF EXISTS tmp_video_episode;
CREATE TEMPORARY TABLE tmp_video_episode   (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `shortName` varchar(32) DEFAULT NULL,
  `startTime` datetime DEFAULT NULL,
  `endTime` datetime DEFAULT NULL,
  `uuid` varchar(48) NOT NULL,
  `sourceGroup_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
); 

# load the incoming episodes into the temp table
load data infile '/home/irg/video_dumps/bpc1/bpc1_video_episode.sql' into table tmp_video_episode;

# Clear out and create a temp table to hold the incoming segments
DROP TEMPORARY TABLE IF EXISTS tmp_video_segment;
CREATE TEMPORARY TABLE `tmp_video_segment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `directoryName` varchar(256) NOT NULL,
  `segNumber` int(10) unsigned DEFAULT NULL,
  `indexFileName` varchar(50) NOT NULL,
  `startTime` datetime DEFAULT NULL,
  `endTime` datetime DEFAULT NULL,
  `uuid` varchar(48) NOT NULL,
  `episode_id` int(11) DEFAULT NULL,
  `settings_id` int(11) DEFAULT NULL,
  `source_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`));
  
# load the incoming segments into the temp table
load data infile '/home/irg/video_dumps/bpc1/bpc1_video_segment.sql' into table tmp_video_segment;

# update temp segments to have episode id that is matching the one coming in
CREATE TEMPORARY TABLE ve_ids (`episode_id` int(11) NOT NULL AUTO_INCREMENT, `temp_episode_id` int(11) NOT NULL, PRIMARY KEY (`episode_id`));
insert into ve_ids select ve.id, te.id from xgds_video_videoepisode ve, tmp_video_episode te where te.shortName=ve.shortName;
update tmp_video_segment s, ve_ids i set s.episode_id=i.episode_id where s.episode_id=i.temp_episode_id;

# TODO IMPORTANT if we never recorded video on the ground/boat computers then the above will fail.  Do something fancy. https://dev.mysql.com/doc/refman/5.7/en/control-flow-functions.html

# REMOVE EXISTING SEGMENTS FROM THE CORRECT SOURCE FOR TODAY.
# THIS ASSUMES YOU HAVE A HOSTNAME LIKE BPC1 OR BPC2 IT WILL NOT WORK FROM BPC3
set @sourceNum=CONVERT(SUBSTRING(@hostname,-1),UNSIGNED INTEGER);  
delete from xgds_video_videosegment where startTime>@today and source_id=@sourceNum;

# INSERT THE NEW VIDEO SEGMENTS
replace into xgds_video_videosegment select * from tmp_video_segment;

# UPDATE THE START TIMES OF THE EPISODES 
CREATE TEMPORARY TABLE ve_start (`id` int(11) NOT NULL AUTO_INCREMENT, `startTime` datetime DEFAULT NULL, PRIMARY KEY (`id`));
insert into ve_start select ve.id, min(vs.startTime) from xgds_video_videosegment vs, xgds_video_videoepisode ve  where ve.id=vs.episode_id and vs.episode_id in (select ve.id from xgds_video_videoepisode ve, tmp_video_episode te where te.shortName=ve.shortName) group by ve.id;
update xgds_video_videoepisode ve, ve_start vs set ve.startTime=vs.startTime where ve.id=vs.id;

# UPDATE THE END TIMES OF THE EPISODES
CREATE TEMPORARY TABLE ve_end (`id` int(11) NOT NULL AUTO_INCREMENT, `endTime` datetime DEFAULT NULL, PRIMARY KEY (`id`));
insert into ve_end select ve.id, max(vs.endTime) from xgds_video_videosegment vs, xgds_video_videoepisode ve  where ve.id=vs.episode_id and vs.episode_id in (select ve.id from xgds_video_videoepisode ve, tmp_video_episode te where te.shortName=ve.shortName) group by ve.id;
update xgds_video_videoepisode ve, ve_end vs set ve.endTime=vs.endTime where ve.id=vs.id;

# LOAD THE TRACK DATA IN, IT HAS A DIFFERENT DATA TYPE SO IT WILL COEXIST WITH OUR OTHER TRACK
load data infile '/home/irg/video_dumps/bpc1/bpc1_track.sql' replace into table basaltApp_basalttrack;

# LOAD THE POSITION DATA IN, IT WILL POINT TO THE NEW TRACK
load data infile '/home/irg/video_dumps/bpc1/bpc1_position.sql' replace into table basaltApp_pastposition;

# TODO WE ARE NOT REPLACING OUR TRACK AND POSITION DATA BECAUSE WE HAVE A TON OF FOREIGN KEYS THAT POINT TO THE EXISTING POSITIONS AND WE NEED A WAY TO UPDATE THEM NICELY.
set FOREIGN_KEY_CHECKS=1;
