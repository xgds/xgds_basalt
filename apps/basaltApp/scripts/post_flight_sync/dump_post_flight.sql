set @today=DATE(NOW());
set @prefix='_video_';
set @rootdir='/home/irg/video_dumps/';

set @videoEpisodeFile=CONCAT(@rootdir,@@global.hostname,'/',@@global.hostname,@prefix,'episode_',@today,'.sql');
set @videoEpisodeCmd=CONCAT("select * from xgds_video_videoepisode where startTime>@today into outfile '",@videoEpisodeFile,"'");
PREPARE veStmt FROM @videoEpisodeCmd;
EXECUTE veStmt;

set @videoSegmentFile=CONCAT(@rootdir,@@global.hostname,'/',@@global.hostname,@prefix,'segment_',@today,'.sql');
set @videoSegmentCmd=CONCAT("select * from xgds_video_videosegment where startTime>@today into outfile '",@videoSegmentFile,"'");
PREPARE vsStmt FROM @videoSegmentCmd;
EXECUTE vsStmt;

set @trackPrefix=DATE_FORMAT(@today, '%Y%m%d');
set @trackFile=CONCAT(@rootdir,@@global.hostname,'/',@@global.hostname,'_track_',@today,'.sql');
set @trackCmd=CONCAT("select id, name, uuid, extras, 2 as dataType_id, iconStyle_id, lineStyle_id, resource_id, timezone from basaltApp_basalttrack where name like concat(@trackPrefix,'%') into outfile '",@trackFile,"'");
PREPARE trackStmt FROM @trackCmd;
EXECUTE trackStmt;

set @positionFile=CONCAT(@rootdir,@@global.hostname,'/',@@global.hostname,'_position_',@today,'.sql');
set @positionCmd=CONCAT("select * from basaltApp_pastposition where timestamp>@today into outfile '",@positionFile,"'");
PREPARE positionStmt FROM @positionCmd;
EXECUTE positionStmt;
