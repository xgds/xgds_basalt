set @today=DATE(NOW());
set @prefix='/tmp/boat/xgds_video_video';
set @videoEpisodeFile=CONCAT(@prefix,'episode_',@today,'.sql');
set @videoSegmentFile=CONCAT(@prefix,'segment_',@today,'.sql');

select * from xgds_video_videoepisode where startTime>@today into outfile @videoEpisodeFile;
select * from xgds_video_videosegment where startTime>@today into outfile @videoSegmentFile;

