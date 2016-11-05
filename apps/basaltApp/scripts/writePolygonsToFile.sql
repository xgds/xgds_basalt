select uuid, name, description, visible, popup, showLabel, image, height, width, polygon, labelStyle_id, mapLayer_id, style_id 
into outfile '/tmp/groundoverlay.sql' from xgds_map_server_groundoverlay;

select uuid, name, description, visible, popup, showLabel, polygon, labelStyle_id, maplayer_id, style_id 
into outfile '/tmp/polygon.sql' from xgds_map_server_polygon;

select uuid, name, description, visible, popup, showLabel, point, labelStyle_id, maplayer_id, style_id 
into outfile '/tmp/point.sql' from xgds_map_server_point;

select uuid, name, description, visible, popup, showLabel, linestring, labelStyle_id, maplayer_id, style_id 
into outfile '/tmp/linestring.sql' from xgds_map_server_linestring;