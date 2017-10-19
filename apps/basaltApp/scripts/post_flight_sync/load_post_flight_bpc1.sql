# only load data from @hostname that is in /tmp/@hostname
set FOREIGN_KEY_CHECKS=0;
set @hostname='bpc1'
set @prefix='_video_'

set @today=DATE(NOW());
delete from xgds_video_videoepisode where startTime>@today;

set @sourceNum=CONVERT(SUBSTRING(@hostname,-1),UNSIGNED INTEGER);
delete from xgds_video_videosegment where startTime>@today and source_id=@sourceNum;

set @videoEpisodeFile=CONCAT('/tmp/',@hostname,'/',@hostname,'/',@hostname,@prefix,'episode',.sql');
set @videoEpisodeCmd=CONCAT("load data infile '@videoEpisodeFile' into table xgds_video_videoepisode");
PREPARE veStmt FROM @videoEpisodeCmd;
EXECUTE veStmt;

set @videoSegmentFile=CONCAT('/tmp/',@hostname,'/',@hostname,'/',@hostname,@prefix,'segment','.sql');
set @videoSegmentCmd=CONCAT("load data infile '@videoSegmentFile' into table xgds_video_videosegment");
PREPARE vsStmt FROM @videoSegmentCmd;
EXECUTE vsStmt;

set @trackPrefix=DATE_FORMAT(@today, '%Y%m%d');

set @trackFile=CONCAT('/tmp/', @hostname, '/', @hostname, '/', @hostname, '_track','.sql');
set @trackCmd=CONCAT("load data infile '@trackFile' into table basaltApp_basalttrack");
PREPARE trackStmt FROM @trackCmd;
EXECUTE trackStmt;

set @positionFile=CONCAT('/tmp/', @hostname, '/', @hostname, '/', @hostname, '_position','.sql');
set @positionCmd=CONCAT("load data infile '@positionFile' into table basaltApp_pastposition");
PREPARE positionStmt FROM @positionCmd;
EXECUTE positionStmt;

set FOREIGN_KEY_CHECKS=1;
