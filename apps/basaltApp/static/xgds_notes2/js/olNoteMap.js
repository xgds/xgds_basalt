// render json note information on the openlayers map

var Note = {
        initStyles: function() {
            if (_.isUndefined(this.styles)){
                this.styles = {};
                this.styles['iconStyle'] = new ol.style.Style({
                    image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                        src: '/static/xgds_notes2/icons/post_office.png',
                        scale: 0.25
                        }))
                      });
                this.styles['text'] = {
                    font: '12px Calibri,sans-serif',
                    fill: new ol.style.Fill({
                        color: 'black'
                    }),
                    stroke: new ol.style.Stroke({
                        color: 'yellow',
                        width: 2
                    }),
                    offsetY: -15
                };
            }
        },
        constructElements: function(notesJson){
            if (_.isEmpty(notesJson)){
                return null;
            }
            this.initStyles();
            var olFeatures = [];
            for (var i = 0; i < notesJson.length; i++) {
                if (_.isNumber(notesJson[i].lat)) {
                    var noteFeature = this.constructMapElement(notesJson[i]);
                    olFeatures = olFeatures.concat(noteFeature);
                }
            }
            var vectorLayer = new ol.layer.Vector({
                name: "Notes",
                source: new ol.source.Vector({
                    features: olFeatures
                }),
            });  
            return vectorLayer;
        },
        constructMapElement:function(noteJson){
        	noteJson.flattenedTags = '';
            var coords = transform([noteJson.lon, noteJson.lat]);
            var feature = new ol.Feature({
                name: getLocalTimeString(noteJson.event_time, noteJson.event_timezone),
                uuid: noteJson.pk,
                geometry: new ol.geom.Point(coords)
            });
            feature.setStyle(this.getStyles(noteJson));
            this.setupPopup(feature, noteJson);
            return feature;
        },
        getStyles: function(noteJson) {
            var styles = [this.styles['iconStyle']];
            if (noteJson.tags != '') {
                var theText = new ol.style.Text(this.styles['text']);
                if (noteJson.tag_names.length > 0){
                	noteJson.flattenedTags = noteJson.tag_names.reduce(function(a, b) {
                		return a.concat(" " + b);
                	});
                }
                theText.setText(noteJson.flattenedTags);
                var textStyle = new ol.style.Style({
                    text: theText
                });
                styles.push(textStyle);
            }
            return styles;
        },
        setupPopup: function(feature, noteJson) {
            var trString = "<tr><td>%s</td><td>%s</td></tr>";
            var formattedString = "<table>";
            for (j = 0; j< 3; j++){
                formattedString = formattedString + trString;
            }
            formattedString = formattedString + "</table>";
            var data = ["Tags:", noteJson.flattenedTags,
                        "Note:", noteJson.content,
                        "Altitude:", noteJson.altitude + " m",
                        "Flight:", noteJson.flight_name,
                        "Author:", noteJson.author_name];
            var popupContents = vsprintf(formattedString, data);
            feature['popup'] = popupContents;
        		
        }
}