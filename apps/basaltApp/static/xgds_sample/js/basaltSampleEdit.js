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
	
	getFormFieldID: function(jsonKey) {  
		/**
		 * Construct field id from the json key from server
		 */
		return "id_" + jsonKey;
	},
	
	getSampleInfo: function() {
		/**
		 * Fetch the sample info from the server given its label number or name.
		 */
		var url = getSampleInfoUrl;
		var postData = {};
		postData[$("#search_input_type").val()] = $("#id_search_input").val();
		
		var _this = this;
		$.ajax({
			url: url,
			type: "POST",
			data: postData, // serializes the form's elements.
			success: function(data)
			{
				// insert data sent from the server.
				var json_dict = data[0];
				_this.updateLabelName(json_dict.label_number, json_dict.name);
				var field_id = "";
				for (var key in json_dict) {
					field_id = _this.getFormFieldID(key);
					field_val = json_dict[key];
					if($("#" + field_id).length != 0) {
						// id exists on page.
						$('#' + field_id).val(field_val);
					}
				}
				
				_this.updateNotes(json_dict);
		    	
			},
			error: function(request, status, error) {
				console.log("ERROR!")
			}
		});
	},
	
	updateNotes: function(data){
		//TODO if collection_time is null or changes must update
		var container = $('#notes_content');
		xgds_notes.initializeNotesReference(container, data.app_label, data.model_type, data.pk, data.collection_time, data.collection_timezone);
		xgds_notes.getNotesForObject(data.app_label, data.model_type, data.pk, 'notes_content', container.find('table.notes_list'));
	},
	
	updateLabelName: function(labelNum, sampleName) {
		// copy over the fields into hidden
    	$('#id_hidden_labelNum').val(labelNum);
    	$('#id_hidden_name').val(sampleName);
		$("#label_number_title").html("<strong> Label number: " + labelNum  + "</strong>");
    	if (_.isNull(sampleName) || sampleName == "") {
			$("#sample_name_title").html("<strong> Name: (Autofills on save) </strong>");
		} else {
			$("#sample_name_title").html("<strong>Name: " + sampleName  + "</strong>");
		}
	},
	
	getInputFieldsToUpdate: function() {
		/**
		 * Get only the input fields inside the form. 
		 */
		var input_fields = $(':input').not($("input[id='id_search_input']"));
		return input_fields.not($("select[class='sample_info_type']"));
	},
	
	clearMessages: function() {
		$('.messages').html('<br/>');
	},
	
	onEnterLoadSampleInfo: function(event) {
		/**
		 * On sample name or label number enter,
		 * enable the fields
		 * load sample data (ajax)
		 * (optional) copy over the label number or sample name field into form's hidden fields 
		 */
		// on label number field enter, get the sample info
	    if(event.keyCode == 13) {
	    	
	    	this.clearMessages();
	    	
	    	//if it's a name, make sure it passes sanity checks
	    	
	    	var searchType = $("#search_input_type").val();
	    	var searchInput = $("#id_search_input").val();
    		var numchars = searchInput.length;
    		if (numchars == 0) {
    			$("#error-message").html("Cannot search on nothing.");
    			return;
    		}
	    	if (searchType == "sampleName") {
	    		if ((numchars != 14) && (numchars != 15)) {
	    			$("#error-message").html("Sample name is not valid!");
	    			return;
	    		}
	    	}
	    	
			// enable fields
	    	var all_input_fields = this.getInputFieldsToUpdate();
	    	all_input_fields.prop("disabled", false);
	    	
			// clear the error message
			$("#error-message").html("");
			
	    	// ajax to get sample info for given label insert into the form.
	    	this.getSampleInfo();
	    }
	},
	
	onSampleInfoTypeValueChange: function() {
    	// fill in hidden data
    	var labelNum = $('#id_label_number').val();
    	$('#id_hidden_labelNum').val(labelNum);
    	var sampleName = $('#id_name').val();
    	$('#id_hidden_name').val(sampleName);
	},
	
	hideOutOfSimFields: function() {
		// hide out of sim fields
		$('#id_resource').parent().parent().hide();
		$('#id_latitude').parent().parent().hide();
		$('#id_longitude').parent().parent().hide();
		$('#id_altitude').parent().parent().hide();
		$('#id_flight').parent().parent().hide();
	},
	
	/**
	 * Show or hide the 'out of sim' fields.
	 */
	toggleAdvancedInput: function() {
		$('#id_resource').parent().parent().toggle();
		$('#id_latitude').parent().parent().toggle();
		$('#id_longitude').parent().parent().toggle();
		$('#id_altitude').parent().parent().toggle();
		$('#id_flight').parent().parent().toggle();
		if ($('#id_resource').is(":visible")) {
			$('.toggleInputFields').html('Close out-of-sim fields');	
		} else {
			$('.toggleInputFields').html('Open out-of-sim fields');	
		}
	},
	
	onSampleInfoTypeChange: function() {
		/**
		 * Enter sample info for given sample name or sample label number.
		 */ 
		if ($(".sample_info_type option:selected").val() == "sampleName") {
			$(".sample_info_type_value").html('<input id="id_name" name="name" type="text"/>  Press enter to load data.');
		} else {
			$(".sample_info_type_value").html('<input id="id_label_number" min="0" name="label" type="number"/>  Press enter to load data.');
		}
	},
	
	setupCollectorInput: function() {
		/**
		 * Autocomplete 'collector' field.
		 */
		// typeahead autocomplete for input fields
		var substringMatcher = function(strs) {
			return function findMatches(q, cb) {
				var matches, substringRegex;
				// an array that will be populated with substring matches
				matches = [];
				// regex used to determine if a string contains the substring `q`
				substrRegex = new RegExp(q, 'i');
				// iterate through the pool of strings and for any string that
				// contains the substring `q`, add it to the `matches` array
				$.each(strs, function(i, str) {
					if (substrRegex.test(str)) {
						matches.push(str);
					}
				});
				cb(matches);
			};
		};
		$('#id_collector').typeahead({
			hint: true,
			highlight: true,
			minLength: 1
		},
		{
			name: 'collector',
			source: substringMatcher(collectors)
		});
	},
	
	initializeSampleEditForm: function(){
		/**
		 * Initialize the sample edit form
		 */
		var _this = this;
		this.hideOutOfSimFields();
		this.setupCollectorInput();
		
		// handler for select box change event.
		$('.sample_info_type').change(function(event){
			_this.onSampleInfoTypeChange(); 
		});
		
		var all_input_fields = this.getInputFieldsToUpdate();
		// only disable fields if the form save succeeded or it's a new form
		if (fieldsEnabledFlag == 0) {
			all_input_fields.prop("disabled", true);
		}
		
		// handler for 'on enter' event.
		$('.sample_info_type_value').keyup(function(event){
			_this.onEnterLoadSampleInfo(event)
		});
		
		// handler for value change event
		$('.sample_info_type_value').change(function(event){
			_this.onSampleInfoTypeValueChange(event);
		});
		
		// hook up the show replicate options to type change.
		var _this = this;
		$('#id_sample_type').change(_this.showReplicateOptions);
		
		// if we get to edit page from sampleview, pull up the info
		if (existingSample) {
			// label number and name should be hidden within the form
			this.updateLabelName(hiddenLabel,hiddenName);
		}
		
		this.showReplicateOptions();
	}
});




