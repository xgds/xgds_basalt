# only load data from boat that is in /tmp/boat
set FOREIGN_KEY_CHECKS=0;
set @today=DATE(NOW());

delete from xgds_video_videoepisode where startTime>@today;
delete from xgds_video_videosegment where startTime>@today;

load data infile '/tmp/boat/boat/boat_video_segment.sql' into table xgds_video_videosegment;
load data infile '/tmp/boat/boat/boat_video_episode.sql' into table xgds_video_videoepisode;

set FOREIGN_KEY_CHECKS=1;
