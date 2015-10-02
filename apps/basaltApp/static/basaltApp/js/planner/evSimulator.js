var ev = ev || {};

ev.Simulator = function() {
    this.elapsedTime = 0; // seconds
    this.distanceTraveled = 0; // meters
    this.coordinates = {
        lng: null,
        lat: null
    };
};

_.extend(ev.Simulator.prototype, {
    // Queries
    getElapsedTimeSeconds: function() {
        return this.elapsedTime;
    },
    getDistanceTraveledMeters: function() {
        return this.distanceTraveled;
    },

    // Control

    geoJsonToCoords: function(geoJson) {
        return {
            lng: geoJson.coordinates[0],
            lat: geoJson.coordinates[1]
        };
    },

    startPlan: function(plan) {
        var firstStation = plan.get('sequence').at(0);
        this.coordinates = this.geoJsonToCoords(firstStation.get('geometry'));
    },
    endPlan: function(plan) {},

    startStation: function(station, context) {},
    endStation: function(station, context) {},

    startSegment: function(segment, context) {},
    endSegment: function(segment, context) {
        var nextCoords = this.geoJsonToCoords(context.nextStation.get('geometry'));
        var distanceVector = geo.calculateDiffMeters(nextCoords, this.coordinates);
        var norm = geo.norm(distanceVector);
        segment._segmentLength = norm;
        this.distanceTraveled = this.distanceTraveled + norm;

        var hintedSpeed = segment.get('hintedSpeed');
        if (typeof(hintedSpeed) == 'undefined' || hintedSpeed < 0) {
            hintedSpeed = context.plan.get('defaultSpeed');
        }
        var segmentDriveTime =  Math.round(norm / hintedSpeed);
        var derivedInfo = segment.get('derivedInfo');
        if (_.isUndefined(derivedInfo)){
        	derivedInfo = {};
        	segment.set('derivedInfo', derivedInfo);
        }
        derivedInfo['durationSeconds'] = segmentDriveTime;
        derivedInfo['distanceMeters'] = norm;
        this.elapsedTime = this.elapsedTime + segmentDriveTime;

        this.coordinates = nextCoords;
    },

    executeCommand: function(command, context) {
        var duration = command.get('duration');
        this.elapsedTime = this.elapsedTime + duration;
    }
});
