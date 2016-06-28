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


$(function() {
    app.views = app.views || {};
    
    
    // This view class manages the map point for a single Station model
    app.views.StationPointView = Backbone.View
        .extend({
            initialize: function(options) {
                this.options = options || {};
                this.stationsVector = this.options.stationsVector;
                
                if (!options.stationsVector && !options.model) {
                    throw 'Missing a required option!';
                }
                this.stationsDecoratorsVector = this.options.stationsDecoratorsVector;
                var pmOptions = {};
                var name = '' + this.model._sequenceLabel;
                if (!_.isUndefined(this.model.get('name'))) {
                    name += ' ' + this.model.get('name');
                }
                pmOptions.name = name || this.model.toString();
                this.point = transform(this.model.get('geometry').coordinates); // lon, lat

                this.initIconStyle();
                this.initTextStyle();
                this.render();

                this.listenTo(this.model, 'change', this.redraw);
                this.listenTo(this.model, 'add:sequence remove:sequence',
                              function(command, collection, event) {
                                  if (command.hasParam('showWedge')) {
                                      this.redrawPolygons();
                                  } else if (command.get('type').indexOf('Pattern') > 0) {
                                      this.redrawPolygons();
                                  }
                              });
                this.model.on('station:remove', function() {
                    this.stationsVector.removeFeature(this.features[0]);
                    if (this.features.length > 1){
                		this.stationsDecoratorsVector.removeFeature(this.features[1]);
                	}
                }, this);
                
                this.listenTo(this.model, 'change', this.redrawTolerance);
                this.listenTo(this.model, 'change', this.redrawBoundary);

            },
            getToleranceGeometry: function() {
            	if ('tolerance' in this.model.attributes) {
            		var circle4326 = ol.geom.Polygon.circular(this.getSphere(), inverseTransform(this.point), this.model.get('tolerance'), 64);
            		return circle4326.transform(LONG_LAT, DEFAULT_COORD_SYSTEM);
            	}
            	return undefined;
            },
            redrawTolerance: function() {
            	this.toleranceGeometry = this.getToleranceGeometry();
                if (this.toleranceGeometry != null){
                	if (this.toleranceFeature != null){
                		this.toleranceFeature.setGeometry(this.toleranceGeometry);
                	}
                }
            },
            getSphere: function() {
            	if (_.isUndefined(app.wgs84Sphere)){
            		app.wgs84Sphere = new ol.Sphere(app.options.BODY_RADIUS_METERS);
            	}
            	return app.wgs84Sphere;
            },
            getBoundaryGeometry: function() {
            	if ('boundary' in this.model.attributes) {
            		var radius = this.model.get('boundary');
            		var circle4326 = ol.geom.Polygon.circular(this.getSphere(), inverseTransform(this.point), radius, 64);
            		return circle4326.transform(LONG_LAT, DEFAULT_COORD_SYSTEM);
            	}
            	return undefined;
            },
            redrawBoundary: function() {
            	this.boundaryGeometry = this.getBoundaryGeometry();
                if (this.boundaryGeometry != undefined){
                	if (this.boundaryFeature != null){
                		this.boundaryFeature.setGeometry(this.boundaryGeometry);
                	}
                }
//                if (!_.isUndefined(this.boundaryGeometry)) {
//                	this.boundaryGeometry.setCenter(this.point);
//                	this.boundaryGeometry.setRadius(this.model.get('boundary'));
//                }
            },
            
            redrawPolygons: function() {
            	//TODO implement
            },
            
            render: function() {
                this.geometry = new ol.geom.Point(this.point);
                this.features = [new ol.Feature({geometry: this.geometry,
                                               id: this.model.attributes['id'],
                                               name: this.model.attributes['id'],
                                               model: this.model,
                                               iconStyle: this.iconStyle,
                                               selectedIconStyle: this.selectedIconStyle,
                                               textStyle: this.textStyle,
                                               style: this.getStationStyles
                                            })]
            	this.features[0].setStyle(this.getStationStyles);
                this.features[0].set('selectedIconStyle', this.selectedIconStyle);
                this.features[0].set('iconStyle', this.iconStyle);
                this.features[0].set('textStyle', this.textStyle);
                
                // draw the tolerance circle
                this.toleranceGeometry = this.getToleranceGeometry();
                if (this.toleranceGeometry != null){
    	            this.toleranceFeature = new ol.Feature({geometry: this.toleranceGeometry,
    	                id: this.model.attributes['id'] + '_stn_tolerance',
    	                name: this.model.attributes['id'] + '_stn_tolerance',
    	                model: this.model,
    	                style: olStyles.styles['tolerance']});
    	            this.toleranceFeature.setStyle(olStyles.styles['tolerance']);
    	            this.features.push(this.toleranceFeature);
            		this.stationsDecoratorsVector.addFeature(this.toleranceFeature);
                }
                
             // draw the boundary circle
                this.boundaryGeometry = this.getBoundaryGeometry();
                if (this.boundaryGeometry != null){
    	            this.boundaryFeature = new ol.Feature({geometry: this.boundaryGeometry,
    	                id: this.model.attributes['id'] + '_stn_boundary',
    	                name: this.model.attributes['id'] + '_stn_boundary',
    	                model: this.model,
    	                style: olStyles.styles['boundary']});
    	            this.boundaryFeature.setStyle(olStyles.styles['boundary']);
    	            this.features.push(this.boundaryFeature);
            		this.stationsDecoratorsVector.addFeature(this.boundaryFeature);
                }

                this.geometry.on('change', this.geometryChanged, this);

                this.model['feature'] = this.features[0];
                this.stationsVector.addFeature(this.features[0]);
            },
            
            geometryChanged: function(event) {
            	this.point = this.geometry.getCoordinates();
            	 var coords = inverseTransform(this.point);
            	 var oldCoords = this.model.getPoint();
//            	 if (oldCoords[0] != coords[0] && oldCoords[1] != coords[1]){
            		 this.model.setPoint({
                         lng: coords[0],
                         lat: coords[1]
                     });
//            	 }
                 this.redrawTolerance();
            },
            
            redraw: function() {
                if (_.isUndefined(this.geometry)){
                    return;
                }
                // redraw code. To be invoked when relevant model attributes change.
                app.Actions.disable();

                this.point = transform(this.model.get('geometry').coordinates);
                var existingCoords = this.geometry.getCoordinates();
                if ((this.point[0] != existingCoords[0]) || 
                    (this.point[1] != existingCoords[1])) {
                    this.geometry.setCoordinates(this.point);
                }
                var newLabel = this.getLabel()
                if (!_.isEqual(newLabel, this.textStyle.getText().getText())){
                	this.textStyle.getText().setText(newLabel);
                }
                this.updateHeadingStyle();

                if (this.wedgeViews) {
                    _.each(this.wedgeViews, function(wedgeView) {
                        wedgeView.update();
                    });
                }
                if (this.commandViews) {
                    _.each(this.commandViews, function(commandView) {
                        commandView.update();
                    });
                }
                this.redrawTolerance();
                this.features[0].changed();
                app.Actions.enable();
            },

            getHeading: function() {
                var heading = 0.0;
                try {
                    heading = this.model.get('headingDegrees');
                } catch(err) {
                    // nothing
                }
                if (_.isUndefined(heading) || _.isNull(heading)){
                    heading = 0.0;
                }  
                return heading;
            },
            
            initIconStyle: function() {
                if (this.model.get('isDirectional')) {
                    heading = this.getHeading();
                    olStyles.styles['direction']['rotation'] = heading;
                    olStyles.styles['selectedDirection']['rotation'] = heading;
                    this.iconStyle = new ol.style.Style({image: new ol.style.Icon(olStyles.styles['direction'])});
                    this.selectedIconStyle = new ol.style.Style({image: new ol.style.Icon(olStyles.styles['selectedDirection'])});
                    olStyles.styles['direction']['rotation'] = 0.0;
                    olStyles.styles['selectedDirection']['rotation'] = 0.0;
                } else {
                    this.iconStyle = olStyles.styles['station'];
                    this.selectedIconStyle = olStyles.styles['selectedStation'];
                }
            },
            
            updateHeadingStyle: function() {
                if (this.model.get('isDirectional')) {
                    var heading = this.getHeading();
                    this.iconStyle.set('rotation', heading);
                    this.selectedIconStyle.set('rotation', heading);
                } 
            },
            
            getLabel: function() {
                var name = '' + this.model._sequenceLabel;
                var modelname = this.model.get('name');
                if (!_.isUndefined(modelname) && !_.isEmpty(modelname)){
                    name += ' ' + modelname;
                }
                return name;
            },
            
            initTextStyle: function() {
                var theText = new ol.style.Text(olStyles.styles['stationText']);
                theText.setText(this.getLabel());
                this.textStyle = new ol.style.Style({
                    text: theText
                });
                if (!_.isUndefined(this.features)){
                	this.features[0].set('textStyle', this.textStyle);
                }
            },
            
            getStationStyles: function(feature, resolution){
            	result = [];
            	var model = this.model;
            	var selectedIconStyle = this.selectedIconStyle;
            	var iconStyle = this.iconStyle;
            	var textStyle = this.textStyle;
            	if (_.isUndefined(model)){
            		// this is the feature
            		model = this.get('model');
            		selectedIconStyle = this.get('selectedIconStyle');
                	iconStyle = this.get('iconStyle');
                	textStyle = this.get('textStyle');
            	}
            	if (app.State.stationSelected === model){
            		return [selectedIconStyle, textStyle];
            	} else {
            		return [iconStyle, textStyle];
            	}
            },

            close: function() {
                this.stopListening();
            }

        });
});
