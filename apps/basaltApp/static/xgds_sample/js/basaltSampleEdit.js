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

var xgds_sample = xgds_sample || {};
$.extend(xgds_sample,{
	getFormFieldID: function(jsonKey) {  
		/**
		 * Construct field id from the json key from server
		 */
		// handle cases where json key doesn't match id
		if (jsonKey == "replicate_name") {
			return "id_replicate";
		} else if (jsonKey == "region_name") {
			return "id_region";
		} else if (jsonKey == "sample_type_name") {
			return "id_sample_type"; 
		} else if (jsonKey == "flight_name") {
			return "id_flight";
		} else if (jsonKey == "resource_name") {
			return "id_resource";
		} else {
			return "id_" + jsonKey;
		}
	},
	showReplicateOptions: function(replicate_name) {
		/**
		 * Triplicates Legend (sampleType = triplicates):
		 * Biology = A, B, C
		 * Chemistry = D, E
		 * Geology 
		 * Archive
		 */
		var selected = "Biology";
		try {
			var sample_type_el = $("#id_sample_type option:selected");
			selected = sample_type_el.text();
		} catch (err) {
			// pass
			console.log(err);
		}
		
		$("#id_replicate").children('option').hide();
		$("#id_replicate").removeAttr('disabled');
		if (selected == "Biology") {
			$("#id_replicate option[value='1']").show();
			$("#id_replicate option[value='2']").show();
			$("#id_replicate option[value='3']").show();
			xgds_sample.setDomElement("id_replicate", 'A');
		} else if (selected == "ORG") {
			$("#id_replicate option[value='4']").show();
			$("#id_replicate option[value='5']").show();
			xgds_sample.setDomElement("id_replicate", 'D');
		} else if ((selected == "Archive") || (selected == "Geology")) {
			$("#id_replicate").val('');
			$("#id_replicate").attr('disabled','disabled')
		} else if (selected = "Special") {
			$("#id_replicate option[value='6']").show();
			$("#id_replicate option[value='7']").show();
			$("#id_replicate option[value='8']").show();
			$("#id_replicate option[value='9']").show();
			$("#id_replicate option[value='10']").show();
			xgds_sample.setDomElement("id_replicate", 'F');
		}
		if (replicate_name != undefined){
			xgds_sample.setDomElement("id_replicate", replicate_name)
		} 
	},
	
	updateAdvancedInputFields: function() {
//		this.advancedInputFields.push('#id_resource');
//		this.advancedInputFields.push('#id_flight');
	},
	
	updateNonEditableFields: function() {
		this.nonEditableFields.push('#id_number');
	},
	hookSampleTypeListener: function() {
		$('#id_sample_type').off('change');
		$('#id_sample_type').on('change', this.showReplicateOptions);
	},
	postInit: function() {
		// hook up the show replicate options to type change.
		var _this = this;
		this.hookSampleTypeListener();
		$('#id_number').prop("disabled", true);
	},
	postDataLoad: function(data){
		this.hookSampleTypeListener();
		this.showReplicateOptions(data.replicate_name);
	}
});




