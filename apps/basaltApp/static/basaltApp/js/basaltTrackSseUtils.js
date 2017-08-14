// __BEGIN_LICENSE__
//Copyright (c) 2015, United States Government, as represented by the 
//Administrator of the National Aeronautics and Space Administration. 
//All rights reserved.
//
//The xGDS platform is licensed under the Apache License, Version 2.0 
//(the "License"); you may not use this file except in compliance with the License. 
//You may obtain a copy of the License at 
//http://www.apache.org/licenses/LICENSE-2.0.
//
//Unless required by applicable law or agreed to in writing, software distributed 
//under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR 
//CONDITIONS OF ANY KIND, either express or implied. See the License for the 
//specific language governing permissions and limitations under the License.
// __END_LICENSE__


$.extend(trackSse, {
	staticIconPrefix: '/static/basaltApp/icons/',
	getTrackModel: function() {
		return app.options.searchModels['Actual_Traverse'].model;
	},
	convertTrackNameToChannel: function(track_name){
		// override 
		var splits = track_name.split('_');
		if (splits.length > 1){
			return splits[1];
		}
		return track_name;
	},
	renderTrack: function(channel, data) {
		var elements = Actual_Traverse.constructElements([data]);
		trackSse.tracksGroup.getLayers().push(elements);
		trackSse.olTracks[channel] = elements;
	}
	
});

