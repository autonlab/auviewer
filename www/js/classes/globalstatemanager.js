'use strict';

// Class declaration
function GlobalStateManager() {

	// Holds the currently-selected project
	this.currentProject = null;

	// Holds the currently-selected file
	this.currentFile = null;

	// Length of time to display for realtime graphs, in seconds
	this.realtimeTimeWindow = 600;

}

// Clear the main file currently loaded in the viewer
GlobalStateManager.prototype.clearMainFile = function() {

	// Clear current file if there is one
	if (this.currentFile !== null) {
		this.currentFile.destroy();
		this.currentFile = null;
	}

};

// Clear the main project currently loaded in the viewer
GlobalStateManager.prototype.clearMainProject = function() {

	// Clear main file from the viewer.
	this.clearMainFile();

	// Clear contents of file select
	document.getElementById('file_selection').innerHTML = '<option></option>';

	// Set current project to null
	this.currentProject = null;

};

GlobalStateManager.prototype.enterRealtimeMode = function() {

	// Add the realtime class name to body
	document.getElementsByTagName('body')[0].className = 'realtime';

	// Reset & unload current main project
	this.resetMainProject();

	// Load the realtime file in the viewer
	this.newMainFile('__realtime__', '__realtime__')

};

GlobalStateManager.prototype.exitRealtimeMode = function () {

	// Remove the realtime class name from body
	document.getElementsByTagName('body')[0].className = '';

	// Reset & unload current main project
	this.resetMainProject();

	// Unsubscribe from realtime updates
	socket.emit('unsubscribe');

};

// Switches to a newly selected file in the main viewer. If project and filename
// parameters are provided, they will be used. Otherwise, the project & file
// dropdown selections will be used.
GlobalStateManager.prototype.newMainFile = function(project='', filename='') {

	// Clear main file from the viewer
	this.clearMainFile();

	// Load newly selected file
	if (project === '' && filename === '') {
		let fileselect = document.getElementById('file_selection');
		this.currentFile = new File(this.currentProject.name, fileselect.options[fileselect.selectedIndex].value);
	} else {
		this.currentFile = new File(project, filename);
	}

};

// Switches to a newly selected project in the main viewer.
GlobalStateManager.prototype.newMainProject = function() {

	// Clear main project from the viewer
	this.clearMainProject();

	// Load newly selected project
	let projectselect = document.getElementById('project_selection');
	this.currentProject = new Project(projectselect.options[projectselect.selectedIndex].value);

	// Request the list of files for the project
	requestHandler.requestInitialProjectPayload(this.currentProject.name, function(data) {

		// Provide the projects template assets to TemplateSystem
		console.log(data['project_template'], data['interface_templates'])
		templateSystem.provideProjectTemplates(data['name'],
			(data.hasOwnProperty('project_template') && data['project_template'] ? JSON.parse(data['project_template']) : {}) || {},
			(data.hasOwnProperty('interface_templates') && data['interface_templates'] ? JSON.parse(data['interface_templates']) : {}) || {}
		);

		let fileSelect = document.getElementById('file_selection');

		for (let i in data['files']) {

			let opt = document.createElement('OPTION');
			opt.setAttribute('value', data['files'][i]);
			opt.innerText = data['files'][i];
			fileSelect.appendChild(opt);

		}

	});

};

// Reset file select & clear currently loaded file from the main viewer.
GlobalStateManager.prototype.resetMainFile = function() {

	// Clear main file from the viewer
	this.clearMainFile();

	// Set the file selection to the initial/default value.
	document.getElementById('file_selection').selectedIndex = 0;

};

// Reset project select & clear currently loaded project from the main viewer.
GlobalStateManager.prototype.resetMainProject = function() {

	// Reset main file
	this.resetMainFile();

	// Clear main project from the viewer
	this.clearMainProject();

	// Set the project selection to the initial/default value.
	document.getElementById('project_selection').selectedIndex = 0;

};
