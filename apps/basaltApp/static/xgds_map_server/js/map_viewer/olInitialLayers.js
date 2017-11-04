//__BEGIN_LICENSE__
// Copyright (c) 2015, United States Government, as represented by the
// Administrator of the National Aeronautics and Space Administration.
// All rights reserved.
//
// The xGDS platform is licensed under the Apache License, Version 2.0
// (the "License"); you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// http://www.apache.org/licenses/LICENSE-2.0.
//
// Unless required by applicable law or agreed to in writing, software distributed
// under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.
//__END_LICENSE__

// DESCRIPTION -- define & override the initial openlayers hardcoded base layers

var setupSO2Worker = function() {
	var worker = new Worker('so2LayerManager.js');
	worker.postMessage();
};

if (!map_api_key) {
    getInitialLayers = function() {
 	return [new ol.layer.Tile({
                      source: new ol.source.MapQuest({layer: 'sat'})
        })]
    }
}
else {
    getInitialLayers = function() {
    		//app.vent.on('treeData:loaded', setupSO2Worker());
        return [
        		new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key: map_api_key,
                imagerySet: 'AerialWithLabels',
                maxZoom: 19})})
//             new ol.layer.Tile({
//                    source: new ol.source.XYZ({
//                        url: '/data/xgds_map_server/geoTiff/Kilauea_True_Color/{z}/{x}/{-y}.png',
//                    })
//                })
        	]
    }
}
