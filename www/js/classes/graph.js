'use strict';

// Graph class constructor. Group is an optional parameter which, if the graph
// represents a group, should be the array of series names inside the group.
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

	// Set this.isGroup (indicates whether this graph represents a group of
	// series) and this.group (holds series names belonging to the group, or
	// empty array if not a group)
	if (this.file.fileData.series[this.series].hasOwnProperty('group') && this.file.fileData.series[this.series].group.length > 0) {
		this.isGroup = true;
		this.group = this.file.fileData.series[this.series].group;
	} else {
		this.isGroup = false;
		this.group = [];
	}

	// Build the graph
	this.build();

}

Graph.prototype.build = function() {

	// Create the graph wrapper dom element
	this.graphWrapperDomElement = document.createElement('DIV');
	this.graphWrapperDomElement.className = 'graph_wrapper';

	this.graphWrapperDomElement.innerHTML =
		'<table>' +
			'<tbody>' +
				'<tr>' +
					'<td class="graph_title">'+this.series+'</td>' +
					'<td rowspan="2">' +
						'<div class="graph"></div>' +
					'</td>' +
				'</tr>' +
				'<tr>' +
					'<td class="legend"><div></div></td>'
				'</tr>' +
			'</tbody>' +
		'</table>';

	document.getElementById('graphs').appendChild(this.graphWrapperDomElement);

	// Grab references to the legend & graph elements so they can be used later.
	this.legendDomElement = this.graphWrapperDomElement.querySelector('.legend > div');
	this.graphDomElement = this.graphWrapperDomElement.querySelector('.graph');

	// let titleDomElement = document.createElement('DIV');
	// titleDomElement.className = 'graph_title';
	// titleDomElement.innerText = this.series;
	// this.graphWrapperDomElement.appendChild(titleDomElement);
	//
	// // Create the legend dom element
	// this.legendDomElement = document.createElement('DIV');
	// this.legendDomElement.className = 'legend';
	// this.graphWrapperDomElement.appendChild(this.legendDomElement);
	//
	// // Create the graph dom element
	// this.graphDomElement = document.createElement('DIV');
	// this.graphDomElement.className = 'graph';
	// this.graphWrapperDomElement.appendChild(this.graphDomElement);

	// Attach this class instance as a DOM element property (this is for the
	// click callback handler to work properly since dygraphs implements it
	// poorly).
	$(this.graphDomElement).data('graphClassInstance', this);

	// Instantiate the dygraph
	if (moveToConfig.defaultSeries.includes(this.series)) {
		this.instantiateDygraph();
	} else {
		this.hideDOMElements();
	}

	// Add the control for the graph
	this.file.graphSelectionMenu.add(this.series, moveToConfig.defaultSeries.includes(this.series));

};

// Hide the graph & legend divs
Graph.prototype.hideDOMElements = function() {
	this.graphWrapperDomElement.style.display = 'none';
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

	// Determine if we have a specified y-axis range for this group or series.
	// If it's a group, then determine a range that would include each series'
	// configured range.
	let yAxisRange = [null, null];
	if (this.isGroup) {
		for (let s of this.group) {
			if (moveToConfig.ranges.hasOwnProperty(s)) {
				if (yAxisRange[0] === null || yAxisRange[0] > moveToConfig.ranges[s][0]) {
					yAxisRange[0] = moveToConfig.ranges[s][0];
				}
				if (yAxisRange[1] === null || yAxisRange[1] < moveToConfig.ranges[s][1]) {
					yAxisRange[1] = moveToConfig.ranges[s][1];
				}
			}
		}
	}
	else if (moveToConfig.ranges.hasOwnProperty(this.series)) {
		yAxisRange = moveToConfig.ranges[this.series];
	}

	// Create the dygraph
	this.dygraphInstance = new Dygraph(this.graphDomElement, this.file.fileData.series[this.series].data, {
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
		clickCallback: clickCallbackHandler,
		colors: ['#171717'],//'#5253FF'],
		dateWindow: timeWindow,
		//drawPoints: true,
		gridLineColor: 'rgb(232,122,128)',
		interactionModel: {
			'mousedown': handleMouseDown.bind(this),
			'mousemove': handleMouseMove.bind(this),
			'mouseup': handleMouseUp.bind(this),
			'dblclick': handleDoubleClick.bind(this),
			'mousewheel': handleMouseWheel.bind(this)
		},
		labels: this.file.fileData.series[this.series].labels,
		labelsDiv: this.legendDomElement,
		plotter: downsamplePlotter,
		/*series: {
		  'Min': { plotter: downsamplePlotter },
		  'Max': { plotter: downsamplePlotter }
		},*/
		//title: this.series,
		underlayCallback: underlayCallbackHandler,
		valueRange: yAxisRange
	});

};

// Returns a boolean indicating whether this graph is currently showing.
Graph.prototype.isShowing = function() {
	return this.dygraphInstance !== null;
};

// Remove the graph from the interface.
Graph.prototype.remove = function() {

	// Unsynchronize the graphs temporarily for the duration of the removal.
	this.file.unsynchronizeGraphs();

	// Destroy the dygraph instance
	if (this.dygraphInstance !== null) {
		this.dygraphInstance.destroy();
	}

	// Delete the dygraph instance reference
	this.dygraphInstance = null;

	// Hide the graph & legend divs
	this.hideDOMElements();

	// Resynchronize the graphs now that removal is complete.
	this.file.synchronizeGraphs()

};

Graph.prototype.replacePlottedData = function(data) {
	this.dygraphInstance.updateOptions({
		file: data
	});
};

// Toggle the graph to show.
Graph.prototype.show = function() {

	// Unsynchronize the graphs temporarily for the duration of the post-load addition.
	this.file.unsynchronizeGraphs();

	// Show the graph & legend divs
	this.showDOMElements();

	// Instantiate the dygraph
	this.instantiateDygraph();

	// Resynchronize the graphs now that the addition is complete.
	this.file.synchronizeGraphs();

	// Run pre-defined anomaly detection jobs (async).
	// NOTE: This function takes either string or array as parameter, so it
	// works for a single or group series graph.
	if (this.isGroup) {
		this.file.runAnomalyDetectionJobsForSeries(this.group);
	} else {
		this.file.runAnomalyDetectionJobsForSeries(this.series);
	}

	// Update the data from the backend for the new series only
	this.updateCurrentViewData()

};

// Show the graph & legend divs for the named series.
Graph.prototype.showDOMElements = function() {
	this.graphWrapperDomElement.style.display = 'block';
};

// Request and update data for the current view of the graph.
// NOTE: There is an identically-named function on both File and Graph classes,
// the former which updates data for all graphs currently appearing and the
// latter which updates the data only for the single graph.
Graph.prototype.updateCurrentViewData = function() {

	// Get the x-axis range
	let xRange = this.dygraphInstance.xAxisRange();

	// Assemble the series ID(s) for which we will request updated data.
	let series = this.isGroup ? this.group : [this.series];

	// Request the updated view data from the backend.
	requestHandler.requestSeriesRangedData(this.file.filename, series, xRange[0]/1000-this.file.fileData.baseTime, xRange[1]/1000-this.file.fileData.baseTime, this.file.getPostloadDataUpdateHandler());

};
