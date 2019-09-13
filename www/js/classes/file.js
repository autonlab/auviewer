'use strict';

function File(filename) {

	// Holds the filelname
	this.filename = filename;

	// Holds graph object instances pertaining to the file.
	this.graphs = {};

	// Holds data for all graphs, keyed by series name
	this.graphData = {};

	// Holds the reference to the graph synchronization object
	this.sync = null;

	/*
	Holds the min [0] and max [1] x-value across all graphs currently displayed.
	This is calculated in the convertToDateObjsAndUpdateExtremes() function. The
	values should hold milliseconds since epoch, as this is the format specified
	for options.dateWindow, though the values will intermediately be instances
	of the Date object while the extremes are being calculated. This array may
	be passed into the options.dateWindow parameter for a dygraph.
	*/
	this.globalXExtremes = [];

	// Holds an instance of the graph selection menu object for this file
	this.graphSelectionMenu = new GraphSelectionMenu(this);

	// Persist for callback
	let file = this;

	requestHandler.requestAllSeriesAllData(this.filename, function(data) {

		// Attach graph data
		file.graphData = data;

		// Calculate x-axis extremes across all data series
		file.calculateExtremes();

		// Pad data, if necessary, for each series
		for (let s of Object.keys(file.graphData.series)) {
			file.padDataIfNeeded(file.graphData.series[s].data);
		}

		// Instantiate each graph
		for (let s of Object.keys(file.graphData.series)) {
			file.graphs[s] = new Graph(s, file);
		}

		// Synchronize the graphs
		file.synchronizeGraphs();

		// Populate the alert generation dropdown
		let alertGenSeriesDropdown = document.getElementById('alert_gen_series_field');
		for (let i = 0; i < alertGenSeriesDropdown.length; i++) {
			alertGenSeriesDropdown.remove(i);
		}
		let opt = document.createElement('option');
		alertGenSeriesDropdown.add(opt);
		for (let s of Object.keys(file.graphData.series)) {
			let opt = document.createElement('option');
			opt.text = s;
			opt.value = s;
			alertGenSeriesDropdown.add(opt);
		}

		// Populate the annotations
		for (let ann of file.graphData.annotations) {
			annotations.push(new Annotation(ann[0], ann[1], ann[6]));
		}
		globalStateManager.currentFile.triggerRedraw();

	});

}

// Calculate x-axis extremes across all data series.
File.prototype.calculateExtremes = function() {

	// Get array of series
	let series = Object.keys(this.graphData.series);

	// If there are no series, return
	if (series.length < 1) {
		return;
	}

	// Prime the graph extremes with the first series, first point
	this.globalXExtremes[0] = this.graphData.series[series[0]].data[0][0];
	this.globalXExtremes[1] = this.graphData.series[series[0]].data[0][0];

	for (let s of series) {

		// If this series has no data, continue
		if (this.graphData.series[s].data.length < 1) {
			continue;
		}

		for (let i in this.graphData.series[s].data) {

			// Update global x-minimum if warranted
			if (this.graphData.series[s].data[i][0] < this.globalXExtremes[0]) {
				this.globalXExtremes[0] = this.graphData.series[s].data[i][0];
			}

			// Update global x-maximumm if warranted
			if (this.graphData.series[s].data[i][0] > this.globalXExtremes[1]) {
				this.globalXExtremes[1] = this.graphData.series[s].data[i][0];
			}

		}

	}

	// When the x-axis extremes have been calculated (as dates), convert them
	// to milliseconds since epoch, as this is what is specified in the options
	// reference: http://dygraphs.com/options.html#dateWindow
	// this.globalXExtremes[0] = this.globalXExtremes[0].valueOf();
	// this.globalXExtremes[1] = this.globalXExtremes[1].valueOf();

};

File.prototype.destroy = function() {

	// Destroy graph synchronization state management
	this.unsynchronizeGraphs();

	// Remove each graph
	for (let s of Object.keys(this.graphs)) {
		this.graphs[s].remove();
	}

	// Clear relevant DOM tree portions
	document.getElementById('graphs').innerText = '';
	document.getElementById('series_toggle_controls').innerText = '';

	// Clear state management data
	this.graphs = {};
	this.graphData = {};
	this.globalXExtremes = [];

};

// Pads a set of data points, if necessary, with null value at end of each data
// point array for downsample sets.
// TODO(gus): Remove later; this is temporary.
File.prototype.padDataIfNeeded = function(data) {

	// Return if there are no data points
	if (typeof data === 'undefined' || data.length < 1) {
		return;
	}

	// Return if padding is not necessary
	if (data[0].length !== 3) {
		return;
	}

	for (let i in data) {
		data[i].push(null);
	}

};

// Synchronize the graphs for zoom and selection.
File.prototype.synchronizeGraphs = function() {

	// If sync is not null, return now.
	if (this.sync != null) {
		return;
	}

	// Build an array of the dygraph instances
	let dygraphInstances = [];
	for (let s of Object.keys(this.graphs)) {
		if (this.graphs[s].dygraphInstance !== null) {
			dygraphInstances.push(this.graphs[s].dygraphInstance);
		}
	}

	// If there is not more than one graph showing to synchronize, return now.
	if (dygraphInstances.length < 2) {
		return;
	}

	// Synchronize all of the graphs, if there are more than one.
	console.log("Synchronizing graphs.");
	this.sync = Dygraph.synchronize(dygraphInstances, {
		range: false,
		selection: true,
		zoom: true
	});

};

// Trigger the dygraphs to redraw. This function relies on the fact that the
// dygraphs are synchronized, and therefore triggering one to redraw will
// trigger them all to do so.
File.prototype.triggerRedraw = function() {

	for (let s of Object.keys(this.graphs)) {
		if (this.graphs[s].dygraphInstance !== null) {
			this.graphs[s].dygraphInstance.updateOptions({});

			// We only need to trigger one to redraw (see function description).
			break;
		}
	}

};

// Request and update data for the current view of all graphs for current file.
// NOTE: There is an identically-named function on both File and Graph classes.
File.prototype.updateCurrentViewData = function() {

	// Find the first graph which is currently displaying
	let dg = null;
	for (let k of Object.keys(this.graphs)) {
		if (this.graphs[k].dygraphInstance !== null) {
			dg = this.graphs[k].dygraphInstance;
			break;
		}
	}

	// Return if no visible graph was found
	if (dg === null) {
		return;
	}

	// Get the x-axis range from the first graph (all graphs should be showing
	// the same range since they are synchronized).
	let xRange = dg.xAxisRange();

	// Persist for callback
	let file = this;

	requestHandler.requestAllSeriesRangedData(this.filename, xRange[0], xRange[1], function(data) {

		// Temporarily unsynchronize the graphs
		file.unsynchronizeGraphs();

		// For each data series, pad the returned data if necessary and then
		// mesh the data into the existing graph.
		for (let s of Object.keys(data.series)) {

			// Pad the data if necessary
			file.padDataIfNeeded(data.series[s].data);

			// We do this in a try block because it's theoretically possible
			// that the backend returns a data series we don't have a graph
			// object for (in other words, a data series it didn't return in
			// the original on-load request for all data series.
			try {
				file.graphs[s].meshData(data.series[s].data);
			}
			catch (error) {
				console.log("Could not find an existing graph object for a data series returned by the backend for all series ranged data.", error);
			}
		}

		// Resynchronize the graphs
		file.synchronizeGraphs();

	});

};

// Unsynchroniz the graphs.
File.prototype.unsynchronizeGraphs = function() {

	if (this.sync != null) {

		console.log("Unsynchronizing graphs.");
		this.sync.detach();
		this.sync = null;

	}

};