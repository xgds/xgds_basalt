function constructSampleView(data) {
	var rawTemplate = $('#template-sample-view').html();
	var compiledTemplate = Handlebars.compile(rawTemplate);
	var newDiv = compiledTemplate(json);
	var sampleViewTemplate = $(newDiv);
	var newEl = $container.append(imageViewTemplate);
}

//datetime picker
var dateTimeOptions = {'controlType': 'select',
	  	       'oneLine': true,
	  	       'showTimezone': false,
	  	       'timezone': '-0000'
	 	       };

$("#id_collection_time").datetimepicker(dateTimeOptions);