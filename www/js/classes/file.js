

function File(filename) {

	// Holds graph object instances pertaining to the file.
	this.graphs = {};

	// Holds data for all graphs
	this.graphData = {};

	// Holds the dom elements of instantiated graphs, keyed by series name
	this.graphDomElements = {};

	// Holds the dom elements of instantiated legends, keyed by series name
	this.legendDomElements = {};

	// Holds the instantiated dygraphs, keyed by series name
	this.dygraphInstances = {};

	// Holds the initial dataset for a given data series, keyed by series name
	this.initialDataSeries = {};

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

	requestHandler.requestAllSeriesAllData(filename, function(data) {

		// Attach graph data
		this.graphData = data;

		// Convert date strings to Date objects in all datasets and produce global
		// x-axis extremes. It is an obvious potential optimization to combine this
		// for loop and the subsequent one, but don't. Global x-axis extremes from
		// all datasets must be calculated before any graph is plotted so that the
		// default zoom can be set. There won't be that many graphs, so redundant
		// for loops are not costly.
		for (var series in data) {
			processData(data[series]['data'], true);
		}

		// When the x-axis extremes have been calculated (as dates), convert them
		// to milliseconds since epoch, as this is what is specified in the options
		// reference: http://dygraphs.com/options.html#dateWindow
		this.globalXExtremes[0] = this.globalXExtremes[0].valueOf();
		this.globalXExtremes[1] = this.globalXExtremes[1].valueOf();

		// Create a graph for each series if it is in the default series array
		for(series in data) {
			addGraphInitialLoad(data, series);
		}

		// Synchronize the graphs
		synchronizeGraphs();

	});

}

File.prototype.destroy = function() {

	// Destroy graph synchronization state management
	unsynchronizeGraphs();

	// Destroy all dygraph instances
	for (var i in dygraphInstances) {
		dygraphInstances[i].destroy();
	}

	// Clear relevant DOM tree portions
	document.getElementById('graphs').innerText = '';
	document.getElementById('series_toggle_controls').innerText = '';

	// Clear state management data
	this.graphs = {};
	this.graphDomElements = {};
	this.legendDomElements = {};
	this.dygraphInstances = {};
	this.initialDataSeries = {};
	this.globalXExtremes = [];

}

File.prototype.processAllSeriesData = function() {



}