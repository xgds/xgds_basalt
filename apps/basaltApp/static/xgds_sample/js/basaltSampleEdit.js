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
	showReplicateOptions: function() {
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
		//var selected = $("#id_sample_type option:selected").html();
		$("#id_replicate").children('option').hide();
		$("#id_replicate").removeAttr('disabled');
		if (selected == "Biology") {
			$("#id_replicate option[value='1']").show();
			$("#id_replicate option[value='2']").show();
			$("#id_replicate option[value='3']").show();
		} else if (selected == "ORG") {
			$("#id_replicate option[value='4']").show();
			$("#id_replicate option[value='5']").show();
		} else if ((selected == "Archive") || (selected == "Geology")) {
			$("#id_replicate").val('');
			$("#id_replicate").attr('disabled','disabled')
		} else if (selected = "Special") {
			$("#id_replicate option[value='6']").show();
			$("#id_replicate option[value='7']").show();
			$("#id_replicate option[value='8']").show();
			$("#id_replicate option[value='9']").show();
			$("#id_replicate option[value='10']").show();
		}
	},
	
	updateAdvancedInputFields: function() {
		this.advancedInputFields.push('#id_resource');
		this.advancedInputFields.push('#id_flight');
	},
	
	updateNonEditableFields: function() {
	},
	
	postInit: function() {
		// hook up the show replicate options to type change.
		var _this = this;
		$('#id_sample_type').change(_this.showReplicateOptions);
		$('#id_number').prop("disabled", true);
		
	},
	
	postDataLoad: function(data){
		this.showReplicateOptions();
	}
	
});




