// render json sample information on the openlayers map

var FTIR = {
		selectedStylePath: '/static/xgds_instrument/images/instrument_icon_selected.png',
		stylePath: '/static/xgds_instrument/images/instrument_icon.png',
        initStyles: function() {
            if (_.isUndefined(this.styles)){
                this.styles = {};
                this.styles['iconStyle'] = new ol.style.Style({
                	zIndex: 1,
                    image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                        src: this.stylePath,
                        scale: 0.8
                        }))
                      });
                this.styles['selectedIconStyle'] = new ol.style.Style({
                	zIndex: 10,
                    image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                        src: this.selectedStylePath,
                        scale: 0.8
                        }))
                      });
                this.styles['yellowStroke'] =  new ol.style.Stroke({
                    color: 'yellow',
                    width: 2
                });
                this.styles['greenStroke'] =  new ol.style.Stroke({
                    color: 'green',
                    width: 2
                });
                this.styles['text'] = {
                    font: '12px Calibri,sans-serif',
                    fill: new ol.style.Fill({
                        color: 'black'
                    }),
                    stroke:this.styles['yellowStroke'],
                    offsetY: -15
                };
            }
        },
        constructElements: function(dataJson){
            if (_.isEmpty(dataJson)){
                return null;
            }
            this.initStyles();
            var olFeatures = [];
            for (var i = 0; i < dataJson.length; i++) {
                if (dataJson[i].lat !== "") {
                    var dataFeature = this.constructMapElement(dataJson[i]);
                    olFeatures = olFeatures.concat(dataFeature);
                }
            }
            var vectorLayer = new ol.layer.Vector({
                name: dataJson[0].type,
                source: new ol.source.Vector({
                    features: olFeatures
                }),
            });  
            return vectorLayer;
        },
        constructMapElement:function(dataJson){
            var coords = transform([dataJson.lon, dataJson.lat]);
            var feature = new ol.Feature({
            	selected: false,
            	view_url: dataJson.view_url,
                name: dataJson.instrument_name,
                pk: dataJson.pk,
                type: dataJson.type,
                geometry: new ol.geom.Point(coords)
            });
            feature.setStyle(this.getStyles(dataJson));
            this.setupPopup(feature, dataJson);
            return feature;
        },
        getStyles: function(dataJson) {
            var styles = [this.styles['iconStyle']];
            var theText = new ol.style.Text(this.styles['text']);
            theText.setText(dataJson.instrument_name);
            var textStyle = new ol.style.Style({
                text: theText
            });
            styles.push(textStyle);
            return styles;
        },
        selectMapElement:function(feature){
        	feature.selected = false;
        	var styles = feature.getStyle();
        	var newstyles = [this.styles['selectedIconStyle']];
        	var newtextstyle = styles[1];
        	newtextstyle.getText().setStroke(this.styles['greenStroke']);
        	newtextstyle.setZIndex(10);
        	newstyles.push(newtextstyle);
        	feature.setStyle(newstyles);
        },
        deselectMapElement:function(feature){
        	feature.selected = true;
        	var styles = feature.getStyle();
        	var newstyles = [this.styles['iconStyle']];
        	var newtextstyle = styles[1];
        	newtextstyle.getText().setStroke(this.styles['yellowStroke']);
        	newtextstyle.setZIndex(1);
        	newstyles.push(newtextstyle);
        	feature.setStyle(newstyles);
        },
        setupPopup: function(feature, dataJson) {
            var data = ["EV:", dataJson.ev_name ? dataJson.ev_name : '',
                        "Collector:", dataJson.collector_name ? dataJson.collector_name : '',
                        "Flight:", dataJson.flight_name ? dataJson.flight_name : '',
                        "Time:", dataJson.acquisition_time ? getLocalTimeString(dataJson.acquisition_time, dataJson.acquisition_timezone):''
                        ];

            var trString = "<tr><td>%s</td><td>%s</td></tr>";
            var formattedString = "<table>";
            for (j = 0; j< data.length/2; j++){
                formattedString = formattedString + trString;
            }
            formattedString = formattedString + "</table>";
            var popupContents = vsprintf(formattedString, data);
            
            feature['popup'] = popupContents;
        }
}