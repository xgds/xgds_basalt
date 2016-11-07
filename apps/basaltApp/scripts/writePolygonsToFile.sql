select uuid, name, description, visible, popup, showLabel, image, height, width, polygon, labelStyle_id, mapLayer_id, style_id 
into outfile '/tmp/tempSql/groundoverlay.sql' from xgds_map_server_groundoverlay;

select uuid, name, description, visible, popup, showLabel, polygon, labelStyle_id, mapLayer_id, style_id 
into outfile '/tmp/tempSql/polygon.sql' from xgds_map_server_polygon;

select uuid, name, description, visible, popup, showLabel, point, icon_id, labelStyle_id, mapLayer_id, style_id 
into outfile '/tmp/tempSql/point.sql' from xgds_map_server_point;

select uuid, name, description, visible, popup, showLabel, lineString, labelStyle_id, maplayer_id, style_id 
into outfile '/tmp/tempSql/linestring.sql' from xgds_map_server_linestring;
