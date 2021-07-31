/*
Supervisor class manages the process of loading project files, labeling functions, and resultant annotations
*/

function Supervisor(payload) {
    this.project_id = payload['project_id']
    this.project_name = payload['project_name']

	/*
	Holds the min [0] and max [1] x-value across all graphs currently displayed.
	This is calculated in the convertToDateObjsAndUpdateExtremes() function. The
	values should hold milliseconds since epoch, as this is the format specified
	for options.dateWindow, though the values will intermediately be instances
	of the Date object while the extremes are being calculated. This array may
	be passed into the options.dateWindow parameter for a dygraph.
	*/
	this.globalXExtremes = [];

	// Load the project config
	this.template = templateSystem.getProjectTemplate(this.project_id);

	// Holds the dom element of the instantiated legend
	this.legendDomElement = null;

	// Holds the dom element of the instantiated graph
	this.graphDomElement = null;

	requestHandler.requestInitialSupervisorPayload(this.project_id, function (data) {
		let lfSelector = document.getElementById('lfSelector');
		for (let lfTitle of data.labeling_function_titles) {
			let nextOpt = document.createElement('option');
			nextOpt.innerHTML = lfTitle;
			lfSelector.appendChild(nextOpt);
		}
		let voteSelector = document.getElementById('voteSelector');
		for (let possibleVote of data.labeling_function_possible_votes) {
			let nextOpt = document.createElement('option');
			nextOpt.innerHTML = possibleVote;
			voteSelector.appendChild(nextOpt);
		}
		this.buildLabelingFunctionTable(data.labeling_function_titles);
		this.initModel(data);
	}.bind(this));
}

Supervisor.prototype.initModel = function(data) {
    this.sync = null;

	//Holds the labeling function ids that we'd like to render for visible patients
	this.activeLFs = [];

	this.active_lf_colors = {
		'blue': false,
		'purple': false,
		'pink': false,
		'red': false,
		'orange': false,
		'yellow': false,
		'green': false,
		'teal': false,
		'cyan': false 
	};

	//Holds the labeling function titles to their associated colors (more succinct than full title to render)
	this.lfTitleToColor = {};

	//Maps lf title to idx in votes array
	this.lfTitleToIdx = {};

	// Prepare data received from the backend and attach to class instance
	// new prepareData method needed
	this.projectData = this.prepareData(data, data.baseTime || 0);
	this.lfVotes = this.projectData.labeling_function_votes;
	this.domElementObjs = new Array(this.projectData.files.length);
	this.dygraphs = new Array(this.projectData.files.length);

	for (const [idx, lfTitle] of this.projectData.labeling_function_titles.entries()) {
		this.lfTitleToIdx[lfTitle] = idx;

	}
	window.requestAnimationFrame(function() {
		// // Attach & render file metadata
		// this.metadata = data.metadata;
		// this.renderMetadata();

		// ----- Below is not applicable (?) -----
		// // Instantiate event graphs
		// this.renderEventGraphs();
		this.projectData.labeling_function_possible_votes
		for (let i = 0; i < this.projectData.files.length; i++) {
			this.domElementObjs[i] = this.buildGraph(this.projectData.files[i][1]);
			let series = Object.values(this.projectData.series[i])[0];
			let events = this.projectData.events[i];
			let metadata = this.projectData.metadata[i];

			this.dygraphs[i] = this.createDygraph(this.domElementObjs[i], series, events);
		}

		// for (let s of Object.keys(this.projectData.series)) {
		// 	this.graphs[s] = new Graph(s, this);
		// }

		// With all graphs instantiated, trigger resize of all graphs
		// (this resolves a dygraphs bug where the first few graphs drawn
		// are wider than the rest due to a scrollbar which initiallly is
		// not needed and, later, is).
		for (let dygraphInstance of this.dygraphs) {
			dygraphInstance.resize();
		}

		// Synchronize the graphs
		if (this.dygraphs.length < 2) {
			return;
		}
		else {
			this.sync = Dygraph.synchronize(this.dygraphs, {
				range: true,
				selection: true,
				zoom: true
			});
		}
	}.bind(this));
}

Supervisor.prototype.clearModel = function() {
	for (let domElementObj of this.domElementObjs) {
		domElementObj.graphDomElement.remove();
		domElementObj.graphWrapperDomElement.remove();
	}
	for (let dygraphInstance of this.dygraphs) {
		dygraphInstance.destroy();
	}
	// let parents = [document.getElementById('labelingFunctionTable').getElementsByTagName('tbody')[0], document.getElementById('lfSelector'), document.getElementById('voteSelector')];
	// for (let parent of parents) {
	// 	while (parent.firstChild) {
	// 		parent.removeChild(parent.firstChild);
	// 	}
	// }
}

Supervisor.prototype.applyQuery = function() {
	let elements = document.getElementById('supervisorQueryForm').elements;
	let random = false;
	let lfSelection;
	let voteSelection;
	for (let elem of elements) {
		if (elem.id==='randomQuery') {
			random = elem.checked;
		} else if (elem.id === 'lfSelector') {
			lfSelection = elem.value;
		} else if (elem.id === 'voteSelector') {
			voteSelection = elem.value;
		}
	}
	let self = this;
	let queryResponse = requestHandler.requestSupervisorSeriesByQuery(this.project_id, {
         'randomFiles': random,
         'categorical': voteSelection,
         'labelingFunction': lfSelection,
         'amount': 5,
        // 'sortByConfidence': bool,
        // 'patientSearchString': str,
	}, function (data) {
		self.clearModel();
		self.initModel(data);
	});

	console.log("sent off query");
}

Supervisor.prototype.buildLabelingFunctionTable = function(labelingFunctionTitles) {
	for (let lfTitle of labelingFunctionTitles) {
		let lfTitleDomElement = document.createElement('tr');
		lfTitleDomElement.innerHTML = 
			'<td >' + lfTitle + '</td>' + 
			'<td >' +
				'<input class="btn" type="checkbox" id="' + lfTitle + '" value = "' + lfTitle + '" onclick="globalStateManager.currentSupervisor.onClick(`'+lfTitle+'`)"> </td>';
		lfTitleDomElement.style.fontSize = 'small';
		document.getElementById('labelingFunctionTable').getElementsByTagName('tbody')[0].appendChild(lfTitleDomElement);
	}
}

Supervisor.prototype.onClick = function(lfTitle) {
	const divInQuestion = document.getElementById(lfTitle);
	if (divInQuestion.checked) {
		this.activeLFs.push(lfTitle);
		for (const [color, alreadyInUse] of Object.entries(this.active_lf_colors)) {
			if (!alreadyInUse) {
				this.active_lf_colors[color] = true;
				this.lfTitleToColor[lfTitle] = color;
				divInQuestion.parentElement.parentElement.style.backgroundColor = color;
				break;
			}
		}
	}
	else {
		const isLF = (elem) => elem === lfTitle;
		let lfIndex = this.activeLFs.findIndex(isLF);
		this.activeLFs.splice(lfIndex, lfIndex+1);
		this.active_lf_colors[this.lfTitleToColor[lfTitle]] = false;
		divInQuestion.parentElement.parentElement.style.backgroundColor = '#888';
	}

	for (const [seriesIdx, domElementObj] of this.domElementObjs.entries()) {
		let correspondingVotesSection = domElementObj.graphWrapperDomElement.getElementsByClassName('labelingFunctionVotes')[0];
		correspondingVotesSection.innerHTML = '';
		// let correspondingVotesSection = votesSection[0];
		for (const activeLF of this.activeLFs) {
			let lfDiv = document.createElement('div');
			lfDiv.style.backgroundColor = this.lfTitleToColor[activeLF];
			lfDiv.style.fontSize = 'small';
			lfDiv.style.color = 'white'
			lfDiv.innerHTML = this.lfVotes[seriesIdx][this.lfTitleToIdx[activeLF]];
			correspondingVotesSection.appendChild(lfDiv);
		}
	}

	// document.getElementById('labelingFunctionTable').getElementsBy
}

Supervisor.prototype.getLFColorByTitle = function(lfTitle) {
	this.lfTitleToColor[lfTitle];
}

Supervisor.prototype.buildGraph = function(fileName) {

	// Create the graph wrapper dom element
	let graphWrapperDomElement = document.createElement('DIV');
	graphWrapperDomElement.className = 'graph_wrapper';
	graphWrapperDomElement.style.height = this.template.graphHeight;

	graphWrapperDomElement.innerHTML =
		'<table class="table">' +
			'<col style="width:10%">' +
			'<col style="width:10%">' +
			'<col style="width:80%">' +
			'<tbody id="seriesTableBody">' +
				'<tr>' +
					'<td rowspan="2" class="labelingFunctionVotes" />' +
					'<td scope="row" class="graph_title"><span title="'+this.altText+'">'+fileName+'</span><span class="webix_icon mdi mdi-cogs" onclick="showGraphControlPanel(\''+fileName+'\');"></span></td>' +
					'<td rowspan="2">' +
						'<div class="graph"></div>' +
					'</td>' +
				'</tr>' +
				'<tr>' +
					'<td class="legend"><div></div></td>' +
				'</tr>' +
			'</tbody>' +
		'</table>';

	document.getElementById('supervisorGraphs').appendChild(graphWrapperDomElement);

	// Grab references to the legend & graph elements so they can be used later.
	let legendDomElement = graphWrapperDomElement.querySelector('.legend > div');
	let graphDomElement = graphWrapperDomElement.querySelector('.graph');//('.graph .innerLeft');
	let rightGraphDomElement = false;//this.graphWrapperDomElement.querySelector('.graph .innerRight');

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
	// poorly). --> REVISIT THIS
	$(graphDomElement).data('graphClassInstance', this);

	// // Instantiate the dygraph if it is configured to appear by default
	// if (this.template['show'] === true) {
	// 	this.instantiateDygraph();
	// } else {
	// 	this.hideDOMElements();
	// }

    //TODO(roman): plot control addition
	// // Add this graph to the plot control
	// this.addSelfToPlotControl();

    return {'graphWrapperDomElement': graphWrapperDomElement,
        'graphDomElement': graphDomElement,
        'legendDomElement': legendDomElement, 
        'rightGraphDomElement': rightGraphDomElement}
};

Supervisor.prototype.createDygraph = function(graphDomElementObj, series, eventData) {
    let timeWindow = this.globalXExtremes;
    let yAxisRange = [null, null];
    if (this.template.hasOwnProperty('range')) {
        yAxisRange = this.template.range;
    }
    let seriesData = new Array(series.data.length);
    // let initialValue;
    for (let i = 0; i < seriesData.length; i++) {
		// seriesData[i] = [i/*new Date(series.data[i][0]*1000 % 1) - initialValue*/, series.data[i][series.data[i].length -1]];
		seriesData[i] = [series.data[i][0]/*new Date(series.data[i][0]*1000 % 1) - initialValue*/, series.data[i][series.data[i].length -1]];
    }
    let dygraphInstance = new Dygraph(graphDomElementObj.graphDomElement, seriesData, {
		// axes: {
		// 	x: {
		// 		pixelsPerLabel: 70,
		// 		independentTicks: true
		// 	},
		// 	y: {
		// 		pixelsPerLabel: 14,
		// 		independentTicks: true
		// 	}
		// },
		clickCallback: handleClick,
		// colors: [this.template.lineColor],//'#5253FF'],
        colors: ['#5253FF'],
		// dateWindow: timeWindow,
		drawPoints: true,
		// gridLineColor: this.template.gridColor,
		// interactionModel: {
		// 	'mousedown': handleMouseDown.bind(this),
		// 	'mousemove': handleMouseMove.bind(this),
		// 	'mouseup': handleMouseUp.bind(this),
		// 	'dblclick': handleDoubleClick.bind(this),
		// 	'mousewheel': handleMouseWheel.bind(this)
		// },
		labels: [series.labels[0], series.labels[3]],
		labelsDiv: graphDomElementObj.legendDomElement,
		// plotter: handlePlotting.bind(this),
		/*series: {
		  'Min': { plotter: handlePlotting },
		  'Max': { plotter: handlePlotting }
		},*/
		//title: this.series,
		// underlayCallback: handleUnderlayRedraw.bind(this),
		// valueRange: yAxisRange

    });

    return dygraphInstance;
}

// Prepares & returns data by converting times to Date objects and calculating
// x-axis extremes across all data.
Supervisor.prototype.prepareData = function(data, baseTime) {

	let t0 = performance.now();

    for (let fIdx = 0; fIdx < data.files.length; fIdx++) {
        // let f_id = f_info[0];

        // Get array of series
        let series = data.series[fIdx];
        let seriesIndices = Object.keys(series);

        // Process series data
        if (seriesIndices.length > 0) {

            // Prime the graph extremes if new. Otherwise, convert the existing extremes
            // to date objects.
            if (this.globalXExtremes.length === 0) {
                this.globalXExtremes[0] = new Date((series[seriesIndices[0]].data[0][0] + baseTime) * 1000);
                this.globalXExtremes[1] = new Date((series[seriesIndices[0]].data[0][0] + baseTime) * 1000);
            } else {
                this.globalXExtremes[0] = new Date(this.globalXExtremes[0].valueOf());
                this.globalXExtremes[1] = new Date(this.globalXExtremes[1].valueOf());
            }

            // Process series data
            for (let s of seriesIndices) {

                // If this series has no data, continue
                if (series[s].data.length < 1) {
                    continue;
                }

                convertFirstColumnToDate(series[s].data, baseTime);

                // Update global x-minimum if warranted
                if (series[s].data[0][0] < this.globalXExtremes[0]) {
                    this.globalXExtremes[0] = series[s].data[0][0];
                }

                // Update global x-maximumm if warranted
                if (series[s].data[series[s].data.length - 1][0] > this.globalXExtremes[1]) {
                    this.globalXExtremes[1] = series[s].data[series[s].data.length - 1][0];
                }

            }

        }

        // Process event data
        if (false && data.hasOwnProperty('events')) {

            // Get array of event series
            let events = Object.keys(data.events[f_id]);

            // Process event data
            for (let s of events) {

                // If this series has no data, continue
                if (data.events[f_id][s].length < 1) {
                    continue;
                }

                for (let i in data.events[f_id][s]) {

                    // Convert the ISO8601-format string into a Date object.
                    data.events[f_id][s][i][0] = new Date((data.events[f_id][s][i][0] + baseTime) * 1000);

                }

                // Update global x-minimum if warranted
                if (data.events[f_id][s][0][0] < this.globalXExtremes[0]) {
                    this.globalXExtremes[0] = data.events[f_id][s][0][0];
                }

                // Update global x-maximumm if warranted
                if (data.events[f_id][s][data.events[f_id][s].length - 1][0] > this.globalXExtremes[1]) {
                    this.globalXExtremes[1] = data.events[f_id][s][data.events[f_id][s].length - 1][0];
                }

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
	globalAppConfig.performance && tt > globalAppConfig.performanceReportingThresholdGeneral && console.log("File.prepareData() took " + Math.round(tt) + "ms.");

	return data;

};

Supervisor.prototype.uploadFile = function(fileElementId) {
	let filePayload = document.getElementById(fileElementId).files[0];
	requestHandler.createSupervisorPrecomputer(this.project_id, filePayload, function() {
		console.log("Successfully uploaded file with id: " + fileElementId);
	})
}