// Backend address & port
var serverAddress = 'localhost';
var serverPort = '8002';

// Series to display by default
defaultSeries = ['HR', 'RR', 'BP', 'SpO2', 'CVP', 'ArtWave'];

// TODO(gus): Convert these redundant tracking objects into one a unified object.

// Holds the dom elements of instantiated graphs, keyed by series name
var graphDomElements = {};

// Holds the dom elements of instantiated legends, keyed by series name
var legendDomElements = {};

// Holds the instantiated dygraphs, keyed by series name
var dygraphInstances = {};

// Holds the initial dataset for a given data series, keyed by series name
var initialDataSeries = {}

// Holds the reference to the graph synchronization object
var sync = null;

/*
This will be a 2-dimensional array that holds the min ([0]) and max ([1])
x-value across all graphs currently displayed. This is calculated in the
convertToDateObjsAndUpdateExtremes() function. The values should hold
milliseconds since epoch, as this is the format specified for
options.dateWindow, though the values will intermediately be instances of the
Date object while the extremes are being calculated. This array may be
passed into the options.dateWindow parameter for a dygraph.
*/
var globalXExtremes = [];

var xhttp = new XMLHttpRequest();

// Creates a dygraph and adds it to the DOM
function addGraphInitialLoad(backendData, series) {

	// Create the legend dom element
	var legendDiv = document.createElement('DIV');

	// Add the dom element to the global collection for later reference
	legendDomElements[series] = legendDiv;

	// Set element to legend css class
	legendDiv.className = 'legend';

	// Attach legend to the graph div on the DOM
	document.getElementById('graphs').appendChild(legendDiv);

	// Create the graph dom element
	var graphDiv = document.createElement('DIV');

	// Add the dom element to the global collection for later reference
	graphDomElements[series] = graphDiv;

	// Set element to graph css class
	graphDiv.className = 'graph';

	// Attach new graph div to the DOM
	document.getElementById('graphs').appendChild(graphDiv);

	// Also attach the original dataset to a global object for use in deleting
	// and re-instantiating the graph upon user request.
	initialDataSeries[series] = backendData[series]

	// Instantiate the dygraph
	if (defaultSeries.includes(series)) {
		instantiateDygraph(series, backendData[series]);
	} else {
		hideGraphDivs(series);
	}

	// Add the control for the graph
	addSeriesControlToInterface(series);

}

// (Re-)instantiates a series graph after initial load.
function addGraphPostLoad(series) {

	// Show the graph & legend divs
	showGraphDivs(series);

	// Unsynchronize the graphs temporarily for the duration of the post-load addition.
	unsynchronizeGraphs();

	// Instantiate the dygraph
	instantiateDygraph(series, initialDataSeries[series]);

	// Resynchronize the graphs now that addition is complete.
	synchronizeGraphs();

	// Reset the zoom to trigger all graphs back to global range
	resetZoom();

}

// Adds a checkbox control to toggle display of the data series.
function addSeriesControlToInterface(series) {

	// Grab the controls div
	controls = document.getElementById('controls');

	// Create the checkbox DOM element
	var checkbox = document.createElement('INPUT');
	checkbox.setAttribute('type', 'checkbox');
	checkbox.setAttribute('value', series);

	// Check the box if the series is showing
	if (isGraphShowing(series)) {
		checkbox.checked = true;
	}

	// Attach the event handler that will add & remove the graph
	checkbox.onclick = function(e) {
		if (e.target.checked) {
			addGraphPostLoad(e.target.value);
		} else {
			removeGraph(e.target.value);
		}
	}

	// Attach the checkbox to the controls panel
	controls.appendChild(checkbox);

	// Create & attach the span element
	var span = document.createElement('SPAN');
	span.innerText = ' '+series;
	controls.appendChild(span);

	// Create & attach a br element
	var br = document.createElement('BR');
	controls.appendChild(br);

}

// Converts all x values in a data array to javascript Date objects.
function convertToDateObjs(data) {

	// Go through all values in the series.
	for(var i = 0; i < data.length; i++) {

		// Convert the ISO8601-format string into a Date object.
		data[i][0] = new Date(data[i][0]);

	}

}

// Converts all x values in a data array to javascript Date objects, and also
// updates the global x-axis extremes.
function convertToDateObjsAndUpdateExtremes(data) {

	// Go through all values in the series.
	for(var i = 0; i < data.length; i++) {

		// Convert the ISO8601-format string into a Date object.
		data[i][0] = new Date(data[i][0]);

		// Update global x-minimum if warranted
		if(globalXExtremes[0] == null || data[i][0] < globalXExtremes[0]) {
			globalXExtremes[0] = data[i][0]
		}

		// Update global x-maximum if warranted
		if(globalXExtremes[1] == null || data[i][0] > globalXExtremes[1]) {
			globalXExtremes[1] = data[i][0]
		}

	}

}

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
	var cnv = e.drawingContext;

	// Holds positioning & dimensions (x, y, w, h) of the plot area, needed for
	// plotting points.
	var area = e.plotArea;

	// Line properties
	cnv.strokeStyle = '#171717';//'#5253FF';
	cnv.fillStyle = '#171717';//'#5253FF';
	cnv.lineWidth = 1;

	// Plot all raw value data points
	for (var i = 0; i < e.allSeriesPoints[2].length; i++) {

		//cnv.fillRect(e.allSeriesPoints[2][i].x * area.w + area.x, e.allSeriesPoints[2][i].y * area.h + area.y, 2, 2)
		cnv.beginPath();
		cnv.arc(e.allSeriesPoints[2][i].x * area.w + area.x, e.allSeriesPoints[2][i].y * area.h + area.y, 1, 0, 2*Math.PI);
		cnv.fill();

	}

	// Plot all downsample intervals
	for (var i = 0; i < e.allSeriesPoints[0].length; i++) {

		// There may be intervals wherein min==max, and to handle these, we must use a different drawing method.
		if (e.allSeriesPoints[0][i].y == e.allSeriesPoints[1][i].y) {

			cnv.fillRect(e.allSeriesPoints[0][i].x * area.w + area.x, e.allSeriesPoints[0][i].y * area.h + area.y, 1, 1)
			/*cnv.beginPath();
			cnv.arc(e.allSeriesPoints[0][i].x * area.w + area.x, e.allSeriesPoints[0][i].y * area.h + area.y, 2, 0, 2*Math.PI);
			cnv.fill();*/

		} else {

			// Begin a path (this instantiates a path object but does not draw it
			cnv.beginPath();

			// Start stroke at the min value
			cnv.moveTo(e.allSeriesPoints[0][i].x * area.w + area.x, e.allSeriesPoints[0][i].y * area.h + area.y);

			// End stroke at the max value
			cnv.lineTo(e.allSeriesPoints[1][i].x * area.w + area.x, e.allSeriesPoints[1][i].y * area.h + area.y);

			// Draw the line on the canvas
			cnv.stroke();

		}

	}

}

// Produces a meshed dataset consisting of the outerDataset and innerDataset,
// with  innerDataset replacing its time range of data points in outerDataset.
function getDownsampleMesh(outerDataset, innerDataset) {

	// We expect non-empty arrays
	if (outerDataset.length < 1 || innerDataset.length < 1) {
		return;
	}

	// Will hold the relevant places to slice the outerDataset.
	var sliceIndexFirstSegment = 0;
	var sliceIndexSecondSegment = 0;

	// Determine outerDataset index of the data point just after innerDataset
	// starts. We will find the index just *after* the last data point before
	// innerDataset starts. However, that's okay, because sliceIndexFirstSegment
	// will be the second parameter in a slice call, which indicates an element
	// that will not be included in the resulting array.
	while (sliceIndexFirstSegment < outerDataset.length && outerDataset[sliceIndexFirstSegment][0].getTime() < innerDataset[0][0].getTime()) {
		sliceIndexFirstSegment++;
	}

	// Determine outerDataset index of the data point just after innerDataset ends.
	sliceIndexSecondSegment = sliceIndexFirstSegment;
	while (sliceIndexSecondSegment < outerDataset.length && outerDataset[sliceIndexSecondSegment][0].getTime() <= innerDataset[innerDataset.length-1][0].getTime()) {
		sliceIndexSecondSegment++;
	}

	// Return the joined dataset with the innerDataset replacing the relevant
	// section of outerDataset.
	return outerDataset.slice(0, sliceIndexFirstSegment).concat(innerDataset, outerDataset.slice(sliceIndexSecondSegment));

}

// Hide the graph & legend divs for the named series
function hideGraphDivs(series) {
	graphDomElements[series].style.display = 'none';
	legendDomElements[series].style.display = 'none';
}

// Instantiates a dygraph on the interface.
function instantiateDygraph(series, dataset) {

	// Create the dygraph
	dygraphInstances[series] = new Dygraph(graphDomElements[series], dataset.data, {
		axes: {
			x: {
				pixelsPerLabel: 70,
				independentTicks: true
			},
			y: {
				pixelsPerLabel: 14,
				independentTicks: true
			}
		},
		colors: ['#171717'],//'#5253FF'],
		dateWindow: globalXExtremes,
		//drawPoints: true,
		gridLineColor: 'rgb(232,122,128)',
		interactionModel: {
			'mousedown': handleMouseDown,
			'mousemove': handleMouseMove,
			'mouseup': handleMouseUp,
			'dblclick': handleDoubleClick,
			'mousewheel': handleMouseWheel
		},
		labels: dataset.labels,
		labelsDiv: legendDomElements[series],
		plotter: downsamplePlotter,
		/*series: {
		  'Min': { plotter: downsamplePlotter },
		  'Max': { plotter: downsamplePlotter }
		},*/
		title: series,
		underlayCallback: underlayCallbackHandler
	});

	// Attach the original dataset to the graph for later use
	dygraphInstances[series].originalDataset = dataset.data
}

// Indicate whether the named graph is currently showing on the interface.
function isGraphShowing(name) {
	return dygraphInstances.hasOwnProperty(name);
}

// Take the offset of a mouse event on the dygraph canvas and
// convert it to a percentages from the left.
function offsetToPercentage(g, offsetX) {
	// This is calculating the pixel offset of the leftmost date.
	var xOffset = g.toDomCoords(g.xAxisRange()[0], null)[0];

	// x y w and h are relative to the corner of the drawing area,
	// so that the upper corner of the drawing area is (0, 0).
	var x = offsetX - xOffset;

	// This is computing the rightmost pixel, effectively defining the width.
	var w = g.toDomCoords(g.xAxisRange()[1], null)[0] - xOffset;

	// Percentage from the left.
	var xPct = w === 0 ? 0 : (x / w);

	// The (1-) part below changes it from "% distance down from the top"
	// to "% distance up from the bottom".
	return xPct;
}

// Removes a graph from the interface
function removeGraph(series) {

	if (dygraphInstances[series] != null) {

		// Unsynchronize the graphs temporarily for the duration of the removal.
		unsynchronizeGraphs();

		// Destroy the dygraph instance
		dygraphInstances[series].destroy();

		// Delete the object key from the dygraph instances we're tracking.
		delete dygraphInstances[series]

		// Hide the graph & legend divs
		hideGraphDivs(series);

		// Resynchronize the graphs now that removal is complete.
		synchronizeGraphs()

		// Reset the zoom to trigger all graphs back to global range
		resetZoom();

	}

}

// Reset the zoom to global range
function resetZoom() {
	d = Object.keys(dygraphInstances);
	if (d.length > 0) {
		dygraphInstances[d[0]].updateOptions({
			dateWindow: globalXExtremes
		})
	}
}

// Show the graph & legend divs for the named series
function showGraphDivs(series) {
	graphDomElements[series].style.display = 'block';
	legendDomElements[series].style.display = 'block';
}

// Synchronizes the graphs for zoom and selection.
function synchronizeGraphs() {

	// Synchronize all of the graphs, if there are more than one.
	if (Object.keys(dygraphInstances).length > 1 && sync == null) {
		console.log("Synchronizing graphs.");
		sync = Dygraph.synchronize(Object.values(dygraphInstances), {
			range: false,
			selection: true,
			zoom: true
		});
	}

}

// Unsynchronizes the graphs.
function unsynchronizeGraphs() {
	if (sync != null) {

		console.log("Unsynchronizing graphs.");
		sync.detach();
		sync = null;

	}
}

// Will request and update the current view of the graph with new data that is
// appropriately downsampled (or not).
function updateCurrentViewData(graph) {

	// Get the x-axis range
	var xRange = graph.xAxisRange();

	console.log("Requesting data for view.");

	// Setup our async http call.
	var x = new XMLHttpRequest();

	// Setup our callback handler.
	x.onreadystatechange = function() {

		if (this.readyState == 4 && this.status == 200) {

			//t2 = performance.now();

			console.log("Applying data to view.");

			// Parse the backend JSON response into a JS object
			var backendData = JSON.parse(x.responseText);

			// Process the new data for each series.
			unsynchronizeGraphs();
			for(series in backendData) {

				if (isGraphShowing(series)) {

					// Convert date strings to Date objects in all datasets.
					convertToDateObjs(backendData[series]['data']);

					var meshedData = getDownsampleMesh(dygraphInstances[series].originalDataset, backendData[series]['data']);

					// Update the graph data, and redraw
					dygraphInstances[series].updateOptions({
						file: meshedData
					});

				}

			}
			synchronizeGraphs();

			// for (series in backendData) {
			//   dygraphInstances[series].updateOptions({}, false);
			//   break;
			// }

			// t3 = performance.now();
			// console.log("It took "+(t2-xt1)+"ms for the data to arrive from the backend.");
			// console.log("It took "+(t3-t2)+"ms for all client-side processing to happen.");

		}

	}

	// Send the async request
	//xt1 = performance.now();
	x.open("GET", "http://"+serverAddress+":"+serverPort+"?start="+xRange[0]+"&stop="+xRange[1], true);
	x.send();

}

// Adjusts x inward by zoomInPercentage%
// Split it so the left axis gets xBias of that change and
// right gets (1-xBias) of that change.
//
// If a bias is missing it splits it down the middle.
function zoom(g, zoomInPercentage, xBias) {
	xBias = xBias || 0.5;
	function adjustAxis(axis, zoomInPercentage, bias) {
		var delta = axis[1] - axis[0];
		var increment = delta * zoomInPercentage;
		var foo = [increment * bias, increment * (1-bias)];
		return [ axis[0] + foo[0], axis[1] - foo[1] ];
	}

	g.updateOptions({
		dateWindow: adjustAxis(g.xAxisRange(), zoomInPercentage, xBias)
	});
}

xhttp.onreadystatechange = function() {

	if (this.readyState == 4 && this.status == 200) {

		//t2 = performance.now();

		// Parse the backend JSON response into a JS object
		var backendData = JSON.parse(xhttp.responseText);

		// Convert date strings to Date objects in all datasets and produce global
		// x-axis extremes. It is an obvious potential optimization to combine this
		// for loop and the subsequent one, but don't. Global x-axis extremes from
		// all datasets must be calculated before any graph is plotted so that the
		// default zoom can be set. There won't be that many graphs, so redundant
		// for loops are not costly.
		for(series in backendData) {
			convertToDateObjsAndUpdateExtremes(backendData[series]['data']);
		}

		// When the x-axis extremes have been calculated (as dates), convert them
		// to milliseconds since epoch, as this is what is specified in the options
		// reference: http://dygraphs.com/options.html#dateWindow
		globalXExtremes[0] = globalXExtremes[0].valueOf();
		globalXExtremes[1] = globalXExtremes[1].valueOf();

		// Create a graph for each series if it is in the default series array
		for(series in backendData) {
			addGraphInitialLoad(backendData, series);
		}

		// Synchronize the graphs
		synchronizeGraphs();

		// t3 = performance.now();
		// console.log("It took "+(t2-xhttpt1)+"ms for the data to arrive from the backend.");
		// console.log("It took "+(t3-t2)+"ms for all client-side processing to happen.");

	}

};
//xhttpt1 = performance.now();

