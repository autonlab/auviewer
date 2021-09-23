/*
Supervisor class manages the process of loading project files, labeling functions, and resultant annotations
*/

function Supervisor(payload) {
    this.project_id = payload['project_id']
    this.project_name = payload['project_name']

	this.prospectiveSegmentShade = 'rgba(211, 211, 211, .33)'; //'#D3D3D3'; // light grey
	this.existentSegmentShade = 'rgba(169, 169, 169, .33)'; //'#A9A9A9'; // dark grey
	this.toBeDeletedShade = 'rgba(233, 116, 81, .33)'; //'#E97451'; //burnt sienna red

	this.votesCalculated=false;
	this.statsCalculated=false;
	this.segmentType = 'CUSTOM';
	this.windowInfo = null;


	$('#modal').css('display', 'inline-block');

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

	this.shade_colors = ['white', 'rgba(188, 86, 208, .33)', 'rgba(222, 27, 95, .33)',  'rgba(27, 189, 222, .33)', 'rgba(27, 222, 76, .33)','orange', 'yellow', 'red', 'green', 'teal', 'cyan'];

	// Load the project config
	this.template = templateSystem.getProjectTemplate(this.project_id);

	// Holds the dom element of the instantiated legend
	this.legendDomElement = null;

	// Holds the dom element of the instantiated graph
	this.graphDomElement = null;

	this.timeWindow = 60 *60*1000;
	let self=this;
	// document.getElementById('recalculateVotes').setAttribute('disabled', true);

	document.getElementById('segment_type_switch').onclick = function() {self.toggleSegmentType()}

	requestHandler.requestInitialSupervisorPayload(this.project_id, function (data) {
		let lfSelector = document.getElementById('lfSelector');
		for (let lfTitle of data.labeling_function_titles) {
			let nextOpt = document.createElement('option');
			nextOpt.innerHTML = lfTitle;
			lfSelector.appendChild(nextOpt);
		}
		let voteSelector = document.getElementById('voteSelector');
		let colorIdx = 0;
		this.votesToColors = {};
		let rowStrings = [];
		for (let possibleVote of data.labeling_function_possible_votes) {
			let nextOpt = document.createElement('option');
			nextOpt.innerHTML = possibleVote;
			voteSelector.appendChild(nextOpt);
			// create 
			this.votesToColors[possibleVote] = this.shade_colors[colorIdx];
			rowStrings.push(`<td style="background-color:${this.shade_colors[colorIdx]}">${possibleVote}</td>`)
			colorIdx++;
		}
		rowStrings = rowStrings.join(' ');
		let shading_legend = document.createElement('table');
		let width = 100 / colorIdx;

		shading_legend.innerHTML =
				// '<col style="width:10%">' +
				`<col style="width:${width}%">`.repeat(colorIdx) +
				'<thead>' +
					'<tr>' +
						// '<th>LF Votes</th>' +
						'<th></th>'.repeat(colorIdx) +
					'</tr>' +
				'</thead>' +
				'<tbody >' +
					'<tr>' + rowStrings + '</tr>'
				'</tbody>';

		document.getElementById('shadingLegend').appendChild(shading_legend);
		this.buildLabelingFunctionTable(data.labeling_function_titles);
		this.initModel(data);
		$(document).on('mousemove', function(e){
			$('#modal').css('top', e.pageY);
			$('#modal').css('left', e.pageX);
		});
		$('#modal').css('display', 'none');
		let self=this;
		$('#view_segment').on('input', function () {
			self.setTimeWindow($('#view_segment').val()*15*60*1000, false, 0);
		});
	}.bind(this));

	toastr.options.timeOut = 3000;
	toastr.options.positionClass = "toast-bottom-center";
	toastr.options.showMethod = 'slideDown';
	toastr.options.hideMethod = 'slideUp';
	toastr.options.preventDuplicates = true;
}

Supervisor.prototype.initModel = function(data) {
    this.sync = null;

	//Holds the labeling function titles to their associated colors (more succinct than full title to render)
	this.lfTitleToColor = {};

	//Maps lf title to idx in votes array
	this.lfTitleToIdx = {};

	// Prepare data received from the backend and attach to class instance
	// new prepareData method needed
	this.projectData = this.prepareData(data, data.baseTime || 0);
	this.filenamesToIdxs = {};
	for (let i = 0; i < this.projectData.files.length; i++) {
		this.filenamesToIdxs[this.projectData.files[i][1]] = i;
	}
	this.lfVotes = this.projectData.labeling_function_votes;

	this.domElementObjs = new Array(this.projectData.files.length);
	this.dygraphs = new Array(this.projectData.files.length);

	this.allSegments = this.addColorToSegments(this.projectData.existent_segments, this.existentSegmentShade);
	this.createdSegments = null;
	this.segmentsToDelete = null;

	this.priorQuerySettings = {
		'random': false,
		'lfSelector': this.projectData.labeling_function_titles[0],
		'voteSelector': this.projectData.labeling_function_possible_votes[0]
	};

	for (const [idx, lfTitle] of this.projectData.labeling_function_titles.entries()) {
		this.lfTitleToIdx[lfTitle] = idx;
	}


	this.activeLF = this.projectData.labeling_function_titles[0];
	this.createThresholds(this.activeLF);
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
			let fileId = this.projectData.files[i][0];
			let seriesId = Object.keys(this.projectData.series[i])[0];
			this.domElementObjs[i] = this.buildGraph(filename, seriesId);
			graphsTableBody.appendChild(this.domElementObjs[i].graphWrapperDomElement);


			let series = Object.values(this.projectData.series[i])[0];
			let events = this.projectData.events[i];
			let metadata = this.projectData.metadata[i];

			this.dygraphs[i] = this.createDygraph(this.domElementObjs[i], series, events);
			let self=this;
			document.getElementById('left_'+filename).onclick = function() { self.pan(self.dygraphs[i], -1); };
			document.getElementById('right_'+filename).onclick = function() { self.pan(self.dygraphs[i], +1); };
			document.getElementById('breakout_'+filename).onclick = function() { self.breakout(fileid); };
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

Supervisor.prototype.toggleSegmentType = function() {
	if (this.segmentType === 'CUSTOM')
	{
		// hide custom creation pane and render window creation pane
		$('#custom_segment_creation').css('display', 'none');

		this.segmentType = 'WINDOW';
		this.windowInfo = {};
		$('#segment_type_label').text('Create window segments')
		$('#window_segment_creation').css('display', 'flex');

	}
	else if (this.segmentType == 'WINDOW')
	{
		// hide window creation pane and render custom creation pane
		$('#window_segment_creation').css('display', 'none');

		this.segmentType = 'CUSTOM';
		$('#segment_type_label').text('Create custom segments')
		$('#custom_segment_creation').css('display', 'flex');
	}

	let self = this;
	requestHandler.getSegments(this.project_id, this.segmentType, function (data) {
		self.allSegments = self.addColorToSegments(data.segments, self.existentSegmentShade);
		self.windowInfo = data.window_info;
		self.reshadeActiveGraphs(self.votesCalculated);
		if (self.segmentType === 'WINDOW') {
			$('#window_size').val(`${Math.round(data.window_info['window_size_ms']/(60*1000))}m`)
			$('#window_roll').val(`${Math.round(data.window_info['window_roll_ms']/(1000*60))}m`)
		}
	});
}

Supervisor.prototype.addIdToSegments = function(targetSegments, sourceSegments) {
	for (let [fileId, seriesBounds] of Object.entries(sourceSegments)) {
		for (let [seriesId, bounds] of Object.entries(seriesBounds)) {
			for (let sourceBounds of bounds) {
				for (let [i, targetBounds] of targetSegments[fileId][seriesId].entries()) {
					//find corresponding targetBound and add sourceBound.id to it
					if (targetBounds.left == sourceBounds.left && targetBounds.right == sourceBounds.right) {
						Object.assign(targetBounds, {'id': sourceBounds.id});
					}
				}
			}
		}
	}
	return targetSegments;
}

Supervisor.prototype.addColorToSegments = function(segments, color) {
	let colorObj = {
		'color': color
	};
	for (let [fileId, seriesBounds] of Object.entries(segments)) {
		for (let [seriesId, bounds] of Object.entries(seriesBounds)) {
			let newBounds = new Array();
			for (let bound of bounds) {
				let newBound = Object.assign(bound, colorObj);
				newBounds.push(newBound)
			}
			segments[fileId][seriesId] = newBounds;
		}
	}
	return segments;
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

	let seriesId = Object.keys(this.projectData.series[idx])[0];
	let leftId = 'left_' + filename;
	let rightId = 'right_' + filename;
	let breakoutButtonId = 'breakout_' + filename;
	graphWrapperDomElement.innerHTML = 
		// '<td >' +
		// 	'<div class="labelingFunctionVotes"></div>' +
		// '</td>' +
		'<td class="graph_title"><span title="'+this.altText+'">'+filename+'</span>' + 
			'<span id="'+breakoutButtonId+'" class="webix_icon wxi-plus"></span>' +
			'<div class="btn-group" role="group" aria-label="Time series navigation">' +
				'<button type="button" id="'+leftId+'" class="btn btn-primary"><span class="webix_icon wxi-angle-left"></span></button>' +
				'<button type="button" id="'+rightId+'" class="btn btn-primary"><span class="webix_icon wxi-angle-right"></span></button>' +
			'</div>' +
		'</td>' +
		'<td >' +
			`<div class="graph" id="${filename};${seriesId}"></div>` +
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
	document.getElementById('breakout_'+filename).onclick = function() { self.breakout(self.projectData.files[idx][0]); };

	this.shadeGraphSegmentsForFile(filename, this.votesCalculated);
}

Supervisor.prototype.regenerateGraphs = function(pageNum) {
	let startIdx = pageNum * this.seriesOnPage;
	let endIdx = Math.min((pageNum + 1) * this.seriesOnPage, this.projectData.files.length);
	this.globalYExtremes[1] = 0;
	// this.activeGraphs = new Array(this.seriesOnPage);
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

	if (this.votesCalculated && this.segmentType==='WINDOW') {
		this.updateVotesWithActiveGraphs();
	}

	this.setTimeWindow(this.timeWindow, forceAdjustment=true, 10);
}

Supervisor.prototype.setTimeWindow = function(newTimeWindow, forceAdjustment=false, maxSteps=10) {
	if (forceAdjustment || (newTimeWindow !== this.timeWindow)) {
		// document.getElementById('recalculateVotes').removeAttribute('disabled'); // since we have a new time slice, it should now be allowed to recalculate
		this.timeWindow = newTimeWindow;
		for (let graphIdx of this.activeGraphs) {
			let curGraph = this.dygraphs[graphIdx];
			let curRange = curGraph.xAxisRange();
			let desiredRange = [curRange[0], curRange[0] + this.timeWindow];
			this.animate(curGraph, desiredRange, maxSteps);
		}
	}
}

Supervisor.prototype.breakout = function(fileid) {
	window.open(
		`project?id=${this.project_id}#file_id=${fileid}`,
		'_blank'
		);
}

Supervisor.prototype.activateSegmentCreationMode = function() {
	if (this.segmentsToDelete !== null) {
		toastr.warning('Exit segment deletion mode to create segments!');
	} else {
		this.createdSegments = {};
		$('#create_segments').attr('onclick','globalStateManager.currentSupervisor.submitCreatedSegments()');
		$('#create_segments').text('Submit created segments');
	}
}

Supervisor.prototype.activateSegmentDeletionMode = function () {
	if (this.createdSegments !== null) {
		toastr.warning('Exit segment creation mode to delete segments!');
	} else {
		this.segmentsToDelete = {};
		$('#delete_segments').attr('onclick','globalStateManager.currentSupervisor.deleteSegments()');
		$('#delete_segments').text('Delete selected segments');
	}
}

Supervisor.prototype.deleteSegments = function () {
	if (this.createdSegments !== null) {
		toastr.warning('Exit segment creation mode to delete segments!');
	} else if (jQuery.isEmptyObject(this.segmentsToDelete)) {
		toastr.warning('No segments selected for deletion!');
	} else {
		let self = this;
		requestHandler.deleteVoteSegments(this.project_id, this.segmentsToDelete, function (data) {
			if (data.success) {
				self.removeSegmentsByColor(self.allSegments, self.toBeDeletedShade);
				self.reshadeActiveGraphs(self.votesCalculated);
				toastr.success(`Successfully deleted ${data.number_deleted} segment${data.number_deleted === 1 ? '' : 's'}`);
			}
			$('#delete_segments').attr('onclick','globalStateManager.currentSupervisor.activateSegmentDeletionMode()');
			$('#delete_segments').text('Delete segments');
			self.segmentsToDelete = null;
		})
	}
}

Supervisor.prototype.removeSegmentsByColor = function(segmentObj, color) {
	for (let [filename, seriesObj] of Object.entries(segmentObj)) {
		for (let [series, boundsArr] of Object.entries(seriesObj)) {
			let newBoundsArr = new Array();
			for (let bounds of boundsArr) {
				if (bounds.color !== color) {
					newBoundsArr.push(bounds);
				}
			}
			segmentObj[filename][series] = newBoundsArr;
		}
	}
}

Supervisor.prototype.reshadeActiveGraphs = function(withVotes=false) {
	for (let file_idx of this.activeGraphs) {
		this.shadeGraphSegmentsForFile(this.projectData.files[file_idx][1], withVotes);
	}
}

Supervisor.prototype.charIsAlpha = function(char) {
	const code = char.charCodeAt(0); // user must pass length 1 string
	if ((code > 64 && code < 91) || // upper alpha (A-Z)
        (code > 96 && code < 123)) // lower alpha (a-z)
	{
		return true;
	}
	return false;
}

Supervisor.prototype.convertTimeStringToInt_ms = function(timeString) {
	// extract time int from beginning of string
	let res = [];
	let i = 0;
	while (!this.charIsAlpha(timeString[i]))
	{
		res.push(timeString[i]);
		i += 1;
	}
	res = parseInt(res.join(''));

	let time_ms = null;
	if (timeString.endsWith('hr'))
	{
		time_ms = res * 60 * 60 * 1000;
	}
	else if (timeString.endsWith('m'))
	{
		time_ms = res * 60 * 1000;
	}
	else if (timeString.endsWith('s'))
	{
		time_ms = res * 1000;
	}

	return time_ms;

}

Supervisor.prototype.populateWindowInfoFromForm = function() {
	let window_size_ms = this.convertTimeStringToInt_ms($('#window_size').val());
	let window_roll_ms = this.convertTimeStringToInt_ms($('#window_roll').val());
	this.windowInfo = {
		'window_size_ms': window_size_ms,
		'window_roll_ms': window_roll_ms
	};
}

Supervisor.prototype.submitWindowSegments = function() {
	// extract window_size_ms && window_roll_ms
	this.populateWindowInfoFromForm();

	// submit for segment creation
	let self = this;
	$('#modal').css('display', 'flex');
	requestHandler.submitVoteSegments(this.project_id, /*created_segments*/null, this.windowInfo, function (data) {
		if (data.success) {
			self.allSegments = self.addColorToSegments(data.newly_created_segments, self.existentSegmentShade);
			self.reshadeActiveGraphs(self.votesCalculated);
			$('#modal').css('display', 'none');
			toastr.success(`Successfully added ${data.num_added} segments`);
			if (self.votesCalculated) {
				self.updateVotesWithActiveGraphs();
			}
		}
	});
}

Supervisor.prototype.submitCreatedSegments = function() {
	if (this.segmentsToDelete !== null) {
		toastr.warning('Exit segment deletion mode to create segments!');
	} else if (jQuery.isEmptyObject(this.createdSegments)) {
		toastr.warning('No created segments to submit!');
	} else {
		let self = this;
		requestHandler.submitVoteSegments(this.project_id, this.createdSegments, /*window_info*/null, function (data) {
			if (data.success) {
				self.allSegments = self.addColorToSegments(self.allSegments, self.existentSegmentShade);
				self.allSegments = self.addIdToSegments(self.allSegments, data.newly_created_segments);
				self.reshadeActiveGraphs(self.votesCalculated);
				toastr.success(`Successfully added ${data.num_added} segments`);
			}
			self.createdSegments = null;
			$('#create_segments').attr('onclick','globalStateManager.currentSupervisor.activateSegmentCreationMode()');
			$('#create_segments').text('Add segments');
		});
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

Supervisor.prototype.animate = function(graph, desiredRange, maxSteps=7) {
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

Supervisor.prototype.calculateStats = function () {
	let self=this;
	requestHandler.requestAggregateLabelerStats(this.project_id, this.segmentType, function (data) {
		self.labelerStatistics = data;
		if (self.statsCalculated) {
			self.clearStatsPane();
		}
		self.renderStats();
		self.statsCalculated = true;
	});
}

Supervisor.prototype.renderStats = function() {
	let stats = this.labelerStatistics[this.activeLF];
	let trStringList = [];
	for (let [statTitle, statValue] of Object.entries(stats)) {
		if (statValue !== null) {
			trStringList.push(
			'<tr>'+
				`<th scope="row">${statTitle}</th>`+
				`<td>${statValue.toFixed(3)}</td>` +
			'</tr>'
			);
		}
	}
	let x = document.createElement('table');
	x.className = 'table table-sm table-striped table-bordered mb-2';
	x.innerHTML = 
		'<tbody>' +
			trStringList.join('');
		'</tbody>';
	document.getElementById('stats_pane').appendChild(x);
}

Supervisor.prototype.clearStatsPane = function() {
	document.getElementById('stats_pane').removeChild(document.getElementById('stats_pane').lastChild);
}

Supervisor.prototype.updateVotesWithActiveGraphs = function () {
	let files = [];
	this.activeGraphs.forEach((activeGraphIdx) => {
		let file_id = this.projectData.files[activeGraphIdx][0];
		files.push(file_id);
	});
	let windowInfo = this.segmentType==='WINDOW' ? this.windowInfo : null;
	$('#modal').css('display', 'flex');
	let self = this;
	requestHandler.getVotes(this.project_id, files, windowInfo, function(data) {
		for (const [segId, votes] of Object.entries(data.labeling_function_votes)) {
			self.labeling_function_votes[segId] = votes;
		}
		self.votesCalculated = true;
		$('#calculate_stats').removeAttr('disabled');
		if (self.statsCalculated) {
			self.clearStatsPane();
			self.renderStats();
		}
		document.getElementById('shadingLegend').style.display = 'inline-block';
		self.reshadeActiveGraphs(withVotes=true);
		// turn off loader now that we've received data
		$('#modal').css('display', 'none')
	});
}

Supervisor.prototype.recalculateVotes = function () {
	// ask backend to segment all series' and vote on subsequent segments, then return them all
	let self = this;
	let files = [];
	let windowInfo = null;
	if (this.segmentType==='WINDOW') {
		this.activeGraphs.forEach((activeGraphIdx) => {
			let file_id = this.projectData.files[activeGraphIdx][0];
			files.push(file_id);
		});
		windowInfo = this.windowInfo;
	}
	requestHandler.getVotes(this.project_id, files, windowInfo, function(data) {
		self.labeling_function_votes = data.labeling_function_votes;
		self.votesCalculated = true;
		$('#calculate_stats').removeAttr('disabled');
		if (self.statsCalculated) {
			self.clearStatsPane();
			self.renderStats();
		}
		document.getElementById('shadingLegend').style.display = 'inline-block';
		self.reshadeActiveGraphs(withVotes=true);
		// turn off loader now that we've received data
		$('#modal').css('display', 'none')
	});
	// set loader on
	$('#modal').css('display', 'flex')
}

Supervisor.prototype.shadeTimeSegmentsWithVotes = function() {
	for (let activeGraphIdx of this.activeGraphs) {
		this.shadeGraph(activeGraphIdx);
	}
}

Supervisor.prototype.shadeGraphSegmentsForFile = function(filename, withVotes=false) {
	if (filename in this.allSegments) {
		for (let [seriesId, dataBoundsArr] of Object.entries(this.allSegments[filename])) {
			this.shadeGraphSegments(this.dygraphs[this.filenamesToIdxs[filename]], dataBoundsArr, withVotes);
		}
	} else {
		console.log(filename);
		this.shadeGraphSegments(this.dygraphs[this.filenamesToIdxs[filename]], [], null);
	}
}
Supervisor.prototype.shadeGraphSegments = function(graph, dataBoundsArray, withVotes=false) {
	let self = this;
	if (dataBoundsArray.length === 0) {
		graph.updateOptions({
			underlayCallback: null
		});
	}
	else {
		graph.updateOptions({
			underlayCallback: function(canvas, area, g) {
				for (let bounds of dataBoundsArray) {
					let bottomLeft = g.toDomCoords(bounds.left, -20);
					let topRight = g.toDomCoords(bounds.right, +20);
					left = bottomLeft[0];
					right = topRight[0];
					// border on both sides
					canvas.fillStyle = 'black';
					let borderWidth = 2;
					canvas.fillRect(left-borderWidth/2, area.y, borderWidth, area.h);
					canvas.fillRect(right-borderWidth/2, area.y, borderWidth, area.h);
					// canvas.fillRect(left, area.y, right-left, borderWidth);
					// canvas.fillRect(left, borderWidth, right-left, borderWidth);
					if (withVotes && (bounds.color !== self.toBeDeletedShade) && (bounds.id in self.labeling_function_votes)) {
						let vote = self.labeling_function_votes[bounds.id][self.lfTitleToIdx[self.activeLF]];
						let color = self.votesToColors[vote];
						canvas.fillStyle = color;
						canvas.fillRect(left, area.y, right-left, area.h);
					} else {
						canvas.fillStyle = bounds.color;
						canvas.fillRect(left, area.y, right-left, area.h);
					}
				}
				// get start and end timestamps
				// let bottomLeft = g.toDomCoords(left, -20);
				// let topRight = g.toDomCoords(right, +20);
				// left = bottomLeft[0];
				// right = topRight[0];
			}
	});

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
			for (let [bucketIdx, endIdx] of endIndices.entries()) {
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

				let vote = self.lfVotesByTimeSegment[graphIdx][bucketIdx];
				let color = self.votesToColors[vote];
				canvas.fillStyle = color;
				canvas.fillRect(left, area.y, right-left, area.h);
				startIdx = endIdx;
			}
		},
		legendFormatter: function(data) {
			return data.series.map(function (series) {
				return series.dashHTML + ' ' + series.label + ' - ' + series.yHTML
				}).join('<br>') +
				'<br>' + 
				self.activeLF + ' - ' + self.getVoteForGraphAndPoint(graphIdx, data.x, self.activeLF);
		}
	});
}

Supervisor.prototype.getVoteForGraphAndPoint = function(graphIdx, xPoint, lfTitle) {
	let startIdx = 0;
	let bucketIdx = 0;
	let series = Object.values(this.projectData.series[graphIdx])[0].data;
	xPoint = new Date(xPoint);
	if (isNaN(xPoint.getTime()) || this.lfVotesByTimeSegment[graphIdx].length === 0) {
		// means date of x point isn't valid
		return 'N/A';
	}
	for (let endIdx of this.timeSegmentEndIndices[graphIdx]) {
		// get start and end timestamps
		let start = series[startIdx][0];
		let end = series[endIdx-1][0];
		if (start <= xPoint && xPoint <= end) {
			break;
		}
		bucketIdx++;
	}
	return this.lfVotesByTimeSegment[graphIdx][bucketIdx];
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
	let lfSelection = document.getElementById('lfSelection');
	for (let lfTitle of labelingFunctionTitles) {
		let nextOpt = document.createElement('option');
		nextOpt.innerHTML = lfTitle;
		lfSelection.appendChild(nextOpt);
		// let lfTitleDomElement = document.createElement('tr');
		// lfTitleDomElement.innerHTML = 
		// 	'<td >' + lfTitle + '</td>' + 
		// 	'<td >' +
		// 		'<input class="btn" type="checkbox" id="' + lfTitle + '" value = "' + lfTitle + '" onclick="globalStateManager.currentSupervisor.onClick(`'+lfTitle+'`)"> </td>';
		// lfTitleDomElement.style.fontSize = 'small';
		// document.getElementById('labelingFunctionTable').getElementsByTagName('tbody')[0].appendChild(lfTitleDomElement);
	}
}

Supervisor.prototype.clearThresholds = function() {
	let thresholdsInputPane = document.getElementById('threshold_pane');
	while (thresholdsInputPane.firstChild) {
		if (thresholdsInputPane.firstChild.id === 'submitThresholds') {
			break;
		}
		thresholdsInputPane.removeChild(thresholdsInputPane.firstChild);
	}
}

Supervisor.prototype.cleanCode = function(codeText) {
	let result = [];
	let firstLine = true;
	let whitespaceIdx = 0;
	// finds the amount space on the first line, and removes that much whitespace on all lines
	for (let line of codeText.split('\n')) {
		if (firstLine) {
			for (let i = 0; i < line.length; i++) {
				if (line[i] !== ' ') {
					whitespaceIdx = i;
					break;
				}
			}
			firstLine = false;
		}
		line = line.slice(whitespaceIdx);
		result.push(line);
	}
	return result.join('\n');
}

Supervisor.prototype.createThresholds = function(lfTitle) {
	let thresholdsInputPane = document.getElementById('threshold_pane');
	for (let threshold of this.projectData.labelers_to_thresholds[lfTitle]) {
		let thresholdValue = this.projectData.thresholds[threshold];
		let newElem = document.createElement('div');
		newElem.classList.add('input-group');
		newElem.classList.add('mb-1');
		newElem.innerHTML =
			'<div class="input-group-prepend">' +
				'<span class="input-group-text">' + threshold + '</span>' +
			'</div>' +
			'<input type="text" class="form-control" id="' + threshold + '">';
		thresholdsInputPane.prepend(newElem);
		document.getElementById(threshold).value = thresholdValue;
	}
	newElem = document.createElement('pre');
	newElem.innerHTML = 
			'<code>'+
			this.cleanCode(this.projectData.labeler_code[this.activeLF]) +
			'</code>';
	thresholdsInputPane.prepend(newElem);
}

Supervisor.prototype.previewThresholds = function() {
	let thresholds = [];
	// collect current thresholds and values and send them off to update backend
	for (let threshold of this.projectData.labelers_to_thresholds[this.activeLF]) {
		let value = document.getElementById(threshold).value;
		thresholds.push({'title': threshold, 'value': value});
	}
	let labeler = this.activeLF;
	let files = [];
	this.activeGraphs.forEach((activeGraphIdx) => {
		let file_id = this.projectData.files[activeGraphIdx][0];
		files.push(file_id);
	});
	let self = this;
	requestHandler.previewThreshold(this.project_id, files, labeler, thresholds, this.voteWindow, function(data) {
		self.replaceShadeState(data.votes, data.end_indices, self.activeGraphs[0]);
		self.shadeTimeSegmentsWithVotes();
	});
}

Supervisor.prototype.replaceShadeState = function(votes, endIndices, startIdx) {
	for (let idx = startIdx; idx < (startIdx+votes.length); idx++) {
		let endIndexSet = endIndices[idx-startIdx];
		let voteSet = votes[idx-startIdx];
		this.lfVotesByTimeSegment[idx] = voteSet;
		this.timeSegmentEndIndices[idx] = endIndexSet;
	}
}

Supervisor.prototype.submitThresholds = function() {
	// collect current thresholds and values and send them off to update backend
	let self = this;
	for (let threshold of this.projectData.labelers_to_thresholds[this.activeLF]) {
		let value = parseFloat(document.getElementById(threshold).value);
		requestHandler.updateThreshold(this.project_id, threshold, value, function (data) {
			if (data.success) {
				toastr.success(`Successfully updated ${threshold}`);
				self.projectData.thresholds[threshold] = value;
				self.recalculateVotes();
			} else {
				toastr.error(`Something went wrong, failed to update ${threshold}`);
			}
		});
	}
}

Supervisor.prototype.onLabelerSelect = function() {
	let lfSelection = document.getElementById('lfSelection');
	this.activeLF = lfSelection.value;
	// tear down threshold pane
	this.clearThresholds();
	if (this.statsCalculated) {
		this.clearStatsPane();
	}
	// replace threshold pane
	this.createThresholds(lfSelection.value);
	if (this.votesCalculated) {
		if (this.statsCalculated) {
			this.renderStats();
			toastr.success(`Now showing votes and aggregate statistics for ${this.activeLF}`);
		} else {
			toastr.success(`Now showing votes for ${this.activeLF}`);
		}
		this.reshadeActiveGraphs(withVotes=true);
	}
	return;
	// const divInQuestion = document.getElementById(lfTitle);
	// if (divInQuestion.checked) {
	// 	this.activeLFs.push(lfTitle);
	// 	for (const [color, alreadyInUse] of Object.entries(this.active_lf_colors)) {
	// 		if (!alreadyInUse) {
	// 			this.active_lf_colors[color] = true;
	// 			this.lfTitleToColor[lfTitle] = color;
	// 			divInQuestion.parentElement.parentElement.style.backgroundColor = color;
	// 			break;
	// 		}
	// 	}
	// }
	// else {
	// 	const isLF = (elem) => elem === lfTitle;
	// 	let lfIndex = this.activeLFs.findIndex(isLF);
	// 	this.activeLFs.splice(lfIndex, lfIndex+1);
	// 	this.active_lf_colors[this.lfTitleToColor[lfTitle]] = false;
	// 	divInQuestion.parentElement.parentElement.style.backgroundColor = '#888';
	// }
}

Supervisor.prototype.getLFColorByTitle = function(lfTitle) {
	this.lfTitleToColor[lfTitle];
}

Supervisor.prototype.buildGraph = function(filename, seriesId) {

	// Create the graph wrapper dom element
	let graphWrapperDomElement = document.createElement('tr');
	graphWrapperDomElement.className = 'graph_row_wrapper';
	graphWrapperDomElement.style.height = this.template.graphHeight;
	let leftId = 'left_' + filename;
	let rightId = 'right_' + filename;
	let breakoutButtonId = 'breakout_' + filename;
	graphWrapperDomElement.innerHTML =
		// '<td >' +
		// 	'<div class="labelingFunctionVotes"></div>' +
		// '</td>' +
		'<td class="graph_title"><span title="'+this.altText+'">'+filename+'</span>' +
			'<span id="'+breakoutButtonId+'" class="webix_icon wxi-plus"></span>' +
			'<div class="btn-group" role="group" aria-label="Time series navigation">' +
				'<button type="button" id="'+leftId+'" class="btn btn-primary"><span class="webix_icon wxi-angle-left"></span></button>' +
				'<button type="button" id="'+rightId+'" class="btn btn-primary"><span class="webix_icon wxi-angle-right"></span></button>' +
			'</div>' +
		'</td>' +
		'<td >' +
			`<div class="graph" id="${filename};${seriesId}"></div>` +
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

Supervisor.prototype.reshadeSegmentIfClicked = function(segmentObj, filename, seriesId, x, color) {
	if (!(filename in segmentObj)) {
		return null;
	}
	if (!(seriesId in segmentObj[filename])) {
		return null;
	}
	for (let [i, segment] of segmentObj[filename][seriesId].entries()) {
		if (segment.left <= x && x <= segment.right) {
			//in bounds
			let result = Object.assign(segment, {'color': color});
			segmentObj[filename][seriesId][i] = result;
			return result;
		}
	}

	// no hit
	return null;
}

Supervisor.prototype.handleClick = function(event, g, context) {

	if (this.segmentsToDelete !== null) {
		const [filename, seriesId] = g.maindiv_.id.split(';');
		let segmentToBeDeleted = this.reshadeSegmentIfClicked(this.allSegments, filename, seriesId, g.toDataXCoord(event.layerX), this.toBeDeletedShade);
		if (segmentToBeDeleted !== null) {
			this.addSegmentTo(this.segmentsToDelete, filename, seriesId, segmentToBeDeleted);
		}
		console.log(segmentToBeDeleted);
		this.shadeGraphSegments(g, this.allSegments[filename][seriesId], this.votesCalculated);
	}
}

// Handle mouse-down for pan & zoom
Supervisor.prototype.handleMouseDown = function(event, g, context) {

	context.initializeMouseDown(event, g, context);

	if (event.altKey) {
		handleAnnotationHighlightStart(event, g, context);
	}
	else if (event.shiftKey) {
		Dygraph.startZoom(event, g, context);
	} else {
		context.medViewPanningMouseMoved = false;
		Dygraph.startPan(event, g, context);
	}

}

Supervisor.prototype.addSegmentTo = function(segmentObj, filename, seriesId, newSegment) {
	if (!(filename in segmentObj)) {
		// add it
		segmentObj[filename] = {};
	}
	if (!(seriesId in segmentObj[filename])) {
		segmentObj[filename][seriesId] = new Array();
	}
	segmentObj[filename][seriesId].push(newSegment);
}

// Handle mouse-up for pan & zoom.
Supervisor.prototype.handleMouseUp = function(event, g, context) {
	if (this.createdSegments !== null) {
		// in segment creation mode

		//add segment bounds to corresponding file > series list
		const [filename, seriesId] = g.maindiv_.id.split(';');
		let left = g.toDataXCoord(context.dragStartX);
		let right = g.toDataXCoord(context.dragEndX);
		this.addSegmentTo(this.createdSegments, filename, seriesId, {left, right, 'color':this.prospectiveSegmentShade});
		this.addSegmentTo(this.allSegments, filename, seriesId, {left, right, 'color':this.prospectiveSegmentShade});
		this.shadeGraphSegments(g, this.allSegments[filename][seriesId], this.votesCalculated);
	} else {
		// perform normal zooming behavior
		Dygraph.endZoom(event, g, context);
	}

	// Dygraph.startZoom(event, g, context);
	// Dygraph.endZoom(event, g, context);
	// if (context.mvIsAnnotating) {
	// 	handleAnnotationHighlightEnd(event, g, context, this);
	// }
	// else if (context.isZooming) {
	// 	Dygraph.endZoom(event, g, context);
	// 	if ('file' in this) {
	// 		this.file.updateCurrentViewData();
	// 	} else {
	// 		this.updateCurrentViewData();
	// 	}
	// }
	// else if (context.isPanning) {
	// 	if (context.medViewPanningMouseMoved) {
	// 		if ('file' in this) {
	// 			this.file.updateCurrentViewData();
	// 		} else {
	// 			this.updateCurrentViewData();
	// 		}
	// 		context.medViewPanningMouseMoved = false;
	// 	}
	// 	Dygraph.endPan(event, g, context);
	// }

}

// Handle mouse-move for pan & zoom.
Supervisor.prototype.handleMouseMove = function(event, g, context) {

	// Dygraph.moveZoom(event, g, context);
	Dygraph.moveZoom(event, g, context);
	// console.log(event, context);
	// Dygraph.startZoom(event, g, context);
	// Dygraph.endZoom(event, g, context);
	// if (context.mvIsAnnotating) {
	// 	handleAnnotationHighlightMove(event, g, context);
	// }
	// else if (context.isZooming) {
	// 	Dygraph.moveZoom(event, g, context);
	// }
	// else if (context.isPanning) {
		// context.medViewPanningMouseMoved = true;
		// Dygraph.movePan(event, g, context);
	// }

}

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
		// clickCallback: this.handleClick.bind(this),
		// colors: [this.template.lineColor],//'#5253FF'],
        colors: ['#5253FF'],
		// dateWindow: timeWindow,
		drawPoints: true,
		// gridLineColor: this.template.gridColor,
		interactionModel: {
			'mousedown': this.handleMouseDown.bind(this),
			'mouseup': this.handleMouseUp.bind(this),
			'mousemove': this.handleMouseMove.bind(this),
			'click': this.handleClick.bind(this)
		},
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
