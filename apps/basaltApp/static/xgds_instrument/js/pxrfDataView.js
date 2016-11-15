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
	renderPxrfData: function(dataProductJson, data){
		xgds_instrument.renderInstrumentPlot(dataProductJson, data.samples);
		xgds_instrument.renderPxrfElements(dataProductJson, data.elements);
	},
	renderPxrfElements: function(dataProductJson, elements){
		var theTable = $("#pxrf_element_table");
		var elementsDataTable = undefined;
		if ( ! $.fn.DataTable.isDataTable("#pxrf_element_table" ) ) {
			elementsDataTable = theTable.DataTable({data:elements,
													order: [ 1, 'desc' ],
													ordering: true,
													info: false,
													paging: false,
													searching: false,
													columnDefs: [ {
													    "targets": [1,2],
													    "render": function ( data, type, full, meta ) {
													      return data.toFixed(2);
													    }
													  } ]
													});
		} else {
			elementsDataTable = theTable.DataTable();
			elementsDataTable.clear();
			elementsDataTable.rows.add(elements);
			elementsDataTable.draw();
		}
	}
});

xgds_instrument.dataRenderers['pXRF'] = xgds_instrument.renderPxrfData;