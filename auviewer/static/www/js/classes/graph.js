'use strict';

/*
The Graph class manages a single graph.
 */

// Graph class constructor. Group is an optional parameter which, if the graph
// represents a group, should be the array of series names inside the group.
function Graph(seriesOrGroupName, file) {

	// References the parent File instance
	this.file = file;

	// Generate new local identifier
	this.localIdentifier = globalStateManager.getGraphIdentifier();

	// Full name
	this.fullName = seriesOrGroupName;

	// Get the template
	this.template = templateSystem.getSeriesTemplate(this.file.parentProject.id, this.fullName);

	// Set properties depending on whether this is a group or series
	if (this.template.hasOwnProperty('members')) {

		/* This is a group */

		// Group flag true
		this.isGroup = true;

		// Short name
		this.shortName = seriesOrGroupName;

		// Group members
		this.members = this.template['members'];

	} else {

		/* This is a series */

		// Group flag false; this is a series
		this.isGroup = false;

		// Short name
		this.shortName = simpleSeriesName(seriesOrGroupName);

		// Group members
		this.members = [seriesOrGroupName];

	}

	// Assemble the alt text
	this.altText = "";
	for (let sn of this.members) {
		if (this.altText) {
			this.altText += "\n"
		}
		this.altText += sn
		const units = this.file.fileData.series[sn].units;
		if (units) {
			this.altText += " (units: "+units+")";
		}
	}

	// Holds the dom element of the instantiated legend
	this.legendDomElement = null;

	// Holds the dom element of the instantiated graph
	this.graphDomElement = null;

	// Holds the dygraph instances
	this.dygraphInstance = null;
	this.rightDygraphInstance = null;

	// Build the graph
	this.build();

}

// Add this graph instance to the plot control interface
Graph.prototype.addSelfToPlotControl = function() {

	// Get array of the containing folder structure names
	const folderComponents = this.fullName.split('/').slice(1, -1);

	let currentPlotDataContainer = this.isGroup ? this.file.plotControlConfig.body.data[1].data : this.file.plotControlConfig.body.data[0].data;
	for (const folder of folderComponents) {

		// Go through and try to find the existing folder
		let found = false;
		for (const existingFolder of currentPlotDataContainer) {
			if (existingFolder.value === folder) {
				currentPlotDataContainer = existingFolder.data;
				found = true;
				break;
			}
		}

		// If the folder did not exist, create it
		if (found === false) {
			const newDataContainer = { value: folder, data: [] };
			currentPlotDataContainer.push(newDataContainer);
			currentPlotDataContainer = newDataContainer.data;
		}

	}

	// Add this series to the plot control container
	currentPlotDataContainer.push({ id: this.fullName, value: this.shortName });

};

Graph.prototype.build = function() {

	// Create the graph wrapper dom element
	this.graphWrapperDomElement = document.createElement('DIV');
	this.graphWrapperDomElement.className = 'graph_wrapper';
	this.graphWrapperDomElement.style.height = this.template.graphHeight;

	this.graphWrapperDomElement.innerHTML =
		'<table>' +
			'<tbody>' +
				'<tr>' +
					'<td class="graph_title"><span title="'+this.altText+'">'+this.shortName+'</span><span class="webix_icon mdi mdi-cogs" onclick="showGraphControlPanel(\''+this.fullName+'\');"></span></td>' +
					'<td rowspan="2">' +
						'<div class="graph"></div>' +
					'</td>' +
				'</tr>' +
				'<tr>' +
					'<td class="legend"><div></div></td>' +
				'</tr>' +
			'</tbody>' +
		'</table>';

	document.getElementById('graphs').appendChild(this.graphWrapperDomElement);

	// Grab references to the legend & graph elements so they can be used later.
	this.legendDomElement = this.graphWrapperDomElement.querySelector('.legend > div');
	this.graphDomElement = this.graphWrapperDomElement.querySelector('.graph');//('.graph .innerLeft');
	this.rightGraphDomElement = false;//this.graphWrapperDomElement.querySelector('.graph .innerRight');

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

	// Instantiate the dygraph if it is configured to appear by default
	if (this.template['show'] === true) {
		this.instantiateDygraph();
	} else {
		this.hideDOMElements();
	}

	// Add this graph to the plot control
	this.addSelfToPlotControl();

};

// Remove the graph from the interface.
Graph.prototype.hide = function() {

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

	// Trigger resize of all graphs (resolves a dygraphs sizing bug)
	this.file.triggerResizeAllGraphs();

	// Resynchronize the graphs now that removal is complete.
	this.file.synchronizeGraphs()

};

// Hide the graph & legend divs
Graph.prototype.hideDOMElements = function() {
	this.graphWrapperDomElement.style.display = 'none';
};

// Instantiates a dygraph on the UI
Graph.prototype.instantiateDygraph = function() {

	// Determine if there is already a graph showing. If so, adopt its x-range.
	// If not, use global x extremes.
	let timeWindow = this.file.getOutermostZoomWindow();
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
		for (let s of this.members) {
			if (this.template.hasOwnProperty('range')) {
				if (yAxisRange[0] === null || yAxisRange[0] > this.template.range[0]) {
					yAxisRange[0] = this.template.range[0];
				}
				if (yAxisRange[1] === null || yAxisRange[1] < this.template.range[1]) {
					yAxisRange[1] = this.template.range[1];
				}
			}
		}
	}
	else if (this.template.hasOwnProperty('range')) {
		yAxisRange = this.template.range;
	}

	// Create the dygraph
	this.dygraphInstance = new Dygraph(this.graphDomElement, this.file.fileData.series[this.fullName].data, {
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
		clickCallback: handleClick,
		colors: [this.template.lineColor],//'#5253FF'],
		dateWindow: timeWindow,
		// drawPoints: true,
		gridLineColor: this.template.gridColor,
		interactionModel: {
			'mousedown': handleMouseDown.bind(this),
			'mousemove': handleMouseMove.bind(this),
			'mouseup': handleMouseUp.bind(this),
			'dblclick': handleDoubleClick.bind(this),
			'mousewheel': handleMouseWheel.bind(this)
		},
		labels: this.file.fileData.series[this.fullName].labels,
		labelsDiv: this.legendDomElement,
		plotter: handlePlotting.bind(this),
		/*series: {
		  'Min': { plotter: handlePlotting },
		  'Max': { plotter: handlePlotting }
		},*/
		//title: this.series,
		underlayCallback: handleUnderlayRedraw.bind(this),
		valueRange: yAxisRange
	});

	if (this.rightGraphDomElement) {

		this.rightDygraphInstance = new Dygraph(this.rightGraphDomElement, this.file.fileData.series[this.fullName].data, {
			axes: {
				x: {
					pixelsPerLabel: 70,
					independentTicks: true
				},
				y: {
					// pixelsPerLabel: 14,
					pixelsPerLabel: 14,
					independentTicks: true,
					drawAxis: false
				}
			},
			//clickCallback: handleClick,
			colors: [this.template.lineColor],//'#5253FF'],
			dateWindow: this.file.getOutermostZoomWindow('lead'),
			// drawPoints: true,
			gridLineColor: this.template.gridColor,
			/*interactionModel: {
				'mousedown': handleMouseDown.bind(this),
				'mousemove': handleMouseMove.bind(this),
				'mouseup': handleMouseUp.bind(this),
				'dblclick': handleDoubleClick.bind(this),
				'mousewheel': handleMouseWheel.bind(this)
			},*/
			labels: this.file.fileData.series[this.fullName].labels,
			labelsDiv: this.legendDomElement,
			plotter: handlePlotting.bind(this),
			/*series: {
			  'Min': { plotter: handlePlotting },
			  'Max': { plotter: handlePlotting }
			},*/
			//title: this.series,
			//underlayCallback: handleUnderlayRedraw.bind(this),
			valueRange: yAxisRange
		});

	}

};

// Returns a boolean indicating whether this graph is currently showing.
Graph.prototype.isShowing = function() {
	return this.dygraphInstance !== null;
};

// Replace the data attached to the dygraph. Block redraw of the dygraph by
// passing in true for the block_redraw optional parameter.
Graph.prototype.replacePlottedData = function(data, block_redraw=false) {
	this.dygraphInstance.updateOptions({
		file: data
	}, block_redraw);
};

// Toggle the graph to show.
Graph.prototype.show = function() {

	// Unsynchronize the graphs temporarily for the duration of the post-load addition.
	this.file.unsynchronizeGraphs();

	// Show the graph & legend divs
	this.showDOMElements();

	// Instantiate the dygraph
	this.instantiateDygraph();

	// Trigger resize of all graphs (resolves a dygraphs sizing bug)
	this.file.triggerResizeAllGraphs();

	// Resynchronize the graphs now that the addition is complete.
	this.file.synchronizeGraphs();

	// Run pre-defined pattern detection jobs (async).
	// NOTE: This function takes either string or array as parameter, so it
	// works for a single or group series graph.
	if (this.isGroup) {
		this.file.runPatternDetectionJobsForSeries(this.members);
	} else {
		this.file.runPatternDetectionJobsForSeries(this.fullName);
	}

	// Update the data from the backend for the new series only
	this.updateCurrentViewData()

};

// Show the graph & legend divs for the named series.
Graph.prototype.showDOMElements = function() {
	this.graphWrapperDomElement.style.display = 'block';
};

// Triggers a resize of the dygraph instance, if showing.
Graph.prototype.triggerResize = function() {
	if (this.isShowing()) {
		this.dygraphInstance.resize();
	}
};

// Request and update data for the current view of the graph.
// NOTE: There is an identically-named function on both File and Graph classes,
// the former which updates data for all graphs currently appearing and the
// latter which updates the data only for the single graph.
Graph.prototype.updateCurrentViewData = function() {

	// Get the x-axis range
	let xRange = this.dygraphInstance.xAxisRange();

	// Assemble the series ID(s) for which we will request updated data.
	let series = this.isGroup ? this.members : [this.fullName];

	// Request the updated view data from the backend.
	requestHandler.requestSeriesRangedData(this.file.parentProject.id, this.file.id, series, xRange[0]/1000-this.file.fileData.baseTime, xRange[1]/1000-this.file.fileData.baseTime, this.file.getPostloadDataUpdateHandler());

};
