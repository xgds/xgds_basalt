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

$.extend(playback, {
	vehicleDriver : {
		lastUpdate: undefined,
		invalid: false,
		ranges: [],
		elements: [],
		lastIndex: 0,
		initialized: false,
		getStationTransform: function(currentTime, station) {
			return {location:transform(station.get('geometry').coordinates), rotation:null};
		},
		getSegmentTransform: function(currentTime, segment, index){
			// interpolate along straight line
			var range = this.ranges[index];
			var newRange = moment.range(range.start, currentTime);
			var currentDuration = newRange.diff('milliseconds') / 1000;
			var fullDuration = segment.getDuration();
			if (fullDuration == 0){
				console.log('ERROR -- SEGMENT DURATION 0' + segment._sequenceLabel);
				return null;
			}
			var geometry = segment.get('geometry');
			var derivedInfo = segment.get('derivedInfo');
			if (derivedInfo !== undefined){
				if (_.isEmpty(derivedInfo.distanceList)) {
					derivedInfo = null;
				}
			}
			if (geometry == undefined || derivedInfo == undefined){
				return this.getSegmentLineInterpolation(currentTime, segment, index, currentDuration, fullDuration);
			} else {
				return this.getSegmentPathInterpolation(currentTime, segment, currentDuration, fullDuration, derivedInfo);
			}
		},
		getSegmentPathInterpolation: function(currentTime, segment, currentDuration, fullDuration, derivedInfo) {
			
			var timeList = derivedInfo.timeList;
			var coordinates = segment.get('geometry').coordinates;
			if (coordinates == undefined) {
				// have not drawn path yet?
				//TODO throw exception
				return null;
			}

			var runningTotal = 0;
			if (currentDuration > 0){
				for (var i=0; i<timeList.length; i++) {
					runningTotal += timeList[i];
					if (runningTotal >= currentDuration){
						break;
					}
				}
			}
				
			var newcoordinates = undefined;
			var next = undefined;
			var prev = undefined;
			if (runningTotal == currentDuration){
				newcoordinates = coordinates[i];
				if (i < timeList.length){
					next = coordinates[i + 1];
					prev = coordinates[i];
				} else {
					next = coordinates[i];
					prev = coordinates[i-1];
				}
			} else if (runningTotal > currentDuration){
				// it is between previous and this
				var previousRunningTotal = runningTotal-timeList[i];
				var delta = currentDuration - previousRunningTotal;
				var percentage = delta / timeList[i];
				
				prev = coordinates[i-1];
				next = coordinates[i];
				
				try {
					var newx = prev[0] + ( percentage * (next[0] - prev[0]));
					var newy = prev[1] + ( percentage * (next[1] - prev[1]));
					newcoordinates = [newx, newy];
				} catch (e) {
					prev = undefined;
				}
			}
			
			if (next == undefined ) {
				return {location:transform(prev), rotation:0}
			} else if (prev == undefined) {
				return {location:transform(next), rotation:0}
			}

			var dx = next[1] - prev[1];
			var dy = next[0] - prev[0];
			var bearing = Math.atan2(dy, dx);
			if (bearing < 0){
				bearing = bearing + 2*Math.PI;
			}
			return {location:transform(newcoordinates), rotation:bearing};
		},
		getSegmentLineInterpolation: function(currentTime, segment, index, currentDuration, fullDuration){
			
			var percentage = currentDuration / fullDuration;
			
			var prevStation = this.elements[index - 1];
			var prev = prevStation.get('geometry').coordinates;
			var nextStation = this.elements[index + 1];
			var next = nextStation.get('geometry').coordinates;
			
			var newx = prev[0] + ( percentage * (next[0] - prev[0]));
			var newy = prev[1] + ( percentage * (next[1] - prev[1]));
			var newcoordinates = [newx, newy];
			
			var dx = next[1] - prev[1];
			var dy = next[0] - prev[0];
			var bearing = Math.atan2(dy, dx);
			if (bearing < 0){
				bearing = bearing + 2*Math.PI;
			}
			
			return {location:transform(newcoordinates), rotation:bearing};
		},
		getPosition: function(currentTime, index) {
			var pathElement = this.elements[index];
			if (pathElement.get('type') == 'Station') {
				return this.getStationTransform(currentTime, pathElement);
			} else if (pathElement.get('type') == 'Segment') {
				return this.getSegmentTransform(currentTime, pathElement, index);
			}
		},
		lookupTransform: function(currentTime, indexReference){
			// This will actually return the position and update the index.
			// You have to pass the index reference this way: {indexVariable: this.lastIndex}
			// because Javascript does not support passing objects by reference. 
			// This way we can both use and update the index variable by reference.
			var lastIndex = indexReference.indexVariable;
			if (this.elements.length == 0){
				return null;
			}
			if (lastIndex > this.ranges.length){
				lastIndex = this.ranges.length - 1;
			}
			if (currentTime === null || currentTime === undefined){
				return null;
			}
			if (currentTime.unix() == this.ranges[lastIndex].start.unix() || this.ranges[lastIndex].contains(currentTime)){
				return this.getPosition(currentTime, lastIndex);
			} else {
				// see if we went back
				if (currentTime.unix() < this.ranges[lastIndex].start.unix()){
					// iterate back
					while (lastIndex > 0) {
						lastIndex--;
						indexReference.indexVariable = lastIndex;
						if (currentTime.unix() == this.ranges[lastIndex].start.unix() || this.ranges[lastIndex].contains(currentTime)){
							return this.getPosition(currentTime, lastIndex);
						}
					}
					return null;
				}
				while (lastIndex < (this.ranges.length - 1)){
					lastIndex++;
					indexReference.indexVariable = lastIndex
					var theRange = this.ranges[lastIndex];
					if (theRange === undefined){
						return null;
					}
					if (currentTime.unix() == theRange.start.unix() || theRange.contains(currentTime)){
						return this.getPosition(currentTime, lastIndex);
					}
				}
			}
			return null;
			
		},
		analyze: function() {
			var plan = app.currentPlan;
			this.elements = [];
			this.ranges = [];
			if (plan.get('sequence').length < 3) {
				this.invalid = true;
				return true;
			} else {
				this.invalid = false;
			}
			
			var analysisTime = moment(app.getStartTime()).tz(app.getTimeZone());
			var _this = this;
			var seq = plan.get('sequence').toArray();
			
			for (var i=0; i<seq.length; i++){
				var pathElement = seq[i];
				var startTime = moment(analysisTime);
				analysisTime.add(pathElement.getDuration(), 's');
				var endTime = moment(analysisTime);
				this.ranges.push(moment.range(startTime, endTime))
				this.elements.push(pathElement);
			}
		},
		initialize: function() {
			if (this.initialized){
				return;
			}
			moment.tz.setDefault(app.getTimeZone());
			var _this = this;
			app.listenTo(app.vent, 'itemSelected:station', function(selected) {
                _this.setCurrentTime(selected); 
            });
            app.listenTo(app.vent, 'itemSelected:segment', function(selected) {
                _this.setCurrentTime(selected); 
            });
            app.listenTo(app.vent, 'updatePlanDuration', function() {
            	_this.pause();
            	_this.analyze();
            });
			this.analyze();
			this.initialized = true;
		},
		setCurrentTime: function(element) {
			// set the current time to the start time of this element
			var index = this.elements.indexOf(element);
			if (index >= 0){
				playback.setCurrentTime(this.ranges[index].start);
			}
		},
		doSetTime: function(currentTime){
			this.lastUpdate = moment(currentTime);
			var newPositionRotation = this.lookupTransform(this.lastUpdate, {indexVariable: this.lastIndex});
			if (newPositionRotation != null){
				app.vent.trigger('vehicle:change',newPositionRotation);
			}
		},
		start: function(currentTime){
			this.doSetTime(currentTime);
		},
		update: function(currentTime){
		    if (this.lastUpdate === undefined){
				this.doSetTime(currentTime);
				return;
			}
			var delta = currentTime.diff(this.lastUpdate);
			if (Math.abs(delta) >= 100) {
				this.doSetTime(currentTime);
			}
		},
		pause: function() {
			// noop
		}
	}
});