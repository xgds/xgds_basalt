var xgds_kn = xgds_kn || {};
var DRIVE_TIME_MULTIPLIER = 1;
var ROTATION_ADDITION = 20;

xgds_kn.Simulator = function() {
    this.elapsedTime = 0; // seconds
    this.distanceTraveled = 0; // meters
    this.coordinates = {
        lng: null,
        lat: null
    };
};


_.extend(xgds_kn.Simulator.prototype, {
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
        var dt = DRIVE_TIME_MULTIPLIER * (norm / hintedSpeed);

        // add in rotation estimate, we rough in 20 seconds for each waypoint.
        this.elapsedTime = this.elapsedTime + dt + ROTATION_ADDITION;

        this.coordinates = nextCoords;
    },

    executeCommand: function(command, context) {
        if (command.get('type') == 'SpiralPattern') {
            var spacing = command.get('spacing');
            var size = command.get('size');
            var overshoots = .4;
            var speed = command.get('speed');

            // new from Lorenzo
            var numLoops =  (size / spacing / 2);
            var numWptsReq = 5 + 8 * (size / 2 / spacing);
            var lastFullLeg = (2 * numLoops + 1) * spacing;
            var nominalPathLength = 2 * numLoops * (2 * numLoops + 1) * spacing + lastFullLeg + (lastFullLeg - spacing) / 2;
            var overshootsLength = (numWptsReq - 1 )/2.0 * (3.57079632679) * overshoots; 
            var totalPathLength = nominalPathLength + overshootsLength;

//            console.log("spiral length " + totalPathLength);
            var durationSeconds =  (totalPathLength / speed);
            durationSeconds = durationSeconds + (5*numWptsReq) // add 5 seconds per waypoint for transition & steering etc
            command.set('duration', durationSeconds / 60);
            this.elapsedTime = this.elapsedTime + durationSeconds;

            return;
        } else if (command.get('type') == 'RasterPattern' || command.get('type') == 'LawnmowerPattern') {
            var spacing = command.get('spacing');
            var width = command.get('width');
            var length = command.get('length');
            var overshoots = .4;
            var speed = command.get('speed');

            // new from Lorenzo
            var numRows = (length/spacing)-1;
            var numWptsReq = 3 + 4 * (length / spacing);
            var nominalPathLength = (numRows+1)*width+length;
            var overshootsLength = (numWptsReq-1)/2*((3.57079632679) * overshoots);
            var totalPathLength = nominalPathLength + overshootsLength;

//            console.log("raster length " + totalPathLength);
            var durationSeconds =  (totalPathLength / speed);
            durationSeconds = durationSeconds + (5*numWptsReq) // add 5 seconds per waypoint for transition & steering etc

            command.set('duration', durationSeconds / 60);
            this.elapsedTime = this.elapsedTime + durationSeconds;
            return;
        }
        var durationMinutes = command.get('duration');
        this.elapsedTime = this.elapsedTime + durationMinutes * 60.0;
    }
});
