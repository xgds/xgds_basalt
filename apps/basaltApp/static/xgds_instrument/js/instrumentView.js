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

var xgds_instrument = xgds_instrument || {};
$.extend(xgds_instrument,{
	clearMessage: function(msg){
        $('#instrument_message').html('<br/><br/>');
    },
    setMessage: function(msg){
        $('#instrument_message').html(msg);
    },
    showValue: function(x, y){
    	var str = this.labels[0] + ": "+ x + "<br/>" + this.labels[1] + ": " + y;
		xgds_instrument.setMessage(str);
    },
	getData: function(dataProductJson){
		if (this.plot != undefined){
			this.plot.destroy();
			this.plot = null;
		}
		this.setMessage('Loading data...');
		$.ajax({
            url: dataProductJson.jsonDataUrl,
            dataType: 'json',
            success: $.proxy(function(data) {
                if (_.isUndefined(data) || data.length === 0){
                    this.setMessage("None found.");
                } else {
                	this.clearMessage();
                    this.renderInstrumentPlot(dataProductJson, data);
                }
            }, this),
            error: $.proxy(function(data){
                this.setMessage("Search failed.");
            }, this)
          });
		
	},
	renderInstrumentPlot: function(dataProductJson, instrumentData){
		this.labels = app.options.searchModels[dataProductJson.instrument_name].plotLabels;
		this.plot = $.plot("#plotDiv", [{ data: instrumentData,
		                                  color: 'blue'}],
		                                { 
		                                series: {
		                    				lines: { show: true },
		                    				points: { show: false }
		                    			},
		                    			clickable: true,
		                    	        grid: {
		                    	        	backgroundColor: '#FFFFFF',
		                    	            hoverable: true,
		                    	            clickable: true,
		                    	            autoHighlight: true
		                    	        },
		                    	        shadowSize: 0,
		                    	        zoom: {
		                    	            interactive: true
		                    	        },
		                    	        pan: {
		                    	            interactive: true
		                    	        },
		                    	        axisLabels: {
		                    	            show: true
		                    	        },
		                    	        xaxes: [{
		                    	            axisLabel: this.labels[0]
		                    	        }],
		                    	        yaxes: [{
		                    	            axisLabel: this.labels[1]
		                    	        }]
		                    	        });
		
		
		$("#plotDiv").bind("plothover", function (event, pos, item) {
			if (item) {
				var x = item.datapoint[0],
					y = item.datapoint[1];
				xgds_instrument.plot.unhighlight();
				xgds_instrument.plot.highlight(item.series, item.datapoint);
				xgds_instrument.showValue(x, y);
			}
		});
	}
});
