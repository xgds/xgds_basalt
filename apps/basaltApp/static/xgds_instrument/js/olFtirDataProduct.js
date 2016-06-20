// render json sample information on the openlayers map

var FtirDataProduct = {
        initStyles: function() {
            if (_.isUndefined(this.styles)){
                this.styles = {};
                this.styles['iconStyle'] = new ol.style.Style({
                    image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                        src: '/static/xgds_instrument/images/instrument_icon.png',
                        scale: 0.8
                        }))
                      });
                this.styles['text'] = {
                    font: '12px Calibri,sans-serif',
                    fill: new ol.style.Fill({
                        color: 'black'
                    }),
                    stroke: new ol.style.Stroke({
                        color: 'cyan',
                        width: 2
                    }),
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
                name: "Instrument Data Product",
                source: new ol.source.Vector({
                    features: olFeatures
                }),
            });  
            return vectorLayer;
        },
        constructMapElement:function(dataJson){
            var coords = transform([dataJson.lon, dataJson.lat]);
            var feature = new ol.Feature({
                name: dataJson.instrument_name,
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
        setupPopup: function(feature, dataJson) {
            var data = [" ", "<a href='/xgds_map_server/view/FTIR/"  + dataJson.pk + "' target='_blank'>View FTIR</a>",
                        "EV:", dataJson.ev_name ? dataJson.ev_name : '',
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