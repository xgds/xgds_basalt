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
	getTrackModel: function() {
		return app.options.searchModels['Actual_Traverse'].model;
	},
	lookupImage: function(url){
		var result = undefined;
		$.each(trackSse.preloadedIcons, function(index, theImg){
			if (theImg.src == url){
				result = theImg;
			}
		});
		return result;
		
	},
	setupPositionIcon: function(channel){
		Position.initStyles();
		if (!(channel in Position.styles)){
			var pointerPath = '/static/basaltApp/icons/' + channel.toLowerCase() + '_pointer.png';
			var theImg = trackSse.lookupImage(pointerPath);
			// these were preloaded in MapView.html
			var theIcon = new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                src: pointerPath,
                img: theImg,  // this is for preload to fix Chrome.
                scale: 0.5
                }));

			var newStyle = new ol.style.Style({
                image: theIcon
            });
			Position.styles[channel] = newStyle;
		}
	}
});