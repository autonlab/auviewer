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
	this.globalYExtremes = [0, 0];
	this.seriesOnPage = 4;
	this.activeGraphs = [...Array(this.seriesOnPage).keys()];

	// Load the project config
	this.template = templateSystem.getProjectTemplate(this.project_id);

	// Holds the dom element of the instantiated legend
	this.legendDomElement = null;

	// Holds the dom element of the instantiated graph
	this.graphDomElement = null;

	this.timeWindow = 60 *60*1000;
	let self=this;
	document.getElementById('recalculateVotes').setAttribute('disabled', true);
	document.getElementById('30_min').onclick = function () {self.setTimeWindow(30 *60*1000);};
	document.getElementById('60_min').onclick = function () {self.setTimeWindow(60 *60*1000);};
	document.getElementById('120_min').onclick = function () {self.setTimeWindow(120 *60*1000);};

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
	this.lfVotesByTimeSegment = null;
	this.timeSegmentEndIndices = null;
	this.domElementObjs = new Array(this.projectData.files.length);
	this.dygraphs = new Array(this.projectData.files.length);

	this.priorQuerySettings = {
		'random': false,
		'lfSelector': this.projectData.labeling_function_titles[0],
		'voteSelector': this.projectData.labeling_function_votes[0]
	};

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

		this.graphsTableDomElement = document.createElement('table');
		this.graphsTableDomElement.className = 'supervisor_table';

		this.graphsTableDomElement.innerHTML =
				// '<col style="width:10%">' +
				'<col style="width:15%">' +
				'<col style="width:85%">' +
				'<thead>' +
					'<tr>' +
						// '<th>LF Votes</th>' +
						'<th></th>' +
						'<th></th>' +
					'</tr>' +
				'</thead>' +
				'<tbody id="seriesTableBody">' +
				'</tbody>';
		document.getElementById('supervisorGraphs').appendChild(this.graphsTableDomElement);
		let graphsTableBody = document.getElementById('seriesTableBody');

		for (let i = 0; i < this.projectData.files.length; i++) {
			let filename = this.projectData.files[i][1];
			this.domElementObjs[i] = this.buildGraph(filename);
			graphsTableBody.appendChild(this.domElementObjs[i].graphWrapperDomElement);


			let series = Object.values(this.projectData.series[i])[0];
			let events = this.projectData.events[i];
			let metadata = this.projectData.metadata[i];

			this.dygraphs[i] = this.createDygraph(this.domElementObjs[i], series, events);
			let self=this;
			document.getElementById('left_'+filename).onclick = function() { self.pan(self.dygraphs[i], -1); };
			document.getElementById('right_'+filename).onclick = function() { self.pan(self.dygraphs[i], +1); };
		}

		this.datatable = $('.supervisor_table').DataTable({
			"lengthChange": false,
			"ordering": false,
			"searching": false,
			"pageLength": this.seriesOnPage
		});
		this.activePage = 0;
		let self=this;
		this.datatable.on( 'draw', function() {
			self.regenerateGraphs(self.datatable.page());
		})
		// for (let s of Object.keys(this.projectData.series)) {
		// 	this.graphs[s] = new Graph(s, this);
		// }

		// With all graphs instantiated, trigger resize of all graphs
		// (this resolves a dygraphs bug where the first few graphs drawn
		// are wider than the rest due to a scrollbar which initiallly is
		// not needed and, later, is).
		this.regenerateGraphs(0);
		for (let dygraphInstance of this.dygraphs) {
			if (dygraphInstance) {
				dygraphInstance.resize();
			}
		}

		// Synchronize the graphs
		if (this.dygraphs.length < 2) {
			return;
		}
		else {
			// this.sync = Dygraph.synchronize(this.dygraphs, {
			// 	range: true,
			// 	selection: true,
			// 	zoom: true
			// });
		}
	}.bind(this));
}

Supervisor.prototype.clearModel = function() {
	for (let domElementObj of this.domElementObjs) {
		domElementObj.graphDomElement.remove();
		domElementObj.graphWrapperDomElement.remove();
	}
	this.datatable.destroy();
	this.graphsTableDomElement.remove();
	for (let dygraphInstance of this.dygraphs) {
		if (dygraphInstance) {
			dygraphInstance.destroy();
		}
	}
	// let parents = [document.getElementById('labelingFunctionTable').getElementsByTagName('tbody')[0], document.getElementById('lfSelector'), document.getElementById('voteSelector')];
	// for (let parent of parents) {
	// 	while (parent.firstChild) {
	// 		parent.removeChild(parent.firstChild);
	// 	}
	// }
}

Supervisor.prototype.regenerateGraphFor = function(filename, idx, curPageIdx) {
	let graphsTableBody = document.getElementById('seriesTableBody');
	let graphWrapperDomElement = document.createElement('tr');
	graphWrapperDomElement.className = 'graph_row_wrapper';
	graphWrapperDomElement.style.height = this.template.graphHeight;

	let leftId = 'left_' + filename;
	let rightId = 'right_' + filename;
	graphWrapperDomElement.innerHTML = 
		// '<td >' +
		// 	'<div class="labelingFunctionVotes"></div>' +
		// '</td>' +
		'<td class="graph_title"><span title="'+this.altText+'">'+filename+'</span>' + 
			'<span class="webix_icon mdi mdi-cogs"></span>' + 
			'<div class="btn-group" role="group" aria-label="Time series navigation">' +
				'<button type="button" id="'+leftId+'" class="btn btn-primary"><span class="webix_icon wxi-angle-left"></span></button>' +
				'<button type="button" id="'+rightId+'" class="btn btn-primary"><span class="webix_icon wxi-angle-right"></span></button>' +
			'</div>' +
		'</td>' +
		'<td >' +
			'<div class="graph"></div>' +
		'</td>';

	this.dygraphs[idx].destroy();

	let graphDomElement = graphWrapperDomElement.querySelector('.graph');//('.graph .innerLeft');
	$(graphDomElement).data('graphClassInstance', this);
	let graphDomElementObj = {
		graphWrapperDomElement: graphWrapperDomElement,
		graphDomElement: graphDomElement
	};
	graphsTableBody.childNodes[curPageIdx].replaceWith(graphWrapperDomElement);
	this.domElementObjs[idx] = graphDomElementObj;
	let series = Object.values(this.projectData.series[idx])[0];
	let events = this.projectData.events[idx];
	this.dygraphs[idx] = this.createDygraph(this.domElementObjs[idx], series, events);
	let self=this;
	document.getElementById('left_'+filename).onclick = function() { self.pan(self.dygraphs[idx], -1); };
	document.getElementById('right_'+filename).onclick = function() { self.pan(self.dygraphs[idx], +1); };
}

Supervisor.prototype.regenerateGraphs = function(pageNum) {
	let startIdx = pageNum * this.seriesOnPage;
	let endIdx = Math.min((pageNum + 1) * this.seriesOnPage, this.projectData.files.length);
	this.globalYExtremes[1] = 0;
	this.activeGraphs = new Array(this.seriesOnPage);
	for (let idx = startIdx; idx < endIdx; idx++) {
		let series = Object.values(this.projectData.series[idx])[0].data;
		for (let i = 0; i < series.length; i++) {
			let yVal = series[i][series[i].length -1];
			if (yVal > this.globalYExtremes[1]) {
				this.globalYExtremes[1] = yVal;
			}
		}
	}
	let j = 0;
	for (let i = startIdx; i < endIdx; i++) {
		this.activeGraphs[j] = i;
		this.regenerateGraphFor(this.projectData.files[i][1], i, j);
		j++;
	}

	if (this.timeSegmentEndIndices) {
		this.shadeTimeSegmentsWithVotes();
	}
	this.setTimeWindow(this.timeWindow, forceAdjustment=true);
}

Supervisor.prototype.setTimeWindow = function(newTimeWindow, forceAdjustment=false) {
	if (forceAdjustment || (newTimeWindow !== this.timeWindow)) {
		document.getElementById('recalculateVotes').removeAttribute('disabled'); // since we have a new time slice, it should now be allowed to recalculate
		this.timeWindow = newTimeWindow;
		for (let graphIdx of this.activeGraphs) {
			let curGraph = this.dygraphs[graphIdx];
			let curRange = curGraph.xAxisRange();
			let desiredRange = [curRange[0], curRange[0] + this.timeWindow];
			this.animate(curGraph, desiredRange);
		}
	}
}
// following three functions copied from third example found [here](https://dygraphs.com/options.html#dateWindow)
Supervisor.prototype.pan = function(graph, dir) {
	let curRange = graph.xAxisRange();
	let scale = curRange[1] - curRange[0];
	let amount = scale * dir;
	let desiredRange = [curRange[0] + amount, curRange[1] + amount];
	this.animate(graph, desiredRange);
}

Supervisor.prototype.animate = function(graph, desiredRange, maxSteps=20) {
	let self=this;
	setTimeout(function() { self.approachRange(graph, desiredRange, maxSteps);}, 50);
}

Supervisor.prototype.approachRange = function(graph, desiredRange, maxSteps) {
	let curRange = graph.xAxisRange();
	if (maxSteps <= 0 || (Math.abs(desiredRange[1] - curRange[1]) < 60 &&
		Math.abs(desiredRange[0] - curRange[0]) < 60)) {
		graph.updateOptions({dateWindow: desiredRange});
	} else {
		let newRange = [.5 * (desiredRange[0] + curRange[0]),
						.5 * (desiredRange[1] + curRange[1])];
		graph.updateOptions({dateWindow: newRange});
		this.animate(graph, desiredRange, maxSteps-1);
	}
}

Supervisor.prototype.recalculateVotes = function () {
	// ask backend to segment all series' and vote on subsequent segments, then return them all
	let self = this;
	requestHandler.requestSupervisorUpdatedTimeSegmentPayload(this.project_id, this.timeWindow, function(data) {
		self.lfVotesByTimeSegment = data.labeling_function_votes;
		self.timeSegmentEndIndices = data.time_segment_end_indices;
		self.shadeTimeSegmentsWithVotes();
		// turn off loader now that we've received data
		$('#loadMe').modal("hide");
	});
	// set loader on
	$('#loadMe').modal({
		keyboard: false,
		backdrop: "static",
		show: true
	});
}

Supervisor.prototype.shadeTimeSegmentsWithVotes = function() {
	for (let activeGraphIdx of this.activeGraphs) {
		this.shadeGraph(activeGraphIdx);
	}
}

Supervisor.prototype.shadeGraph = function(graphIdx) {
	let graph = this.dygraphs[graphIdx];
	let endIndices = this.timeSegmentEndIndices[graphIdx];
	let series = Object.values(this.projectData.series[graphIdx])[0].data;
	let self = this;
	graph.updateOptions({
		underlayCallback: function(canvas, area, g) {
			let startIdx = 0;
			let alternating = false;
			for (let endIdx of endIndices) {
				if (startIdx === endIdx) {
					break;
				}
				// get start and end timestamps
				let start = series[startIdx][0];
				let end = series[endIdx-1][0];
				let bottomLeft = g.toDomCoords(start, -20);
				let topRight = g.toDomCoords(end, +20);
				let left = bottomLeft[0];
				let right = topRight[0];

				if (alternating) {
					canvas.fillStyle = "rgba(255, 255, 102, 1.0)";
				} else {
					canvas.fillStyle = "rgba(102, 255, 255, 1.0)";
				}
				canvas.fillRect(left, area.y, right-left, area.h);
				startIdx = endIdx;
				alternating = !alternating;
			}
		},
		legendFormatter: function(data) {
			return data.series.map(function (series) {
				return series.dashHTML + ' ' + series.label + ' - ' + series.yHTML
			}).join('<br>') +
				'<br>' + 
				self.activeLFs.map(function (lfTitle) {
					let lfVote = self.getVoteForGraphAndPoint(graphIdx, data.x, lfTitle);
					return lfTitle + ' - ' + lfVote; 
				}).join('<br>');
		}
	});
	console.log('finished shading idx: ' + graphIdx + '!');
}

Supervisor.prototype.getVoteForGraphAndPoint = function(graphIdx, xPoint, lfTitle) {
	let startIdx = 0;
	let bucketIdx = 0;
	let series = Object.values(this.projectData.series[graphIdx])[0].data;
	xPoint = new Date(xPoint);
	for (let endIdx of this.timeSegmentEndIndices[graphIdx]) {
		// get start and end timestamps
		let start = series[startIdx][0];
		let end = series[endIdx-1][0];
		if (start <= xPoint && xPoint <= end) {
			break;
		}
		bucketIdx++;
	}
	let lfIdx = this.lfTitleToIdx[lfTitle];
	return this.lfVotesByTimeSegment[graphIdx][bucketIdx][lfIdx];
}

Supervisor.prototype.onQueryClick = function() {
	let elements = document.getElementById('supervisorQueryForm').elements;
	let randomChanged = false;
	let lfChanged = false;
	for (let elem of elements) {
		if (elem.id==='randomQuery') {
			if (this.priorQuerySettings.random !== elem.checked) {
				randomChanged = true;
			}
			this.priorQuerySettings.random = elem.checked;
		} else if (elem.id === 'lfSelector') {
			if (this.priorQuerySettings.lfSelector !== elem.value) {
				lfChanged = true;
			}
			this.priorQuerySettings.lfSelector = elem.value;
		} else if (elem.id === 'voteSelector') {
			if (this.priorQuerySettings.voteSelector !== elem.value) {
				lfChanged = true;
			}
			this.priorQuerySettings.voteSelector = elem.value;
		}
	}
	if (randomChanged) {
		let randomChecked = document.getElementById('randomQuery').checked;
		if (randomChecked) {
			document.getElementById('voteSelector').setAttribute("disabled", true);
			document.getElementById('lfSelector').setAttribute("disabled", true);
		} else {
			document.getElementById('voteSelector').removeAttribute("disabled");
			document.getElementById('lfSelector').removeAttribute("disabled");
		}
	}
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
	requestHandler.requestSupervisorSeriesByQuery(this.project_id, {
         'randomFiles': random,
         'categorical': voteSelection,
         'labelingFunction': lfSelection,
        //  'amount': 5,
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

	// for (const [seriesIdx, domElementObj] of this.domElementObjs.entries()) {
	// 	let correspondingVotesSection = domElementObj.graphWrapperDomElement.getElementsByClassName('labelingFunctionVotes')[0];
	// 	correspondingVotesSection.innerHTML = '';
	// 	// let correspondingVotesSection = votesSection[0];
	// 	for (const activeLF of this.activeLFs) {
	// 		let lfDiv = document.createElement('div');
	// 		lfDiv.style.backgroundColor = this.lfTitleToColor[activeLF];
	// 		lfDiv.style.fontSize = 'small';
	// 		lfDiv.style.color = 'white'
	// 		lfDiv.innerHTML = this.lfVotes[seriesIdx][this.lfTitleToIdx[activeLF]];
	// 		correspondingVotesSection.appendChild(lfDiv);
	// 	}
	// }

	// document.getElementById('labelingFunctionTable').getElementsBy
}

Supervisor.prototype.getLFColorByTitle = function(lfTitle) {
	this.lfTitleToColor[lfTitle];
}

Supervisor.prototype.buildGraph = function(fileName) {

	// Create the graph wrapper dom element
	let graphWrapperDomElement = document.createElement('tr');
	graphWrapperDomElement.className = 'graph_row_wrapper';
	graphWrapperDomElement.style.height = this.template.graphHeight;
	let leftId = 'left_' + fileName;
	let rightId = 'right_' + fileName;
	graphWrapperDomElement.innerHTML =
		// '<td >' +
		// 	'<div class="labelingFunctionVotes"></div>' +
		// '</td>' +
		'<td class="graph_title"><span title="'+this.altText+'">'+fileName+'</span>' + 
			'<span class="webix_icon mdi mdi-cogs"></span>' + 
			'<div class="btn-group" role="group" aria-label="Time series navigation">' +
				'<button type="button" id="'+leftId+'" class="btn btn-primary"><span class="webix_icon wxi-angle-left"></span></button>' +
				'<button type="button" id="'+rightId+'" class="btn btn-primary"><span class="webix_icon wxi-angle-right"></span></button>' +
			'</div>' +
		'</td>' +
		'<td >' +
			'<div class="graph"></div>' +
		'</td>';


	// Grab references to the legend & graph elements so they can be used later.
	let graphDomElement = graphWrapperDomElement.querySelector('.graph');//('.graph .innerLeft');
	let rightGraphDomElement = false;//this.graphWrapperDomElement.querySelector('.graph .innerRight');

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
        'rightGraphDomElement': rightGraphDomElement}
};

Supervisor.prototype.createDygraph = function(graphDomElementObj, series, eventData) {
    let timeWindow = this.globalXExtremes;
    let yAxisRange = this.globalYExtremes;
    if (this.template.hasOwnProperty('range')) {
        yAxisRange = this.template.range;
    }
    let seriesData = new Array(series.data.length);
    // let initialValue;
    for (let i = 0; i < seriesData.length; i++) {
		let yVal = series.data[i][series.data[i].length -1];
		// seriesData[i] = [i/*new Date(series.data[i][0]*1000 % 1) - initialValue*/, series.data[i][series.data[i].length -1]];
		seriesData[i] = [series.data[i][0]/*new Date(series.data[i][0]*1000 % 1) - initialValue*/, yVal];
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
		legend: 'follow',
		ylabel: 'aEEG',
		// plotter: handlePlotting.bind(this),
		/*series: {
		  'Min': { plotter: handlePlotting },
		  'Max': { plotter: handlePlotting }
		},*/
		//title: this.series,
		// underlayCallback: handleUnderlayRedraw.bind(this),
		valueRange: yAxisRange
    });

    return dygraphInstance;
}

// Prepares & returns data by converting times to Date objects and calculating
// x-axis extremes across all data.
Supervisor.prototype.prepareData = function(data, baseTime) {

	let t0 = performance.now();

    for (let fIdx = 0; fIdx < data.files.length; fIdx++) {
    // for (let fIdx = 0; fIdx < .length; fIdx++) {
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