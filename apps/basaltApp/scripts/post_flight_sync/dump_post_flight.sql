set @today=DATE(NOW());
set @prefix='_video_';

set @videoEpisodeFile=CONCAT('/tmp/',@@global.hostname,'/',@@global.hostname,@prefix,'episode_',@today,'.sql');
set @videoEpisodeCmd=CONCAT("select * from xgds_video_videoepisode where startTime>@today into outfile '",@videoEpisodeFile,"'");
PREPARE veStmt FROM @videoEpisodeCmd;
EXECUTE veStmt;

set @videoSegmentFile=CONCAT('/tmp/',@@global.hostname,'/',@@global.hostname,@prefix,'segment_',@today,'.sql');
set @videoSegmentCmd=CONCAT("select * from xgds_video_videosegment where startTime>@today into outfile '",@videoSegmentFile,"'");
PREPARE vsStmt FROM @videoSegmentCmd;
EXECUTE vsStmt;

