set FOREIGN_KEY_CHECKS = 0;
LOAD DATA INFILE '/tmp/tempSql/groundoverlay.sql' REPLACE INTO TABLE xgds_basalt.xgds_map_server_groundoverlay;
LOAD DATA INFILE '/tmp/tempSql/polygon.sql' REPLACE INTO TABLE xgds_basalt.xgds_map_server_polygon;
LOAD DATA INFILE '/tmp/tempSql/linestring.sql' REPLACE INTO TABLE xgds_basalt.xgds_map_server_linestring;
LOAD DATA INFILE '/tmp/tempSql/point.sql' REPLACE INTO TABLE xgds_basalt.xgds_map_server_point;
set FOREIGN_KEY_CHECKS = 1;
