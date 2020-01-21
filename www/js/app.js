'use strict';

/*
  Hard-coding some project configuration for now which we will move into db or
  config files later.
*/
let bpRange = [0, 250];
let pulseRange = [0, 200];
let spo2Range = [30, 100];
let moveToConfig = {

	anomalyDetection: [
		{
			series: 'numerics/HR/data',
			tlow: 58,
			thigh: 110,
			dur: 10,
			duty: 70,
			maxgap: 1800
		},
		{
			series: 'numerics/HR.HR/data',
			tlow: 58,
			thigh: 110,
			dur: 10,
			duty: 70,
			maxgap: 1800
		},
		{
			series: 'numerics/rRR/data',
			tlow: 10,
			thigh: 29,
			dur: 300,
			duty: 70,
			maxgap: 300
		},
		{
			series: 'numerics/RR.RR/data',
			tlow: 10,
			thigh: 29,
			dur: 300,
			duty: 70,
			maxgap: 300
		},
		{
			series: 'numerics/NBP-S/data',
			tlow: 90,
			thigh: 165,
			dur: 300,
			duty: 70,
			maxgap: 300
		},
		{
			series: 'numerics/NBP-M/data',
			tlow: 65,
			dur: 300,
			duty: 70,
			maxgap: 300
		},
		{
			series: 'numerics/SPO2-%/data',
			tlow: 90,
			dur: 300,
			duty: 70,
			maxgap: 300
		},
		{
			series: 'numerics/SpO₂.SpO₂/data',
			tlow: 90,
			dur: 300,
			duty: 70,
			maxgap: 300
		},
		{
			series: 'numerics/SpO₂T.SpO₂T/data',
			tlow: 90,
			dur: 300,
			duty: 70,
			maxgap: 300
		}
	],

	// Series to display by default
	defaultSeries: ['numerics/HR/data', 'numerics/HR.HR/data', 'numerics/HR.BeatToBeat/data', 'numerics/ART.Systolic/data', 'numerics/ART.Diastolic/data', 'numerics/SpO₂.SpO₂/data', 'numerics/SpO₂T.SpO₂T/data', 'numerics/SPO2-%/data', 'CVP/data', 'ArtWave/data'],

	groups: [
		['numerics/AR1-D/data', 'numerics/AR1-S/data', 'numerics/AR1-M/data'],
		['numerics/ART.Diastolic/data', 'numerics/ART.Systolic/data', 'numerics/ART.Mean/data'],
		['numerics/NBP.NBPd/data', 'numerics/NBP.NBPm/data', 'numerics/NBP.NBPs/data'],
		['numerics/NBP-D/data', 'numerics/NBP-M/data', 'numerics/NBP-S/data']
	],

	ranges: {
		'numerics/AR1-D/data': bpRange,
		'numerics/AR1-M/data': bpRange,
		'numerics/AR1-S/data': bpRange,
		'numerics/ART.Diastolic/data': bpRange,
		'numerics/ART.Mean/data': bpRange,
		'numerics/ART.Pulse/data': pulseRange,
		'numerics/ART.Systolic/data': bpRange,
		'numerics/NBP.NBPd/data': bpRange,
		'numerics/NBP.NBPm/data': bpRange,
		'numerics/NBP.NBPs/data': bpRange,
		'numerics/NBP.Pulse/data': pulseRange,
		'numerics/RR.RR/data': [0, 50],
		'numerics/SpO₂.Pulse/data': pulseRange,
		'numerics/SpO₂.SpO₂/data': spo2Range,
		'numerics/SpO₂T.SpO₂T/data': spo2Range,
		'numerics/SPO2-%/data': spo2Range
	}

};

// TODO(gus): This needs to be moved somewhere.
// This function is a plotter that plugs into dygraphs in order to plot a down-
// sampled data series. Plotting is not documented, so the best reference for
// plotting with dygraphs is to review http://dygraphs.com/tests/plotters.html
// and its source code.
function downsamplePlotter(e) {

	/*// We only want to run the plotter for the first series.
	if (e.seriesIndex !== 1) return;

	// We require two series for min & max.
	if (e.seriesCount != 3) {
	  throw "The medview plotter expects three y-values per series for downsample min, downsample max, and real value.";
	}*/

	// This is the official dygraphs way to plot all the series at once, per
	// source code of dygraphs.com/tests/plotters.html.
	if (e.seriesIndex !== 0) {
		return
	}

	// This is a reference to a proxy for the canvas element of the graph
	let cnv = e.drawingContext;

	// Holds positioning & dimensions (x, y, w, h) of the plot area, needed for
	// plotting points.
	let area = e.plotArea;

	// Line properties
	cnv.strokeStyle = '#171717';//'#5253FF';
	cnv.fillStyle = '#171717';//'#5253FF';
	cnv.lineWidth = 1;

	// Plot each series, whether it be an individual series or a group of them.
	//console.log(e.allSeriesPoints);
	for (let i = 0; i + 2 < e.allSeriesPoints.length; i += 3) {
		
		// Plot the raw data column for the series, which will be the third
		// column of this series' set of three columns.
		for (let j = 0; j < e.allSeriesPoints[i+2].length; j++) {

			//cnv.fillRect(e.allSeriesPoints[i+2][j].x * area.w + area.x, e.allSeriesPoints[i+2][j].y * area.h + area.y, 2, 2)
			cnv.beginPath();
			cnv.arc(e.allSeriesPoints[i+2][j].x * area.w + area.x, e.allSeriesPoints[i+2][j].y * area.h + area.y, 1, 0, 2 * Math.PI);
			cnv.fill();

		}
		
		// Plot the downsample min & max columns for the series, which will be
		// the first & second columns of this series' set of three columns.
		for (let j = 0; j < e.allSeriesPoints[i].length; j++) {

			// There may be intervals wherein min==max, and to handle these, we must use a different drawing method.
			if (!e.allSeriesPoints[i+1][j]) {
				// console.log(i, j, e.allSeriesPoints.length, e.allSeriesPoints[i].length);
				// console.log(e.allSeriesPoints[i][j]);
				// console.log(e.allSeriesPoints[i+1][j]);
				// console.log(e.allSeriesPoints);
			}
			if (e.allSeriesPoints[i][j].y === e.allSeriesPoints[i+1][j].y) {

				cnv.fillRect(e.allSeriesPoints[i][j].x * area.w + area.x, e.allSeriesPoints[i][j].y * area.h + area.y, 1, 1)
				/*cnv.beginPath();
				cnv.arc(e.allSeriesPoints[i][j].x * area.w + area.x, e.allSeriesPoints[i][j].y * area.h + area.y, 2, 0, 2*Math.PI);
				cnv.fill();*/

			} else {

				// Begin a path (this instantiates a path object but does not draw it
				cnv.beginPath();

				// Start stroke at the min value
				cnv.moveTo(e.allSeriesPoints[i][j].x * area.w + area.x, e.allSeriesPoints[i][j].y * area.h + area.y);

				// End stroke at the max value
				cnv.lineTo(e.allSeriesPoints[i+1][j].x * area.w + area.x, e.allSeriesPoints[i+1][j].y * area.h + area.y);

				// Draw the line on the canvas
				cnv.stroke();

			}

		}
		
	}

}

let requestHandler = new RequestHandler();
let globalStateManager = new GlobalStateManager();

// Setup the websocket connection
let socket = io();
socket.on('connect', function() {
    console.log('Connected to realtime connection.')
});

socket.on('new_data', function(data) {

	// Log the received data
	vo('rcvd socketio new_data:', deepCopy(data));

	// Grab the current file
	let currentFile = globalStateManager.currentFile;

	// If we're not in realtime mode, we cannot process incoming realtime data.
	if (!currentFile || !(currentFile.projname === '__realtime__' && currentFile.filename === '__realtime__')) {
		console.log('Received new realtime data, but not in realtime mode. Ignoring.');
		return;
	}

	// Add the new data
	//currentFile.getPostloadDataUpdateHandler()(data);
	currentFile.newDataQueue.push(data);

	// Kick-off continuous render mode if we're not already in it.
	if (!currentFile.continuousRender) {
		currentFile.processNewRealtimeData();
	}

});

// Attach event handlers to the annotation modal
$('#annotationModal button.saveButton').click(function() {
	$('#annotationModal').data('callingAnnotation').save();
});
$('#annotationModal button.cancelButton').click(function() {
	$('#annotationModal').data('callingAnnotation').cancel();
});
$('#annotationModal button.deleteButton').click(function() {
	if (confirm("Are you sure you want to delete this annotation?")) {
		$('#annotationModal').data('callingAnnotation').delete();
	}
});

// Request the list of files for the project
requestHandler.requestProjectsList(function(data) {

	let projectSelect = document.getElementById('project_selection');

	for (let i in data) {

		let opt = document.createElement('OPTION');
		opt.setAttribute('value', data[i]);
		opt.innerText = data[i];
		projectSelect.appendChild(opt);

	}

});
