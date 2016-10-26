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

app.views = app.views || {};

app.views.PlanLinksView = Backbone.View.extend({
    template: '#template-plan-links',
    initialize: function() {
	Handlebars.registerHelper('optimizeSelected', function (input, optimize) {
            return input === optimize ? 'selected' : '';
        });
        var source = $(this.template).html();
        if (_.isUndefined(source)) {
            this.template = function() {
                return '';
            };
        } else {
            this.template = Handlebars.compile(source);
        }
    },
    getBoundingExtent: function() {
    	var extent = app.map.planView.getPlanExtens();
    	var amount = 5.0;
    	extent[0] = extent[0] - amount;
        extent[1] = extent[1] - amount;
        extent[2] = extent[2] + amount;
        extent[3] = extent[3] + amount;
        var firstCoords = inverseTransform([extent[0], extent[1]]);
        var lastCoords = inverseTransform([extent[2], extent[3]]);
        var result =  [firstCoords[0], firstCoords[1], lastCoords[0], lastCoords[1]];
        return result;
    },
    render: function() {
        this.$el.html(this.template({
            planLinks: app.planLinks,
            planUuid: app.currentPlan.get('uuid'),
            planId: app.currentPlan.get('serverId'),
            optimization: app.currentPlan.get('optimization')
        }));
        var callback = app.options.XGDS_PLANNER2_LINKS_LOADED_CALLBACK;
        if (callback != null) {
            callback(this.$el);
        }
        var context = this;
        this.$el.find('#pextantButton').click(function(event) {
            event.preventDefault();
            var theForm = $("#pextantForm");
            var postData = theForm.serializeArray();
            postData.push({name:'extent', 'value': context.getBoundingExtent()})
            $('#pextantMessage').text('Sextant is processing, stand by...');
            $.ajax(
        	        {
        	            url: "/basaltApp/pextant/" + app.currentPlan.get('serverId'),
        	            type: "POST",
        	            data: postData,
        	            dataType: 'json',
        	            success: function(data)
        	            {
        	            	$('#pextantMessage').text(data.msg);
        	            	app.updatePlan(data.plan);
        	            },
        	            error: function(data)
        	            {
        	            	$('#pextantMessage').text(data.responseJSON.msg);
        	            	app.updatePlan(data.responseJSON.plan);
        	            }
        	        });
        });
        this.$el.find('#clearPextantButton').click(function(event) {
            event.preventDefault();
            var theForm = $("#pextantForm");
            var postData = theForm.serializeArray();
            $('#pextantMessage').text('Clearing sextant route...');
            $.ajax(
        	        {
        	            url: "/basaltApp/pextant/" + app.currentPlan.get('serverId') +'/1',
        	            type: "POST",
        	            data: postData,
        	            dataType: 'json',
        	            success: function(data)
        	            {
        	            	$('#pextantMessage').text(data.msg);
        	            	app.updatePlan(data.plan);
        	            },
        	            error: function(data)
        	            {
        	            	$('#pextantMessage').text(data.responseJSON.msg);
        	            	app.updatePlan(data.responseJSON.plan);
        	            }
        	        });
        });
    }
});