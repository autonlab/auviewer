'use strict';

let requestHandler = new RequestHandler();
let globalStateManager = new GlobalStateManager();
let templateSystem = new TemplateSystem();

// Setup the websocket connection
let socket = io();
socket.on('connect', function() {
	console.log('Connected to realtime connection.');

	// Request initial payload (builtin & global templates)
	socket.emit('initial_payload');
});

socket.on('initial_payload', function(data) {
	globalAppConfig.verbose && console.log('SocketIO initial_payload received.');
	templateSystem.provideBuiltinTemplates(
		(data.hasOwnProperty('builtin_default_project_template') && data['builtin_default_project_template'] ? JSON.parse(data['builtin_default_project_template']) : {}) || {},
		(data.hasOwnProperty('builtin_default_interface_templates') && data['builtin_default_interface_templates'] ? JSON.parse(data['builtin_default_interface_templates']) : {}) || {},
	);
	templateSystem.provideGlobalTemplates(
		(data.hasOwnProperty('global_default_project_template') && data['global_default_project_template'] ? JSON.parse(data['global_default_project_template']) : {}) || {},
		(data.hasOwnProperty('global_default_interface_templates') && data['global_default_interface_templates'] ? JSON.parse(data['global_default_interface_templates']) : {}) || {},
	);
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

// Request the list of files for the project
requestHandler.requestProjectsList(function(data) {

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

});
