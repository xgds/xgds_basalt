#! /bin/bash

/home/irg/tungsten/tungsten/tools/tpm update --hosts=boat,shore --repl-svc-applier-filters=delay,replicate --property=replicator.filter.delay.delay=300 --property=replicator.filter.replicate.ignore=xgds_basalt.xgds_video_videosegment,xgds_basalt.xgds_video_videoepisode,xgds_basalt.xgds_core_constant,xgds_basalt.django_migrations

ssh boat ./tungsten/tungsten/tools/tpm update --hosts=boat,shore --repl-svc-applier-filters=delay,replicate --property=replicator.filter.delay.delay=300 --property=replicator.filter.replicate.ignore=xgds_basalt.xgds_video_videosegment,xgds_basalt.xgds_video_videoepisode,xgds_basalt.xgds_core_constant,xgds_basalt.django_migrations
