function constructSampleView(data) {
	var rawTemplate = $('#template-sample-view').html();
	var compiledTemplate = Handlebars.compile(rawTemplate);
	var newDiv = compiledTemplate(json);
	var sampleViewTemplate = $(newDiv);
	var newEl = $container.append(imageViewTemplate);
}
