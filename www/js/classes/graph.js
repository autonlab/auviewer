'use strict';

function Graph(series, file) {

	// References the parent File instance
	this.file = file;

	// Holds the series name of the graph
	this.series = series;

	// Holds the dom element of the instantiated legend
	this.legendDomElement = null;

	// Holds the dom element of the instantiated graph
	this.graphDomElement = null;

	// Holds the dygraph instance
	this.dygraphInstance = null;

	// Build the graph
	this.build();

}

Graph.prototype.build = function() {

	// Create the legend dom element
	let legendDiv = document.createElement('DIV');

	// Add the dom element to the object for later reference
	this.legendDomElement = legendDiv;

	// Set element to legend css class
	legendDiv.className = 'legend';

	// Attach legend to the graph div on the DOM
	document.getElementById('graphs').appendChild(legendDiv);

	// Create the graph dom element
	let graphDiv = document.createElement('DIV');

	// Add the dom element to the object for later reference
	this.graphDomElement = graphDiv;

	// Set element to graph css class
	graphDiv.className = 'graph';

	// Attach new graph div to the DOM
	document.getElementById('graphs').appendChild(graphDiv);

	// Instantiate the dygraph
	if (config.defaultSeries.includes(this.series)) {
		this.instantiateDygraph();
	} else {
		this.hideDOMElements();
	}

	// Add the control for the graph
	this.file.graphSelectionMenu.add(this.series);

};

// Handle double-click for restoring the original zoom.
Graph.prototype.handleDoubleClick = function(event, g, context) {
	g.updateOptions({
		dateWindow: this.file.globalXExtremes
	});
};

// Handle mouse-down for pan & zoom
Graph.prototype.handleMouseDown = function(event, g, context) {

	context.initializeMouseDown(event, g, context);

	if (event.altKey) {
		startAnnotationHighlight(event, g, context);
	}
	else if (event.shiftKey) {
		Dygraph.startZoom(event, g, context);
	} else {
		context.medViewPanningMouseMoved = false;
		Dygraph.startPan(event, g, context);
	}

};

// Handle mouse-move for pan & zoom.
Graph.prototype.handleMouseMove = function(event, g, context) {

	if (context.mvIsAnnotating) {
		moveAnnotationHighlight(event, g, context);
	}
	else if (context.isZooming) {
		Dygraph.moveZoom(event, g, context);
	}
	else if (context.isPanning) {
		context.medViewPanningMouseMoved = true;
		Dygraph.movePan(event, g, context);
	}

};

// Handle mouse-up for pan & zoom.
Graph.prototype.handleMouseUp = function(event, g, context) {

	if (context.mvIsAnnotating) {
		endAnnotationHighlight(event, g, context);
	}
	else if (context.isZooming) {
		Dygraph.endZoom(event, g, context);
		this.file.updateCurrentViewData();
	}
	else if (context.isPanning) {
		if (context.medViewPanningMouseMoved) {
			this.file.updateCurrentViewData();
			context.medViewPanningMouseMoved = false;
		}
		Dygraph.endPan(event, g, context);
	}

};

// Handle shift+scroll or alt+scroll for zoom.
Graph.prototype.handleMouseWheel = function(event, g, context) {

	// We allow the user to use either alt or shift plus the mousewheel to zoom.
	// We also allow the user to use pinch-to-zoom; the event.ctrlKey is true
	// when the user is using pinch-to-zoom gesture.
	if (event.ctrlKey || event.altKey || event.shiftKey) {

		let normal = event.detail ? event.detail * -1 : event.wheelDelta / 40;
		// For me the normalized value shows 0.075 for one click. If I took
		// that verbatim, it would be a 7.5%.
		let percentage = normal / 50;

		if (!(event.offsetX)){
			event.offsetX = event.layerX - event.target.offsetLeft;
		}

		let xPct = this.offsetToPercentage(g, event.offsetX);

		this.zoom(g, percentage, xPct);

		// Persist for timeout callback
		let graph = this;

		// If we're zooming with the mouse-wheel or with pinch-to-zoom, we want
		// to set a timeout to update the current view's data. This is to prevent
		// repeated, overlapping calls in the midst of zooming.
		if (g.updateDataTimer != null) {
			clearTimeout(g.updateDataTimer);
		}
		g.updateDataTimer = setTimeout(function(){ g.updateDataTimer = null; graph.file.updateCurrentViewData(); }, 200);


		//updateCurrentViewData(g);
		event.preventDefault();

	}

};

// Hide the graph & legend divs
Graph.prototype.hideDOMElements = function() {

	this.graphDomElement.style.display = 'none';
	this.legendDomElement.style.display = 'none';

};

// Instantiates a dygraph on the UI
Graph.prototype.instantiateDygraph = function() {

	// Determine if there is already a graph showing. If so, adopt its x-range.
	// If not, use global x extremes.
	let timeWindow = this.file.globalXExtremes;
	for (let s of Object.keys(this.file.graphs)) {
		if (this.file.graphs[s].dygraphInstance !== null) {
			timeWindow = this.file.graphs[s].dygraphInstance.xAxisRange();
			break;
		}
	}

	// Create the dygraph
	this.dygraphInstance = new Dygraph(this.graphDomElement, this.file.graphData[this.series].data, {
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
		dateWindow: timeWindow,
		//drawPoints: true,
		gridLineColor: 'rgb(232,122,128)',
		interactionModel: {
			'mousedown': this.handleMouseDown.bind(this),
			'mousemove': this.handleMouseMove.bind(this),
			'mouseup': this.handleMouseUp.bind(this),
			'dblclick': this.handleDoubleClick.bind(this),
			'mousewheel': this.handleMouseWheel.bind(this)
		},
		labels: this.file.graphData[this.series].labels,
		labelsDiv: this.legendDomElement,
		plotter: downsamplePlotter,
		/*series: {
		  'Min': { plotter: downsamplePlotter },
		  'Max': { plotter: downsamplePlotter }
		},*/
		title: this.series,
		underlayCallback: underlayCallbackHandler
	});

};

// Meshes a provided subset of data (e.g. higher resolution data for a subset
// x-axis range) with the outer, original data, and triggers a graph refresh.
Graph.prototype.meshData = function(data) {

	// This is only necessary for graphs which are currently showing
	if (this.dygraphInstance === null) {
		return;
	}

	// We expect non-empty arrays
	if (this.file.graphData[this.series].data.length < 1 || typeof data === 'undefined' || data.length < 1) {
		return;
	}

	// Will hold the relevant places to slice the outerDataset.
	let sliceIndexFirstSegment = 0;
	let sliceIndexSecondSegment = 0;

	// Determine outerDataset index of the data point just after innerDataset
	// starts. We will find the index just *after* the last data point before
	// innerDataset starts. However, that's okay, because sliceIndexFirstSegment
	// will be the second parameter in a slice call, which indicates an element
	// that will not be included in the resulting array.
	// TODO(gus): Convert this to binary search.
	while (sliceIndexFirstSegment < this.file.graphData[this.series].data.length && this.file.graphData[this.series].data[sliceIndexFirstSegment][0] < data[0][0]) {
		sliceIndexFirstSegment++;
	}

	// Determine outerDataset index of the data point just after innerDataset ends.
	sliceIndexSecondSegment = sliceIndexFirstSegment;
	while (sliceIndexSecondSegment < this.file.graphData[this.series].data.length && this.file.graphData[this.series].data[sliceIndexSecondSegment][0] <= data[data.length-1][0]) {
		sliceIndexSecondSegment++;
	}

	// Return the joined dataset with the innerDataset replacing the relevant
	// section of outerDataset.
	let meshedData = this.file.graphData[this.series].data.slice(0, sliceIndexFirstSegment).concat(data, this.file.graphData[this.series].data.slice(sliceIndexSecondSegment));

	// Update the graph data, and redraw
	this.dygraphInstance.updateOptions({
		file: meshedData
	});

};

// Take the offset of a mouse event on the dygraph canvas and
// convert it to a percentages from the left.
Graph.prototype.offsetToPercentage = function(g, offsetX) {
	// This is calculating the pixel offset of the leftmost date.
	let xOffset = g.toDomCoords(g.xAxisRange()[0], null)[0];

	// x y w and h are relative to the corner of the drawing area,
	// so that the upper corner of the drawing area is (0, 0).
	let x = offsetX - xOffset;

	// This is computing the rightmost pixel, effectively defining the width.
	let w = g.toDomCoords(g.xAxisRange()[1], null)[0] - xOffset;

	// Percentage from the left.
	// The (1-) part below changes it from "% distance down from the top"
	// to "% distance up from the bottom".
	return w === 0 ? 0 : (x / w);
};

// Remove the graph from the interface.
Graph.prototype.remove = function() {

	// Unsynchronize the graphs temporarily for the duration of the removal.
	this.file.unsynchronizeGraphs();

	// Destroy the dygraph instance
	this.dygraphInstance.destroy();

	// Delete the dygraph instance reference
	this.dygraphInstance = null;

	// Hide the graph & legend divs
	this.hideDOMElements();

	// Resynchronize the graphs now that removal is complete.
	this.file.synchronizeGraphs()

};

// Show the graph on the interface.
Graph.prototype.show = function() {

	// Unsynchronize the graphs temporarily for the duration of the post-load addition.
	this.file.unsynchronizeGraphs();

	// Show the graph & legend divs
	this.showDOMElements();

	// Instantiate the dygraph
	this.instantiateDygraph();

	// Resynchronize the graphs now that the addition is complete.
	this.file.synchronizeGraphs();

	// Update the data from the backend for the new series only
	this.updateCurrentViewData()

};

// Show the graph & legend divs for the named series.
Graph.prototype.showDOMElements = function() {

	this.graphDomElement.style.display = 'block';
	this.legendDomElement.style.display = 'block';

};

// Request and update data for the current view of the graph.
// NOTE: There is an identically-named function on both File and Graph classes.
Graph.prototype.updateCurrentViewData = function() {

	// Get the x-axis range
	let xRange = this.dygraphInstance.xAxisRange();

	// Persist for callback
	let graph = this;

	requestHandler.requestSingleSeriesRangedData(this.file.filename, this.series, xRange[0], xRange[1], function(data) {

		// Validate the response data
		if (typeof data === 'undefined' || !data || !data.hasOwnProperty(graph.series) || !data[graph.series].hasOwnProperty('data') || !data[graph.series].hasOwnProperty('labels')) {
			console.log('Invalid response received.');
			return;
		}

		// Temporarily unsynchronize the graphs
		graph.file.unsynchronizeGraphs();

		// Pad the returned data if necessary
		graph.file.padDataIfNeeded(data[graph.series].data);
		
		// Mesh the updated current view data
		graph.meshData(data[graph.series].data);
		
		// Resynchronize the graphs
		graph.file.synchronizeGraphs();

	});

};

// Adjusts x inward by zoomInPercentage%
// Split it so the left axis gets xBias of that change and
// right gets (1-xBias) of that change.
//
// If a bias is missing it splits it down the middle.
Graph.prototype.zoom = function(g, zoomInPercentage, xBias) {
	xBias = xBias || 0.5;
	let axis = g.xAxisRange();
	let delta = axis[1] - axis[0];
	let increment = delta * zoomInPercentage;
	let foo = [increment * xBias, increment * (1-xBias)];
	g.updateOptions({
		dateWindow: [ axis[0] + foo[0], axis[1] - foo[1] ]
	});
};