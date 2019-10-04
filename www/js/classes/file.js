'use strict';

function File(filename) {

	// Holds the filelname
	this.filename = filename;

	// Holds graph object instances pertaining to the file.
	this.graphs = {};

	// Holds the initial payload data for the file
	this.fileData = {};

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

	// Request the initial file payload, and handle the response when it comes.
	requestHandler.requestInitialFilePayload(this.filename, function(data) {

		// Attach graph data
		file.fileData = data;

		// Calculate x-axis extremes across all data series
		file.calculateExtremes();

		// Pad data, if necessary, for each series
		for (let s of Object.keys(file.fileData.series)) {
			padDataIfNeeded(file.fileData.series[s].data);
		}











		/*** BEGIN HARD-CODED PROJECT CONIG ***/
		/*
			Hard-coding some project configuration for now which we will move
			into db or config files later.
		 */

		let groups = [
			['numerics/AR1-D/data', 'numerics/AR1-S/data', 'numerics/AR1-M/data'],
			['numerics/ART.Diastolic/data', 'numerics/ART.Systolic/data', 'numerics/ART.Mean/data'],
			['numerics/NBP.NBPd/data', 'numerics/NBP.NBPm/data', 'numerics/NBP.NBPs/data']
		];

		// Let's create a collated data set for each group.
		// NOTE: If you're trying to understand this code in the future, I'm
		// sorry. I could not document this in any way that would help make it
		// more understandable, and it is a bit of a labyrinth.
		groupLoop:
		for (let group of groups) {

			// Check whether all series members of the group are present, and if
			// not, then skip this group.
			for (let s of group) {
				if (!file.fileData.series.hasOwnProperty(s)) {
					continue groupLoop;
				}
			}

			// Enumerate the column labels
			const labels = ['time'];
			for (let s of group) {
				labels.push(s + ' Min');
				labels.push(s + ' Max');
				labels.push(s);
			}

			// Add the combined series to the file data.
			file.fileData.series["Group:\n" + group.join("\n")] = {
				id: "Group:\n" + group.join("\n"),
				labels: labels,
				group: group,
				data: createMergedTimeSeries(group, file.fileData.series)
			};

		}

		/*** END HARD-CODED PROJECT CONIG ***/
















		// Instantiate each graph
		for (let s of Object.keys(file.fileData.series)) {
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
		for (let s of Object.keys(file.fileData.series)) {
			let opt = document.createElement('option');
			opt.text = s;
			opt.value = s;
			alertGenSeriesDropdown.add(opt);
		}

		// Populate the annotations
		for (let ann of file.fileData.annotations) {
			annotations.push(new Annotation(ann[0], ann[1], ann[6]));
		}
		globalStateManager.currentFile.triggerRedraw();

	});

}

// Calculate x-axis extremes across all data series.
File.prototype.calculateExtremes = function() {

	// Get array of series
	let series = Object.keys(this.fileData.series);

	// If there are no series, return
	if (series.length < 1) {
		return;
	}

	// Prime the graph extremes with the first series, first point
	this.globalXExtremes[0] = this.fileData.series[series[0]].data[0][0];
	this.globalXExtremes[1] = this.fileData.series[series[0]].data[0][0];

	for (let s of series) {

		// If this series has no data, continue
		if (this.fileData.series[s].data.length < 1) {
			continue;
		}

		for (let i in this.fileData.series[s].data) {

			// Update global x-minimum if warranted
			if (this.fileData.series[s].data[i][0] < this.globalXExtremes[0]) {
				this.globalXExtremes[0] = this.fileData.series[s].data[i][0];
			}

			// Update global x-maximumm if warranted
			if (this.fileData.series[s].data[i][0] > this.globalXExtremes[1]) {
				this.globalXExtremes[1] = this.fileData.series[s].data[i][0];
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
	this.fileData = {};
	this.globalXExtremes = [];

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

	console.log("FILE updateCurrentViewData called.");

	// Holds the array of series IDs for which we will request updated data.
	let series = [];

	// Will hold the last graph we found that is showing on the UI, for purposes
	// of grabbing the x-axis range.
	let lastGraphShowing = null;

	// Build array of series to request updated data for, including both
	// individual and group series.
	for (let g in this.graphs) {

		// We're only adding the series of graphs currently showing.
		if (this.graphs[g].isShowing()) {

			lastGraphShowing = this.graphs[g];

			if (this.graphs[g].isGroup) {

				for (let s of this.graphs[g].group) {
					if (series.indexOf(s) === -1) {
						series.push(s);
					}
				}

			} else if (series.indexOf(g) === -1) {

				series.push(this.graphs[g].series);

			}

		}

	}

	// Return if no visible graph was found
	if (series.length === 0) {
		return;
	}

	// Grab the x-axis range from the last showing graph (all graphs should be
	// showing the same range since they are synchronized).
	let xRange = lastGraphShowing.dygraphInstance.xAxisRange();

	// Persist for callback
	let file = this;

	requestHandler.requestMultiSeriesRangedData(this.filename, series, xRange[0], xRange[1], function(data) {
		// Validate the response data
		if (typeof data === 'undefined' || !data || !data.hasOwnProperty('series')) {
			console.log('Invalid response received.');
			return;
		}

		// Go through all series received in the response, and pad if necessary.
		// We do this before iterating through and attaching the data to the
		// graphs because there is not always a 1:1 relationship between series
		// and graph instance.
		//
		// After padding the data of each series, replace the series data with a
		// mesh of the series superset (cached) and the current-view series
		// subset (received in response just now).
		for (let s in data.series) {

			padDataIfNeeded(data.series[s].data);

			data.series[s].data = createMeshedTimeSeries(file.fileData.series[s].data, data.series[s].data);

		}

		console.log("FINAL DATA", data);

		// Temporarily unsynchronize the graphs
		file.unsynchronizeGraphs();

		// In order to process the backend response, we actually iterate through
		// all of the local client-side graph instances (as opposed to iterating
		// through the series provided in the response). We do this because one
		// data series could be present in more than one graph (at least as
		// conceived currently), for example as an individua series graph and in
		// a group-of-series graph.
		graphLoop:
		for (let g in file.graphs) {

			// We're only processing data responses for series of graphs
			// currently showing.
			if (file.graphs[g].isShowing()) {

				if (file.graphs[g].isGroup) {

					// Group-of-series graph handling...

					// Verify that we received all series in the group in the
					// backend response. If not, continue on to the next graph.
					for (let s of file.graphs[g].group) {
						if (!data.series.hasOwnProperty(s)) {
							vo("Did not receive data for series "+s+". Skipping group "+g+".");
							continue graphLoop;
						}
					}

					// Replace graph data with merge of mesh of group series
					console.log("Replacing multi series graph data with", createMergedTimeSeries(file.graphs[g].group, data.series));
					file.graphs[g].replacePlottedData(createMergedTimeSeries(file.graphs[g].group, data.series))

				} else {

					// Single graph handling...

					// If this is a graph that represents a single series, then
					// we grab the series name from the graph instance property.
					let s = file.graphs[g].series;

					// Verify that we received the series in question in the
					// backend response.
					if (!data.series.hasOwnProperty(s)) {
						continue;
					}

					// Replace graph data with mesh of series
					file.graphs[g].replacePlottedData(data.series[s].data);

				}

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