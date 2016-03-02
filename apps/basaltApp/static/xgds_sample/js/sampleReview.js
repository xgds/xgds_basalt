function constructSampleView(data) {
	var rawTemplate = $('#template-sample-view').html();
	var compiledTemplate = Handlebars.compile(rawTemplate);
	var newDiv = compiledTemplate(json);
	var sampleViewTemplate = $(newDiv);
	var newEl = $container.append(imageViewTemplate);
}

function activateButtons() {
    $("#cancel_edit").hide();
    $("#edit_sample_button").show();
	
	$("#edit_sample_button").click(function(event) {
	    event.preventDefault();
	    $("#edit_sample_button").hide();
	    $("#cancel_edit").show();
	});

	$("#cancel_edit").click(function(event) {
	    event.preventDefault();
	    $("#cancel_edit").hide();
	    $("#edit_sample_button").show();
	});
}

//datetime picker
var dateTimeOptions = {'controlType': 'select',
	  	       'oneLine': true,
	  	       'showTimezone': false,
	  	       'timezone': '-0000'
	 	       };

$("#id_collection_time").datetimepicker(dateTimeOptions);