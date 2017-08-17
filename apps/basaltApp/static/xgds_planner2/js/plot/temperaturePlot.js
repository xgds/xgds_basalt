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

hi_temp = {};

$.extend(hi_temp, {
	constructModel: function() {
		return new PlotDataTileModel({'name': 'Temp',
									  'dataFileUrl': '/data/xgds_map_server/mapData/Hawaii_Temperature_Island.8bit.png',
								   	  'lineColor': '#03c6c8',
								   	  'minValue': 0,
								   	  'maxValue': 40,
								   	  'update': UPDATE_ON.ModifyEnd,
								   	  'dataSourceUuid': '8a4a7b74-a6e1-4748-b456-ddfad959659a'  
								   	 });
		
	}
});