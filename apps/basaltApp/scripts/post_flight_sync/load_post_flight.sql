set FOREIGN_KEY_CHECKS=0;
set @today=DATE(NOW());
set @prefix='/tmp/boat/xgds_video_video';

delete from xgds_video_videoepisode;
delete from xgds_video_videosegment;

load data infile '/tmp/boat/xgds_video_videosegment.sql' into table xgds_video_videosegment;
load data infile '/tmp/boat/xgds_video_videoepisode.sql' into table xgds_video_videoepisode;

set FOREIGN_KEY_CHECKS=1;
