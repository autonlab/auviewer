'use strict';

/*
  Hard-coding some project configuration for now which we will move into db or
  config files later.
*/
let bpRange = [0, 250];
let pulseRange = [0, 200];
let spo2Range = [30, 100];
let moveToConfig = {

	groups: [
		['numerics/AR1-D/data', 'numerics/AR1-S/data', 'numerics/AR1-M/data'],
		['numerics/ART.Diastolic/data', 'numerics/ART.Systolic/data', 'numerics/ART.Mean/data'],
		['numerics/NBP.NBPd/data', 'numerics/NBP.NBPm/data', 'numerics/NBP.NBPs/data']
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

// Attach event handlers to the annotation modal
$('#annotationModal button.btn-primary').click(function() {
	$('#annotationModal').data('callingAnnotation').finalize();
});
$('#annotationModal button.btn-secondary').click(function() {
	if ($('#annotationModal').data('state') == 'create') {
		$('#annotationModal').data('callingAnnotation').cancel();
	} else if($('#annotationModal').data('state') == 'edit') {
		// TODO(gus): Implement deletion
		// $('#annotationModal').data('callingAnnotation').delete();
		$('#annotationModal').data('callingAnnotation').hideDialog();
	}
});

// Request the list of files for the project
requestHandler.requestFileList(function(data) {

    	let fileSelect = document.getElementById('file_selection');

		for (let i in data) {

			let opt = document.createElement('OPTION');
			opt.setAttribute('value', data[i]);
			opt.innerText = data[i];
			fileSelect.appendChild(opt);

		}

	});
