// render json note information on the openlayers map

var Note = {
		selectedStylePath: '/static/xgds_notes2/icons/post_office_selected.png',
		stylePath: '/static/xgds_notes2/icons/post_office.png',
        initStyles: function() {
            if (_.isUndefined(this.styles)){
                this.styles = {};
                this.styles['iconStyle'] = new ol.style.Style({
                	zIndex: 1,
                    image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                        src: this.stylePath,
                        scale: 0.25
                        }))
                      });
                this.styles['selectedIconStyle'] = new ol.style.Style({
                	zIndex: 10,
                    image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                        src: this.selectedStylePath,
                        scale: 0.25
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
                	zIndex: 1,
                    font: '12px Calibri,sans-serif',
                    fill: new ol.style.Fill({
                        color: 'black'
                    }),
                    stroke: this.styles['yellowStroke'],
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
                name: notesJson[0].type,
                source: new ol.source.Vector({
                    features: olFeatures
                }),
            });  
            return vectorLayer;
        },
        constructMapElement:function(noteJson){
        	noteJson.flattenedTags = '';
            var coords = transform([noteJson.lon, noteJson.lat]);
            var view_url = noteJson.content_url;
            if (_.isUndefined(view_url) || _.isEmpty(view_url)) {
            	view_url = '/xgds_map_server/view/' + noteJson.type + '/' + noteJson.pk;
            }
            var feature = new ol.Feature({
            	selected: false,
            	view_url: view_url,
                name: getLocalTimeString(noteJson.event_time, noteJson.event_timezone),
                uuid: noteJson.pk,
                pk: noteJson.pk,
                type: noteJson.type,
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
        setupPopup: function(feature, noteJson) {
            var trString = "<tr><td>%s</td><td>%s</td></tr>";
            var formattedString = "<table>";
            for (j = 0; j< 3; j++){
                formattedString = formattedString + trString;
            }
            formattedString = formattedString + "</table>";
            var data = ["Tags:", noteJson.flattenedTags,
                        "Note:", noteJson.content,
                        "Altitude:", noteJson.alt + " m",
                        "Flight:", noteJson.flight_name,
                        "Author:", noteJson.author_name];
            var popupContents = vsprintf(formattedString, data);
            feature['popup'] = popupContents;
        		
        }
}