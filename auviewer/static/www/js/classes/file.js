'use strict';

function File(project, filename) {

	// Holds the project name
	this.projname = project;

	// Holds the filelname
	this.filename = filename;

	// Load the project config
	this.config = templateSystem.getProjectTemplate(project);

	// Holds the file metadata
	this.metadata = {};

	// Holds graph object instances pertaining to the file.
	this.graphs = {};

	// Holds the initial payload data for the file
	this.fileData = {};

	// Holds annotations for the file
	this.annotations = [];

	// Indicates the index of the annotation currently being reviewed in the
	// annotation workflow, or -1 if user is not currently in the workflow.
	this.annotationWorkflowCurrentIndex = -1;

	// Indicates user is at the i'th anomaly, during the annotation workflow.
	this.annotationWorkflowAnomalyNumber = 0;

	// Used for realtime-mode to buffer incoming new data
	this.newDataBuffer = null;

	// This flag indicates whether we're currently in continuous render mode
	// (see File.prototype.renderBufferedRealtimeData).
	this.continuousRender = false;

	// Holds the reference to the graph synchronization object
	this.sync = null;

	// Holds the parameters of executed anomaly detection jobs whose results are
	// still being displayed (avoids duplication of jobs).
	this.alreadyExecutedAnomalyDetectionJobs = [];

	/*
	Holds the min [0] and max [1] x-value across all graphs currently displayed.
	This is calculated in the convertToDateObjsAndUpdateExtremes() function. The
	values should hold milliseconds since epoch, as this is the format specified
	for options.dateWindow, though the values will intermediately be instances
	of the Date object while the extremes are being calculated. This array may
	be passed into the options.dateWindow parameter for a dygraph.
	*/
	this.globalXExtremes = [];

	// Persist for callback
	let file = this;

	// If we're not in realtime-mode, request the initial file payload, and
	// handle the response when it comes.
	requestHandler.requestInitialFilePayload(this.projname, this.filename, function (data) {

		// Prepare data received from the backend and attach to class instance
		file.fileData = file.prepareData(data, data.baseTime);

		// Pad data, if necessary, for each series
		for (let s of Object.keys(file.fileData.series)) {
			padDataIfNeeded(file.fileData.series[s].data);
		}

		// Create any defined group series which has at least one member series
		// presently available.
		//
		// For each project-defined group, create a new, collated data set.
		// NOTE: If you're trying to understand this code in the future, I'm
		// sorry. I could not document this in any way that would help make it
		// more understandable, and it is a bit of a labyrinth.
		for (let group of file.config.groups) {

			// // Check whether all series members of the group are present, and if
			// // not, then skip this group.
			// for (let s of group) {
			// 	if (!this.fileData.series.hasOwnProperty(s)) {
			// 		continue groupLoop;
			// 	}
			// }

			// Verify at least one series member of the group is present.
			let atLeastOneSeriesPresent = false;
			for (let s of group) {
				if (file.fileData['series'].hasOwnProperty(s)) {
					atLeastOneSeriesPresent = true;
					break;
				}
			}
			if (atLeastOneSeriesPresent === false) {
				continue;
			}

			file.createGroupSeries(group, createMergedTimeSeries(group, file.fileData.series));

		}

		window.requestAnimationFrame(

			(function() {

				let t0 = performance.now();

				// Attach & render file metadata
				this.metadata = data.metadata;
				this.renderMetadata();

				// Instantiate event graphs
				this.renderEventGraphs();

				// Instantiate series graphs
				for (let s of Object.keys(this.fileData.series)) {
					this.graphs[s] = new Graph(s, file);
				}

				// Synchronize the graphs
				this.synchronizeGraphs();

				// Populate the annotations
				if (Array.isArray(this.fileData.annotations) && this.fileData.annotations.length > 0) {
					for (let a of this.fileData.annotations) {
						this.annotations.push(new Annotation({valuesArrayFromBackend: a}, 'existing'));
					}
					globalStateManager.currentFile.triggerRedraw();
				}

				// If this is a realtime file, subscribe to realtime updates via the
				// websocket connection.
				if (this.mode() === 'realtime') {

					socket.emit('subscribe', {
						project: this.projname,
						filename: this.filename
					});

				}

				let tt = performance.now() - t0;
				globalAppConfig.verbose && tt > globalAppConfig.performanceReportingThresholdMS && console.log("Initial file graph building took " + Math.round(tt) + "ms.", this.projname, this.filename);

				// Grab the alert generation dropdown
				let alertGenSeriesDropdown = document.getElementById('alert_gen_series_field');

				// // Clear the alert generation dropdown
				// // See: https://jsperf.com/innerhtml-vs-removechild/15
				// while (alertGenSeriesDropdown.firstChild) {
				// 	alertGenSeriesDropdown.removeChild(alertGenSeriesDropdown.firstChild);
				// }

				// Populate the alert generation dropdown
				let opt = document.createElement('option');
				alertGenSeriesDropdown.add(opt);
				for (let s of Object.keys(this.fileData.series)) {
					let opt = document.createElement('option');
					opt.text = s;
					opt.value = s;
					alertGenSeriesDropdown.add(opt);
				}

				// Re-render the select picker
				$(alertGenSeriesDropdown).selectpicker('refresh');

				// Process pre-defined anomaly detection for all currently-displaying
				// series. We gather all displaying series before starting to send the
				// anomaly detection requests because we don't want to conflict with a
				// the on-display anomaly detection that will happen when a user toggles
				// a hidden series to display.
				let seriesInitiallyDisplaying = [];
				for (let s of Object.keys(this.graphs)) {
					if (this.graphs[s].isShowing()) {
						if (this.graphs[s].isGroup) {
							seriesInitiallyDisplaying.push.apply(seriesInitiallyDisplaying, this.graphs[s].group);
						} else {
							seriesInitiallyDisplaying.push(this.graphs[s].series);
						}
					}
				}
				this.runAnomalyDetectionJobsForSeries(seriesInitiallyDisplaying);

			}).bind(file)

		);

	});

}

// Go to the next annotation in the workflow.
File.prototype.annotationWorkflowNext = function() {

	// Iterate through next subsequent annotations until we hit another anomaly
	// or hit the end of the array.
	while(this.annotationWorkflowCurrentIndex++ || true) {

		// If we hit the end of the array, we've completed the annotation workflow.
		if (this.annotationWorkflowCurrentIndex >= this.annotations.length) {
			this.annotationWorkflowCurrentIndex = -1;
			this.resetZoomToOutermost();

			this.annotationWorkflowAnomalyNumber = 0;
			document.getElementById("annotationWorkflowSubtext").innerText = '';

			return;
		}

		// If we reach another anomaly, stop there.
		if (this.annotations[this.annotationWorkflowCurrentIndex].state === 'anomaly') {
			break;
		}

	}

	// Update indicator number
	this.annotationWorkflowAnomalyNumber++;

	// Update annotation display to reflect the newly set parameters.
	this.annotationWorkflowUpdateCurrent();

};

// Go to the previous annotation in the workflow.
File.prototype.annotationWorkflowPrevious = function() {

	// Iterate through next subsequent annotations until we hit another anomaly
	// or hit the end of the array.
	while(this.annotationWorkflowCurrentIndex-- || true) {

		// If we hit the end of the array, we've completed the annotation workflow.
		if (this.annotationWorkflowCurrentIndex < 0) {
			this.annotationWorkflowCurrentIndex = -1;
			this.resetZoomToOutermost();

			this.annotationWorkflowAnomalyNumber = 0;
			document.getElementById("annotationWorkflowSubtext").innerText = '';

			return;
		}

		// If we reach another anomaly, stop there.
		if (this.annotations[this.annotationWorkflowCurrentIndex].state === 'anomaly') {
			break;
		}

	}

	// Update indicator number
	this.annotationWorkflowAnomalyNumber--;

	// Update annotation display to reflect the newly set parameters.
	this.annotationWorkflowUpdateCurrent();

};

// Update current annotation display for the workflow according to
// this.annotationWorkflowCurrentIndex and this.annotationWorkflowAnomalyNumber.
File.prototype.annotationWorkflowUpdateCurrent = function() {

	// Grab our annotation
	let annotation = this.annotations[this.annotationWorkflowCurrentIndex];

	// Update annotation counter display
	let prefix = '<tr><th>';
	let between = '</th><td>';
	let postfix = '</td></tr>';

	document.getElementById("annotationWorkflowSubtext").innerHTML =
		'<p style="font-style: italic; margin-bottom: 2px;">Current Anomaly</p>' +
		'<table><tbody>' +
		prefix+'Anomaly #:'+between+this.annotationWorkflowAnomalyNumber+postfix +
		prefix+'Series:'+between+annotation.series+postfix +
		prefix+'Begin:'+between+annotation.getStartDate().toLocaleString()+postfix +
		prefix+'End:'+between+annotation.getEndDate().toLocaleString()+postfix +
		'</tbody></table>';

	// Calculate the zoom window

	// Total zoom window time to display
	let zwTotal = 6 * 60 * 60;

	// Total gap = total zoom window less the anomaly duration
	let zwTotalGap = zwTotal - (annotation.end - annotation.begin);

	// Gap on either side
	let zwGapSingleSide = zwTotalGap / 2;

	// Compute the zoom window begin & end
	let zwBegin = (annotation.begin - zwGapSingleSide + this.fileData.baseTime)*1000;
	let zwEnd = (annotation.end + zwGapSingleSide + this.fileData.baseTime)*1000;

	// Zoom to the designated window
	this.zoomTo([zwBegin, zwEnd]);

};

// Removes all detected anomalies
File.prototype.clearAnomalies = function() {

	// Clear all anomaly annotations from the annotations array
	for (let i = this.annotations.length-1; i >= 0; i--) {
		if (this.annotations[i].state === 'anomaly') {
			this.annotations[i].deleteLocal();
		}
	}

	// Clear the already-executed anomaly detection jobs array
	this.alreadyExecutedAnomalyDetectionJobs = [];

	// Redraw
	this.triggerRedraw();

};

// Creates a group series in the class's attached file data with a mesh of the
// member series data.
File.prototype.createGroupSeries = function(group, mergedGroupData) {

	// Enumerate the column labels
	let labels = ['time'];
	for (let s of group) {
		labels.push(s + ' Min');
		labels.push(s + ' Max');
		labels.push(s);
	}

	// Add the new combined series to the file data if it does not
	// already exist.
	this.fileData.series[getGroupName(group)] = {
		id: "Group:\n" + group.join("\n"),
		labels: labels,
		group: group,
		data: mergedGroupData
	};

};

File.prototype.destroy = function() {

	window.requestAnimationFrame(

		(function() {

			// Destroy graph synchronization state management
			this.unsynchronizeGraphs();

			// Remove each graph
			for (let s of Object.keys(this.graphs)) {
				this.graphs[s].remove();
			}

			// Clear the graph div
			// See: https://jsperf.com/innerhtml-vs-removechild/15
			const graphsDiv = document.getElementById('graphs');
			while (graphsDiv.firstChild) {
				graphsDiv.removeChild(graphsDiv.firstChild);
			}

			// Clear the series display controller dropdown
			// See: https://jsperf.com/innerhtml-vs-removechild/15
			const seriesDisplayControllerDropdown = document.getElementById('series_display_controller');
			while (seriesDisplayControllerDropdown.firstChild) {
				seriesDisplayControllerDropdown.removeChild(seriesDisplayControllerDropdown.firstChild);
			}
			$(seriesDisplayControllerDropdown).selectpicker('refresh');

			// Clear the alert generation dropdown
			// See: https://jsperf.com/innerhtml-vs-removechild/15
			const alertGenSeriesDropdown = document.getElementById('alert_gen_series_field');
			while (alertGenSeriesDropdown.firstChild) {
				alertGenSeriesDropdown.removeChild(alertGenSeriesDropdown.firstChild);
			}
			$(alertGenSeriesDropdown).selectpicker('refresh');

			// Clear state management data
			this.graphs = {};
			this.fileData = {};
			this.globalXExtremes = [];

		}).bind(this)

	);

};

// Run anomaly detection with the parameters provided. The callback parameter,
// if provided, will be called either after the response has been received from
// the server and processed or upon a return resulting from a missing-parameter
// error.
File.prototype.detectAnomalies = function(series, thresholdlow, thresholdhigh, duration, persistence, maxgap, callback=null) {

	globalAppConfig.verbose && console.log("Anomaly detection called.");

	// In case any of our numerical parameters are numerical 0, convert them to
	// strings now so we can effectively do parameter checking.
	if (thresholdlow === 0) {
		thresholdlow = '0';
	}
	if (thresholdhigh === 0) {
		thresholdhigh = '0';
	}
	if (duration === 0) {
		duration = '0';
	}
	if (persistence === 0) {
		persistence = '0';
	}
	if (maxgap === 0) {
		maxgap = '0';
	}

	// These parameters are required, and either threshold low or threshold high
	// or both is required.
	if(
		(!series ||
		(!duration && duration !== 0) ||
		(!persistence && persistence !== 0) ||
		(!maxgap && maxgap !== 0))

		||

		((!thresholdlow && thresholdlow !== 0) &&
		(!thresholdhigh && thresholdhigh !== 0))
	) {

		// Log the error to console.
		console.log("Required parameters are missing for anomaly detection.");

		// Call callback if provided
		if (callback !== null && typeof callback === 'function') {
			callback();
		}

		// Return as we cannot continue anomaly detection.
		return;

	}

	// Check whether this job has already run
	for (let j of this.alreadyExecutedAnomalyDetectionJobs) {
		if (j[0] === series &&
			(j[1] === parseFloat(thresholdlow) || (isNaN(j[1]) && isNaN(parseFloat(thresholdlow)))) &&
			(j[2] === parseFloat(thresholdhigh) || (isNaN(j[2]) && isNaN(parseFloat(thresholdhigh)))) &&
			(j[3] === parseFloat(duration) || (isNaN(j[3]) && isNaN(parseFloat(duration)))) &&
			(j[4] === parseFloat(persistence) || (isNaN(j[4]) && isNaN(parseFloat(persistence)))) &&
			(j[5] === parseFloat(maxgap)) || (isNaN(j[5]) && isNaN(parseFloat(maxgap)))) {

			// Log the error to console.
			console.log("An anomaly detection job with the same parameters executed previously. Aborting.");

			// Call callback if provided
			if (callback !== null && typeof callback === 'function') {
				callback();
			}

			// Return as we cannot continue anomaly detection.
			return;
		}
	}

	// Add this job's parameters to the already-executed jobs array
	this.alreadyExecutedAnomalyDetectionJobs.push([series, parseFloat(thresholdlow), parseFloat(thresholdhigh), parseFloat(duration), parseFloat(persistence), parseFloat(maxgap)]);

	// Persist for callback
	let file = this;

	requestHandler.requestAnomalyDetection(globalStateManager.currentFile.projname, globalStateManager.currentFile.filename, series, thresholdlow, thresholdhigh, duration, persistence, maxgap, function (data) {

		if (Array.isArray(data) && data.length > 0) {

			for (let a of data) {
				file.annotations.push(new Annotation({series: series, begin: a[0], end: a[1]}, 'anomaly'));
			}

			file.triggerRedraw();

			// Call callback if provided
			if (callback !== null && typeof callback === 'function') {
				callback();
			}

		}

	});

    globalAppConfig.verbose && console.log("Anomaly detection request sent.");

};

// Run anomaly detection with the user-input form values.
File.prototype.detectAnomaliesFromForm = function() {

	let series = document.getElementById("alert_gen_series_field").value;
	let thresholdlow = document.getElementById("alert_gen_threshold_low_field").value;
	let thresholdhigh = document.getElementById("alert_gen_threshold_high_field").value;
	let duration = document.getElementById("alert_gen_duration_field").value;
	let persistence = document.getElementById("alert_gen_dutycycle_field").value;
	let maxgap = document.getElementById("alert_gen_maxgap_field").value;

	this.detectAnomalies(series, thresholdlow, thresholdhigh, duration, persistence, maxgap);

};

// Returns the graph class instance for the series name provided if it exists.
// Otherwise, returns null;
File.prototype.getGraphForSeries = function(s) {
	for (let g in this.graphs) {
		if (this.graphs[g].series === s) {
			return this.graphs[g];
		}
	}
	return null;
};

// Return the first showing graph, or null.
File.prototype.getFirstShowingGraph = function() {
	for (let s of Object.keys(this.graphs)) {
		if (this.graphs[s].dygraphInstance !== null) {
			return this.graphs[s];
		}
	}
	return null;
};

// Returns the outermost zoom window, a two-member array with start & stop time.
File.prototype.getOutermostZoomWindow = function(type='') {
	if (type==='lead') {
		return [this.globalXExtremes[1] - (10*1000), this.globalXExtremes[1]];
	}
	return this.mode() === 'realtime' ? [this.globalXExtremes[1] - (globalStateManager.realtimeTimeWindow*1000), this.globalXExtremes[1]] : this.globalXExtremes;
};

// Returns a handler function which processes new series data received from the
// backend.
File.prototype.getPostloadDataUpdateHandler = function() {

	let file = this;

	return function(data) {

		// Validate the response data
		if (typeof data === 'undefined' || !data || (!data.hasOwnProperty('series') && !data.hasOwnProperty('events'))) {
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

			convertFirstColumnToDate(data.series[s].data, file.fileData.baseTime);

			padDataIfNeeded(data.series[s].data);

			data.series[s].data = createMeshedTimeSeries(file.fileData.series[s].data, data.series[s].data);

		}

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
								globalAppConfig.verbose && console.log("Did not receive data for series " + s + ". Skipping group " + g + ".");
								continue graphLoop;
							}
						}

						// Replace graph data with merge of mesh of group series
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

	};

};

// Handle a series display controller item being selected or deselected.
File.prototype.handleSeriesDisplayControllerUpdate = function() {
	const options = document.getElementById('series_display_controller').options;
	for (let opt of options) {
		let graph = this.getGraphForSeries(opt.value)
		if (opt.selected === true && graph.isShowing() === false) {
			globalAppConfig.verbose && console.log('Showing', opt.value);
			graph.show();
		}
		else if(opt.selected === false && graph.isShowing() === true) {
			globalAppConfig.verbose && console.log('Hiding', opt.value);
			graph.remove();
		}
	}
};

// Returns the mode of File, either 'realtime' or 'file'.
File.prototype.mode = function() {
	return (this.projname === '__realtime__' && this.filename === '__realtime__') ? 'realtime' : 'file';
};

// Prepares & returns data by converting times to Date objects and calculating
// x-axis extremes across all data.
File.prototype.prepareData = function(data, baseTime) {

	let t0 = performance.now();

	// Get array of series
	let series = Object.keys(data.series);

	// Process series data
	if (series.length > 0) {

		// Prime the graph extremes if new. Otherwise, convert the existing extremes
		// to date objects.
		if (this.globalXExtremes.length === 0) {
			this.globalXExtremes[0] = new Date((data.series[series[0]].data[0][0] + baseTime) * 1000);
			this.globalXExtremes[1] = new Date((data.series[series[0]].data[0][0] + baseTime) * 1000);
		} else {
			this.globalXExtremes[0] = new Date(this.globalXExtremes[0].valueOf());
			this.globalXExtremes[1] = new Date(this.globalXExtremes[1].valueOf());
		}

		// Process series data
		for (let s of series) {

			// If this series has no data, continue
			if (data.series[s].data.length < 1) {
				continue;
			}

			convertFirstColumnToDate(data['series'][s].data, baseTime);

			// Update global x-minimum if warranted
			if (data.series[s].data[0][0] < this.globalXExtremes[0]) {
				this.globalXExtremes[0] = data.series[s].data[0][0];
			}

			// Update global x-maximumm if warranted
			if (data.series[s].data[data.series[s].data.length - 1][0] > this.globalXExtremes[1]) {
				this.globalXExtremes[1] = data.series[s].data[data.series[s].data.length - 1][0];
			}

		}

	}

	// Process event data
	if (data.hasOwnProperty('events')) {

		// Get array of event series
		let events = Object.keys(data.events);

		// Process event data
		for (let s of events) {

			// If this series has no data, continue
			if (data.events[s].length < 1) {
				continue;
			}

			for (let i in data.events[s]) {

				// Convert the ISO8601-format string into a Date object.
				data.events[s][i][0] = new Date((data.events[s][i][0] + baseTime) * 1000);

			}

			// Update global x-minimum if warranted
			if (data.events[s][0][0] < this.globalXExtremes[0]) {
				this.globalXExtremes[0] = data.events[s][0][0];
			}

			// Update global x-maximumm if warranted
			if (data.events[s][data.events[s].length - 1][0] > this.globalXExtremes[1]) {
				this.globalXExtremes[1] = data.events[s][data.events[s].length - 1][0];
			}

		}

	}

	// If we have global x-extremes data now
	if (this.globalXExtremes.length > 0) {

		// When the x-axis extremes have been calculated (as dates), convert them
		// to milliseconds since epoch, as this is what is specified in the options
		// reference: http://dygraphs.com/options.html#dateWindow
		this.globalXExtremes[0] = this.globalXExtremes[0].valueOf();
		this.globalXExtremes[1] = this.globalXExtremes[1].valueOf();

	}

	let tt = performance.now() - t0;
	globalAppConfig.verbose && tt > globalAppConfig.performanceReportingThresholdMS && console.log("File.prepareData() took " + Math.round(tt) + "ms.");

	return data;

};

//Processes newly received realtime data.
File.prototype.processNewRealtimeData = function(newData) {

	// Validations
	if (this.mode() !== 'realtime') {
		// This function only applies to realtime mode. If we're not in realtime
		// mode, then return now.
		console.log('Error: File.prototype.processNewRealtimeData() called while not in realtime mode.');
		return;
	} else if (typeof newData === 'undefined' || !newData || !newData.hasOwnProperty('series')) {
		// Validate the new data
		console.log('Error: File.prototype.processNewRealtimeData called with invalid data parameter.', newData);
		return;
	}

	// Initialize buffer if needed
	if (this.newDataBuffer === null) {
		this.newDataBuffer = { 'series': {} };
	}

	// Add new data to buffer
	let preparedData = this.prepareData(newData, this.fileData.baseTime);
	for (let s of Object.getOwnPropertyNames(preparedData['series'])) {
		if (this.newDataBuffer['series'].hasOwnProperty(s)) {
			// If the series is already in the buffer, concatenate the new data
			// with the currently-buffered series data.
			this.newDataBuffer['series'][s]['data'] = this.newDataBuffer['series'][s]['data'].concat(preparedData['series'][s]['data']);
		} else {
			this.newDataBuffer['series'][s] = preparedData['series'][s];
		}

		// Trim the data if we've surpassed globalAppConfig.M data points
		if (this.newDataBuffer['series'][s]['data'].length > globalAppConfig.M) {
			this.newDataBuffer['series'][s]['data'].splice(0, this.newDataBuffer['series'][s]['data'].length - globalAppConfig.M)
		}

	}

	// If we're not in continuous render mode, put us into continuous render
	// mode and call the renderer.
	if (this.continuousRender === false) {
		globalAppConfig.verbose && console.log('Initiating continuous render mode.');
		this.continuousRender = true;
		this.renderBufferedRealtimeData();
	}

};

// Renders new buffered realtime data recursively & continuously until there is
// no more data data in the buffer.
File.prototype.renderBufferedRealtimeData = function() {

	window.requestAnimationFrame(

		(function() {

			// If the new data buffer is empty, take us out of continuous render
			// mode and return.
			if (this.newDataBuffer === null) {
				globalAppConfig.verbose && console.log('No data in realtime buffer. Aborting continuous render mode.');
				this.continuousRender = false;
				return;
			}

			globalAppConfig.verbose && console.log('Re-rendering realtime data.');

			// Grab the current buffer for local use, and then clear
			const buffer = this.newDataBuffer;
			this.newDataBuffer = null;

			// Start the performance timer
			let t0 = performance.now();

			// Unsynchronize the graphs
			this.unsynchronizeGraphs();

			// Get the new outermost zoom window now after the newly processed data.
			let dt = this.getOutermostZoomWindow();
			let ldt = this.getOutermostZoomWindow('lead');

			// Iterate through the new series
			for (let s of Object.getOwnPropertyNames(buffer['series'])) {

				// If there is a pre-existing equivalent series
				if (this.fileData['series'].hasOwnProperty(s)) {

					// Add the buffered data to the series data
					this.fileData['series'][s]['data'] = this.fileData['series'][s]['data'].concat(buffer['series'][s]['data']);

					// Trim the data if we've surpassed globalAppConfig.M data points
					if (this.fileData['series'][s]['data'].length > globalAppConfig.M) {
						this.fileData['series'][s]['data'].splice(0, this.fileData['series'][s]['data'].length - globalAppConfig.M)
					}

					// Grab the graph class instance
					let g = this.getGraphForSeries(s);

					// If the graph for this series is showing, redraw with new data.
					if (g.isShowing()) {

						// Re-plot the graph with the new data
						g.dygraphInstance.updateOptions({
							file: this.fileData['series'][s]['data'],
							dateWindow: dt
						});

						// Also re-plot the leading graph display with the new data
						if (g.rightDygraphInstance) {
							g.rightDygraphInstance.updateOptions({
								file: this.fileData['series'][s]['data'],
								dateWindow: ldt
							});
						}

					}

				} else {

					// Attach the new data
					this.fileData['series'][s] = buffer['series'][s];

					// Instantiate the new graph
					this.graphs[s] = new Graph(s, this);

				}

			}

			// Iterate through group series
			for (let group of this.config.groups) {

				// If this group has no new data in the realtime buffer, skip it.
				let atLeastOneSeriesPresent = false;
				for (let s of group) {
					if (buffer['series'].hasOwnProperty(s)) {
						atLeastOneSeriesPresent = true;
						break;
					}
				}
				if (atLeastOneSeriesPresent === false) {
					// Skip this group
					continue;
				}

				// Having reached this point, we know this group has new
				// buffered realtime data available.

				// Grab the group name
				const groupName = getGroupName(group);

				// If the group already exists, update it with the new data.
				if (this.fileData['series'].hasOwnProperty(groupName)) {

					// Add the buffered data to the series data
					this.fileData['series'][groupName]['data'] = this.fileData['series'][groupName]['data'].concat(createMergedTimeSeries(group, buffer['series']))

					// Trim the data if we've surpassed globalAppConfig.M data points
					if (this.fileData['series'][groupName]['data'].length > globalAppConfig.M) {
						this.fileData['series'][groupName]['data'].splice(0, this.fileData['series'][groupName]['data'].length - globalAppConfig.M)
					}

					// Grab the graph class instance
					let g = this.getGraphForSeries(groupName);

					// If the graph for this series is showing, redraw with new data.
					if (g.isShowing()) {

						// Re-plot the graph with the new data
						g.dygraphInstance.updateOptions({
							file: this.fileData['series'][groupName]['data'],
							dateWindow: dt
						});

						// Also re-plot the leading graph display with the new data
						if (g.rightDygraphInstance) {
							g.rightDygraphInstance.updateOptions({
								file: this.fileData['series'][groupName]['data'],
								dateWindow: ldt
							});
						}

					}

				}

				// If the group does not exist yet, create it.
				else {

					// Create the new group (which also attaches the new data).
					this.createGroupSeries(group, createMergedTimeSeries(group, buffer['series']));

					// Instantiate the new group graph
					this.graphs[groupName] = new Graph(groupName, this);

				}

			}

			// Synchronize the graphs
			this.synchronizeGraphs();

			let tt = performance.now() - t0;
			globalAppConfig.verbose && tt > globalAppConfig.performanceReportingThresholdMS && console.log("Re-rendering realtime data took " + Math.round(tt) + "ms.");

			// Call recursively.
			setTimeout(this.renderBufferedRealtimeData.bind(this),  100);

		}).bind(this)

	);

};

// Render event graph
File.prototype.renderEventGraphs = function() {

	// Check that we have the relevant event data
	if ( !('events' in this.fileData) || !('meds' in this.fileData.events) ) {
		return;
	}

	for (let eventtype of ['ce', 'meds']) {

		let eventdata = undefined;
		if (eventtype === 'ce') {
			eventdata = this.fileData.events.ce;
		} else if (eventtype === 'meds') {
			eventdata = this.fileData.events.meds;
		}

		if (eventdata === undefined)
			continue;

		// Create our data
		let graphData = [];
		for (let e of eventdata) {
			graphData.push([e[0], 1]);
		}

		// Create the graph wrapper dom element
		let graphWrapperDomElement = document.createElement('DIV');
		graphWrapperDomElement.className = 'graph_wrapper';

		graphWrapperDomElement.innerHTML =
			'<table>' +
				'<tbody>' +
					'<tr>' +
						'<td class="graph_title">' + (eventtype === 'meds' ? 'Medications' : (eventtype === 'ce' ? 'Clinical Events' : '')) +'</td>' +
						'<td rowspan="2">' +
							'<div class="graph"></div>' +
						'</td>' +
					'</tr>' +
					'<tr>' +
						'<td class="legend"><div></div></td>' +
					'</tr>' +
				'</tbody>' +
			'</table>';

		document.getElementById('graphs').appendChild(graphWrapperDomElement);

		// Grab references to the legend & graph elements so they can be used later.
		let legendDomElement = graphWrapperDomElement.querySelector('.legend > div');
		let graphDomElement = graphWrapperDomElement.querySelector('.graph');

		// Create the event dygraph instances object is does not exist
		if (!('eventDygraphInstances' in this)) {
			this.eventDygraphInstances = {};
		}

		this.eventDygraphInstances[eventtype] = new Dygraph(graphDomElement, graphData, {
			axes: {
				y: {
					pixelsPerLabel: 300
				}
			},
			colors: ['#171717'],
			dateWindow: this.globalXExtremes,
			gridLineColor: 'rgb(232,122,128)',
			interactionModel: {
				'mousedown': handleMouseDown.bind(this),
				'mousemove': handleMouseMove.bind(this),
				'mouseup': handleMouseUp.bind(this),
				'dblclick': handleDoubleClick.bind(this),
				'mousewheel': handleMouseWheel.bind(this)
			},
			labels: ['Time', (eventtype === 'meds' ? 'Medications' : (eventtype === 'ce' ? 'Clinical Events' : ''))],
			labelsDiv: legendDomElement,
			valueRange: [0, 2]
		});

		let annotations = [];
		for (let e of eventdata) {
			annotations.push({
				series: (eventtype === 'meds' ? 'Medications' : (eventtype === 'ce' ? 'Clinical Events' : '')),
				x: e[0].valueOf(),
				shortText: 'M',
				text: e[1]
			});
		}

		// Persist this for the callback
		let file = this;
		let et = eventtype;

		this.eventDygraphInstances[eventtype].ready(function () {
			file.eventDygraphInstances[et].setAnnotations(annotations);
		});

	}

};

// Render the file metadata
File.prototype.renderMetadata = function() {

	// If we have no metadata, take no actions & return now.
	if (Object.keys(this.metadata).length < 1) {
		return;
	}

	let div = document.createElement('DIV');
	div.id = 'metadata';
	div.innerHTML = '<h2>Metadata</h2>';
	for (let property of Object.keys(this.metadata)) {
		div.innerHTML += '<br>'+property+': '+this.metadata[property];
	}
	document.getElementById('graphs').appendChild(div);

};

// Reset zoom to outermost view
File.prototype.resetZoomToOutermost = function() {
	this.zoomTo(this.getOutermostZoomWindow(), true);
};

// Runs pre-defined anomaly detection jobs for one or more series. The series
// parameter may be a string or array of strings.
File.prototype.runAnomalyDetectionJobsForSeries = function(series) {

	if (!Array.isArray(series)) {
		series = [series];
	}

	// Persist for callback
	let file = this;

	// We now use recursion to send the anomaly detection requests serially.
	let adi = 0;
	let recursiveDetectionFunc = function() {

		if (adi < file.config.anomalyDetection.length) {

			let i = adi++;

			// If the series was initially displaying, run the pre-defined
			// anomaly detection for it.
			if (file.config.anomalyDetection[i].hasOwnProperty('series') && series.includes(file.config.anomalyDetection[i].series)) {
				file.detectAnomalies(
					file.config.anomalyDetection[i].hasOwnProperty('series') ? file.config.anomalyDetection[i].series : null,
					file.config.anomalyDetection[i].hasOwnProperty('tlow') ? file.config.anomalyDetection[i].tlow : null,
					file.config.anomalyDetection[i].hasOwnProperty('thigh') ? file.config.anomalyDetection[i].thigh : null,
					file.config.anomalyDetection[i].hasOwnProperty('dur') ? file.config.anomalyDetection[i].dur : null,
					file.config.anomalyDetection[i].hasOwnProperty('duty') ? file.config.anomalyDetection[i].duty : null,
					file.config.anomalyDetection[i].hasOwnProperty('maxgap') ? file.config.anomalyDetection[i].maxgap : null,
					recursiveDetectionFunc);
			} else {
				// Even if this anomaly detection was not processed because
				// the series was not passed in, continue onto the next one.
				recursiveDetectionFunc();
			}

		}

	};

	// Kick off the recursive pre-defined anomaly detection.
	recursiveDetectionFunc();

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

	if ('eventDygraphInstances' in this) {
		for (let k of Object.keys(this.eventDygraphInstances)) {
			dygraphInstances.push(this.eventDygraphInstances[k]);
		}
	}

	// If there is not more than one graph showing to synchronize, return now.
	if (dygraphInstances.length < 2) {
		return;
	}

	// Synchronize all of the graphs.
	globalAppConfig.verbose && console.log("Synchronizing graphs.");
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

	// Request the updated view data from the backend.
	requestHandler.requestSeriesRangedData(this.projname, this.filename, series, xRange[0]/1000-this.fileData.baseTime, xRange[1]/1000-this.fileData.baseTime, this.getPostloadDataUpdateHandler());

};

// Unsynchroniz the graphs.
File.prototype.unsynchronizeGraphs = function() {

	if (this.sync != null) {

		globalAppConfig.verbose && console.log("Unsynchronizing graphs.");
		this.sync.detach();
		this.sync = null;

	}

};

// Zoom in or out by a percentage. dir parameter should be 0 for out, 1 for in.
// pct parameter should be float representing percentage by which to zoom
// (i.e. pct==.1 means 10%).
File.prototype.zoomBy = function(dir, pct) {

	// Parameter check for dir
	if (dir !== 0 && dir !== 1) {
		return;
	}

	// Grab the first showing graph
	const g = this.getFirstShowingGraph();

	// If none is showing, we can do nothing so return.
	if (g === null) {
		return;
	}

	// Get the current time range
	const ctr = g.dygraphInstance.xAxisRange();

	// Get the current timespan
	const cts = ctr[1] - ctr[0];

	// Calculate new timespan depending on whether we're zooming in or out
	const nts = dir === 0 ? Math.floor(cts+cts*pct) : Math.floor(cts-cts*pct);

	// Zoom to the new time span if new timespan is valid
	if (nts >= 1) {
		this.zoomTo(nts)
	} else {
		console.log("Cannot zoom " + (dir === 1 ? 'in' : 'out') + " by " + pct + ".")
	}

};

// Zoom to either a given time window (e.g. timeWindow=[t1,t2]) or a time span
// in milliseconds(e.g. timeWindow=1000 for 1s)
File.prototype.zoomTo = function(timeWindow, suppressDataRefresh=false) {

	// Grab the first showing graph
	const g = this.getFirstShowingGraph();

	// If none is showing, we can do nothing so return.
	if (g === null) {
		return;
	}

	// If we've been provided a timespan, convert it to and call self with range.
	if (!Array.isArray(timeWindow)) {

		// Get the current time range
		const ctr = g.dygraphInstance.xAxisRange();

		// Calculate midpoint of the current range
		const midpoint = ctr[1] - (ctr[1]-ctr[0])/2;

		// Calculate half of timespan
		const tshalf = timeWindow/2;

		// Calculate new time range
		const ntr = [Math.floor(midpoint-tshalf), Math.floor(midpoint+tshalf)];

		// Sanity check -- if they're already zoomed into this leve, we're done.
		if (ctr[0] === ntr[0] && ctr[1] === ntr[1]) {
			return;
		}

		// Call self with new time range
		this.zoomTo(ntr, suppressDataRefresh);

		// We're done here.
		return;

	}

	// Given a time range, update a single graph to the time range. We only need
	// to trigger this on one graph since they are expected to be synchronized.
	g.dygraphInstance.updateOptions({
		dateWindow: timeWindow
	});

	// Refresh data from the server for this zoom window, unless suppressed
	if (suppressDataRefresh !== true) {
		this.updateCurrentViewData();
	}

};