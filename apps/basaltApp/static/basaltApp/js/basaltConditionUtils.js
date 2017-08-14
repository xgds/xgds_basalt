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

$.extend(condition, {
	updateColor: function(received) {
		var ch = received[1].fields;
		var cdiv = $('#conditionDiv');
		cdiv.removeClass (function (index, className) {
		    return (className.match (/(^|\s)alert-\S+/g) || []).join(' ');
		});
		if (!_.isEmpty(ch.activity_status)) {
			var status = ch.activity_status[0];
			if (status == 'activity_in_progress' || status == 'activity_started'){
				cdiv.addClass('alert-success');
			} else if (status == 'activity_completed' || status == 'activity_aborted'){
				cdiv.addClass('alert-danger');
			} else {
				cdiv.addClass('alert-info');
			}
		} else {
			cdiv.addClass('alert-info');
		}
	},
	getMessage: function(received) {
		var c = received[0].fields;
		var ch = received[1].fields;
		
		// EV# FLIGHT# (TIME): NAME STATUS
		var result = c.flight;
		result += ' (' + condition.getPrintableTime(ch.source_time, c.timezone) + '): '; // todo convert to the timezone
		result += c.name;
		result += ' ' + c.xgds_id;
		if (!_.isEmpty(ch.activity_status)){
			result += ' <strong>' + ch.activity_status[1] + '</strong>';
		}
		return result;
	},
	getCurrentConditions: function() {
		$.ajax({
            url: '/basaltApp/condition/activeJSON',
            dataType: 'json',
            success: $.proxy(function(data) {
            	if (!_.isEmpty(data)){
            		var fakeEvent = {data: data};
            		condition.handleConditionEvent(fakeEvent);
            	} else {
            		$('#conditionDiv').html('No active EVAs.');
            	}
            }, this),
            error: function(data){
            	$('#conditionDiv').html('No active EVAs.');
            }
          });
	}
});