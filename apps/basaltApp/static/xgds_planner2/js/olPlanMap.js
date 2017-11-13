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

// render json plan information on the openlayers map (as a layer from the tree)

var Plan = {
        initStyles: function() {
            if (_.isUndefined(this.styles)){
                this.styles = {};
                this.styles['lineStyle'] = new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'yellow',
                        width: 2
                      })
                    });
                this.styles['station'] = new ol.style.Style({
                    image: new ol.style.Icon({
                        src: '/static/xgds_map_server/icons/placemark_circle.png',
                        scale: .8,
                        rotateWithView: false,
                        opacity: 1
                        })
                    });
                this.styles['boundary'] = new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: 'rgba(255, 255, 0, 0.8)',
                        width: 3
                    })
                });
                this.styles['tolerance'] = new ol.style.Style({
                    fill: new ol.style.Fill({
                        color: 'rgba(255, 255, 0, 0.3)',
                    })
                });
                this.styles['stationText'] = {
                    font: '16px Calibri,sans-serif,bold',
                    fill: new ol.style.Fill({
                        color: 'yellow'
                    }),
                    stroke: new ol.style.Stroke({
                        color: 'black',
                        width: 2
                    }),
                    offsetY: -20
                };
                this.styles['segmentText'] = {
                    font: '14px Calibri,sans-serif',
                    stroke: new ol.style.Stroke({
                        color: 'red',
                        width: 1
                    })
                };
             };
        },
        constructElements: function(plansJson){
            if (_.isEmpty(plansJson)){
                return null;
            }
            this.initStyles();
            var olFeatures = [];
            for (var i = 0; i < plansJson.length; i++) {
                var planFeatures = this.construct(plansJson[i]);
                olFeatures = olFeatures.concat(planFeatures);
            }
            var vectorLayer = new ol.layer.Vector({
                name: "Plans",
                source: new ol.source.Vector({
                    features: olFeatures
                })
            });  
            return vectorLayer;
        },
        construct: function(planJson){
            var allFeatures = [];
            var coords = [];
            var coord;
            for (var i = 0; i < planJson.sequence.length; i++){
                if (planJson.sequence[i].type == "Station"){
                    coord = transform(planJson.sequence[i].geometry.coordinates);
                    coords.push(coord);
                    var station = this.constructStation(planJson.sequence[i], coord);

                    // if (i == 0) station = this.initTextStyle(station, "Start");
                    // else if (i == planJson.sequence.length - 1) station = this.initTextStyle(station, "End");

                    allFeatures.push(station);
                    allFeatures.push(this.getBoundaryFeature(planJson.sequence[i]));
                    allFeatures.push(this.getToleranceFeature(planJson.sequence[i]));
                }
            }
            var lineFeature = new ol.Feature({
                name: planJson.name,
                geometry: new ol.geom.LineString(coords)
            });
            lineFeature.setStyle(this.styles['lineStyle']);
            this.setupLinePopup(lineFeature, planJson);
            allFeatures.unshift(lineFeature);
            return allFeatures;
        },
        constructStation: function(stationJson, coord){
            var feature = new ol.Feature({
                name: stationJson.id,
                geometry: new ol.geom.Point(coord),
                textStyle: this.styles['stationText']
            });
            feature.setStyle(this.styles['station']);
            this.setupStationPopup(feature, stationJson);
            return feature;
        },
        setupStationPopup: function(feature, stationJson) {
            var trString = "<tr><td>%s</td><td>%s</td></tr>";
            var formattedString = "<table>";
            for (var j = 0; j< 3; j++){
                formattedString = formattedString + trString;
            }
            formattedString = formattedString + "</table>"; 
            var data = ["Notes:", stationJson.notes,
                        "Lat:", stationJson.geometry.coordinates[1],
                        "Lon:", stationJson.geometry.coordinates[0]];
            feature['popup'] = vsprintf(formattedString, data);
        },
        setupLinePopup: function(feature, planJson) {
            var trString = "<tr><td>%s</td><td>%s</td></tr>";
            var formattedString = "<table>";
            for (var k = 0; k< 2; k++){
                formattedString = formattedString + trString;
            }
            formattedString = formattedString + "</table>";
            var data = ["Notes:", planJson.notes,
                        "Author:", planJson.author];
            feature['popup'] = vsprintf(formattedString, data);
        },
        initTextStyle: function(feature, text) {
            var theText = new ol.style.Text(this.styles['stationText']);
            theText.setText(text);
            this.textStyle = new ol.style.Style({
                text: theText
            });
            if (!_.isUndefined(feature)){
                feature.set('textStyle', this.textStyle);
            }
            return feature;
        },
		getToleranceGeometry: function(stationJson) {
			if ('tolerance' in stationJson) {
				var circle4326 = ol.geom.Polygon.circular(this.getSphere(), stationJson.geometry.coordinates, stationJson.tolerance, 64);
				return circle4326.transform(LONG_LAT, DEFAULT_COORD_SYSTEM);
			}
			return undefined;
		},
		getToleranceFeature: function(stationJson) {
		    var toleranceFeature;
			var toleranceGeom = this.getToleranceGeometry(stationJson);
			var style = this.styles['tolerance'];
			if (toleranceGeom != undefined){
				if (toleranceFeature != undefined){
					toleranceFeature.setGeometry(toleranceGeom);
				} else {
					toleranceFeature = new ol.Feature({
                        geometry: toleranceGeom,
						id: stationJson.uuid + '_stn_tolerance',
						name: stationJson.id + '_stn_tolerance',
						model: stationJson,
						style: style});
					toleranceFeature.setStyle(style);
				}
			}

			return toleranceFeature;
		},
		getSphere: function() {
			if (_.isUndefined(app.wgs84Sphere)){
				app.wgs84Sphere = new ol.Sphere(app.options.BODY_RADIUS_METERS);
			}
			return app.wgs84Sphere;
		},
		getBoundaryGeometry: function(stationJson) {
			if ('boundary' in stationJson) {
				var circle4326 = ol.geom.Polygon.circular(this.getSphere(), stationJson.geometry.coordinates, stationJson.boundary, 64);
				return circle4326.transform(LONG_LAT, DEFAULT_COORD_SYSTEM);
			}
			return undefined;
		},
		getBoundaryFeature: function(stationJson) {
		    var boundaryFeature;
			var boundaryGeom = this.getBoundaryGeometry(stationJson);
			var style = this.styles['boundary']
			if (boundaryGeom != undefined){
				if (boundaryFeature != undefined){
					boundaryFeature.setGeometry(boundaryGeom);
				} else {
					boundaryFeature = new ol.Feature({
                        geometry: boundaryGeom,
						id: stationJson.uuid + '_stn_boundary',
						name: stationJson.id + '_stn_boundary',
						model: stationJson,
						style: style});
					boundaryFeature.setStyle(style);
				}
			}

			return boundaryFeature;
		},
}