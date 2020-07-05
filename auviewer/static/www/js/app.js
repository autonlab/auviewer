'use strict';

// Verify we're serving Chrome browser
if (navigator.userAgent.indexOf("Chrome") === -1) {

	const body = document.getElementsByTagName("BODY")[0];

	// Clear all body elements
	// See: https://jsperf.com/innerhtml-vs-removechild/15
	while (body.firstChild) {
		body.removeChild(body.firstChild);
	}

	// Add user notice
	body.innerHTML =
		'<!-- Browser warning -->\n' +
		'<div style="position: absolute; z-index: 9999999999; width: 100%; height: 100%; background-color: white; display: flex; justify-content: center; align-items: center;">\n' +
		'\t<div style="width: 100%; text-align: center;">\n' +
		'\t\t<h1>Please use Chrome to view this web app.</h1><h6>Unfortunately, the charting library we use at this time is incompatible with other browsers.</h6>\n' +
		'\t</div>\n' +
		'</div>';

	throw new Error("Please use Chrome browser to view this web app. Unfortunately, the charting library we use at this time is incompatible with other browsers.");

}

let requestHandler = new RequestHandler();
let globalStateManager = new GlobalStateManager();
let templateSystem = new TemplateSystem();

// Setup the websocket connection
let socket = io();
socket.on('connect', function() {
	console.log('Connected to realtime connection.');
});

socket.on('new_data', function(data) {

	// Log the received data
	globalAppConfig.verbose && console.log('rcvd socketio new_data:', deepCopy(data));

	// Grab the current file
	let currentFile = globalStateManager.currentFile;

	// If we're not in realtime mode, we cannot process incoming realtime data.
	if (!currentFile || !(currentFile.projname === '__realtime__' && currentFile.filename === '__realtime__')) {
		console.log('Received new realtime data, but not in realtime mode. Ignoring.');
		return;
	}

	// Send the new data for processing
	currentFile.processNewRealtimeData(data);

});

socket.on('push_template', function(data) {

	// Log the received data
	globalAppConfig.verbose && console.log('rcvd socketio push_template:', deepCopy(data));

	// Check for expected data format

	// We expect template to be a string
	if (!data.hasOwnProperty('template') || !(typeof data.template === 'string' || data.template instanceof String )) {
		console.log("Error: push_template received data without template:", data);
		return
	}

	// Parse parameters
	let template = JSON.parse(data.template);
	let project = data.hasOwnProperty('project') ? data.project : '';
	let intfc = data.hasOwnProperty('interface') ? data.interface : '';

	// Push template to the template system
	templateSystem.providePushTemplate(template, project, intfc)

});

// Attach event handlers to the annotation modal
$('#annotationModal button.saveButton').click(function() {
	$('#annotationModal').data('callingAnnotation').save();
});
$('#annotationModal button.cancelButton').click(function() {
	$('#annotationModal').data('callingAnnotation').cancel();
});
$('#annotationModal button.deleteButton').click(function() {
	if (confirm("Are you sure you want to delete this annotation?")) {
		$('#annotationModal').data('callingAnnotation').delete();
	}
});

$('#annotationsListModal').on('show.bs.modal', function (e) {

	// Clear previous annotation list
	// See: https://jsperf.com/innerhtml-vs-removechild/15
	const tbody = this.querySelector('tbody');
	while (tbody.firstChild) {
		tbody.removeChild(tbody.firstChild);
	}

	let modal = this;

	let rowClickHandler = function() {
		$(modal).modal('hide');
		$(this).data('annotation').goTo();
	};

	if (globalStateManager.currentFile && globalStateManager.currentFile.hasOwnProperty('annotations')) {

		for (let a of globalStateManager.currentFile.annotations) {

			if (a.state === 'existing') {

				// Create the dom element
				let tr = document.createElement('tr');

				// Attach the annotation to the dom element for use by the click
				// handler, then attach the click handler.
				$(tr).data('annotation', a);
				tr.addEventListener("click", rowClickHandler);

				// Display content of the row
				tr.innerHTML =
					'<th scope="row">' + a.id + '</th>' +
					'<td>' + a.getStartDate().toLocaleString() + '</td>' +
					'<td>' + a.getEndDate().toLocaleString() + '</td>' +
					'<td>' + JSON.stringify(a.annotation) + '</td>';
				tbody.appendChild(tr);
			}

		}

	}

});

function populateAllAnnotationsModal() {

	const modal = document.getElementById('allAnnotationsListModal')

	// Clear previous annotation list
	// See: https://jsperf.com/innerhtml-vs-removechild/15
	const tbody = modal.querySelector('tbody');
	while (tbody.firstChild) {
		tbody.removeChild(tbody.firstChild);
	}

	const rowClickHandler = function() {
		$(modal).modal('hide');
		$(this).data('annotation').goTo();
	};

	if (globalStateManager.currentProject && Array.isArray(globalStateManager.currentProject.annotations)) {

		for (let a of globalStateManager.currentProject.annotations) {

			if (a.state === 'existing') {

				// Create the dom element
				let tr = document.createElement('tr');

				// Attach the annotation to the dom element for use by the click
				// handler, then attach the click handler.
				$(tr).data('annotation', a);
				tr.addEventListener("click", rowClickHandler);

				// Display content of the row
				tr.innerHTML =
					'<th scope="row">' + a.id + '</th>' +
					'<td>' + a.file + '</td>' +
					'<td>' + a.getStartDate().toLocaleString() + '</td>' +
					'<td>' + a.getEndDate().toLocaleString() + '</td>' +
					'<td>' + JSON.stringify(a.annotation) + '</td>';
				tbody.appendChild(tr);
			}

		}

	}

}

$('#allAnnotationsListModal').on('show.bs.modal', function (e) {

	if (globalStateManager.currentProject && Array.isArray(globalStateManager.currentProject.annotations)) {

		populateAllAnnotationsModal();

	} else if (globalStateManager.currentProject) {

		// Request project annotations
		globalStateManager.currentProject.getAnnotations(populateAllAnnotationsModal);

	}

});

// Request the list of files for the project
requestHandler.requestInitialPayload(function(data) {

	templateSystem.provideBuiltinTemplates(
		(data.hasOwnProperty('builtin_default_project_template') && data['builtin_default_project_template'] ? JSON.parse(data['builtin_default_project_template']) : {}) || {},
		(data.hasOwnProperty('builtin_default_interface_templates') && data['builtin_default_interface_templates'] ? JSON.parse(data['builtin_default_interface_templates']) : {}) || {},
	);
	templateSystem.provideGlobalTemplates(
		(data.hasOwnProperty('global_default_project_template') && data['global_default_project_template'] ? JSON.parse(data['global_default_project_template']) : {}) || {},
		(data.hasOwnProperty('global_default_interface_templates') && data['global_default_interface_templates'] ? JSON.parse(data['global_default_interface_templates']) : {}) || {},
	);

	let projectSelect = document.getElementById('project_selection');

	for (let i in data['projects']) {

		let opt = document.createElement('OPTION');
		opt.setAttribute('value', data['projects'][i]);
		opt.innerText = data['projects'][i];
		projectSelect.appendChild(opt);

	}

	// Re-render the select picker
	$(projectSelect).selectpicker('refresh');

	// Detect hash variables
	var hash = window.location.hash.substr(1);
	var result = hash.split('&').reduce(function (result, item) {
	    var parts = item.split('=');
	    result[parts[0]] = parts[1];
	    return result;
	}, {});

	// Handle initial hash variables
	if (result.hasOwnProperty('project') && result.hasOwnProperty('file')) {
		globalStateManager.loadFile(result['file'], result['project'])
	}

});















var small_film_set = [
	{ id:1, title:"The Shawshank Redemption", year:1994, votes:678790, rating:9.2, rank:1},
	{ id:2, title:"The Godfather", year:1972, votes:511495, rating:9.2, rank:2},
	{ id:3, title:"The Godfather: Part II", year:1974, votes:319352, rating:9.0, rank:3},
	{ id:4, title:"The Good, the Bad and the Ugly", year:1966, votes:213030, rating:8.9, rank:4},
	{ id:5, title:"My Fair Lady", year:1964, votes:533848, rating:8.9, rank:5},
	{ id:6, title:"12 Angry Men", year:1957, votes:164558, rating:8.9, rank:6}
];

// let xyz = webix.ui({
// 	view: "window",
// 	close: true,
// 	head: "Available Graphs &mdash; Show/Hide",
// 	left: 50,
// 	move: true,
// 	top: 50,
// 	body: {
// 		view: "treetable",
// 		collapse: true,
// 		autoheight: true,
// 		autowidth: true,
// 		filterMode:{ level: false, showSubItems: false },
// 		select: false,
// 		threeState: true,
// 		columns: [
// 			{ id: "value", adjust: true, fillspace: true, header: ["Graphs", {content:"textFilter"}], minWidth: 350, template: "{common.space()}{common.icon()}{common.treecheckbox()}{common.folder()}#value#" }
// 		],
// 		data: [
// 			{ "value": "The Shawshank Redemption", "data":[
// 					{ "value": "Part 1"},
// 					{ "value": "Part 2", "data":[
// 							{ "value": "Part 1", checked: true}
// 						]}
// 				]}
// 		]
// 	}
// });
//
// xyz.show();







































