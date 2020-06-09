'use strict';

// Class declaration
function GlobalStateManager() {

	// Holds the currently-selected project
	this.currentProject = null;

	// Holds the currently-selected file
	this.currentFile = null;

	// Length of time to display for realtime graphs, in seconds
	this.realtimeTimeWindow = 600;

	// Variable used to storage a file pending load
	this.filePendingLoad = null;

	// Holds incrementing graph identifier
	this.nextGraphIdentifier = 0

}

// Clear the main file currently loaded in the viewer
GlobalStateManager.prototype.clearFile = function() {

	// Clear current file if there is one
	if (this.currentFile !== null) {
		this.currentFile.destroy();
		this.currentFile = null;
	}

	// Clear the hash parameters
	window.location.hash = '';

};

// Clear the main project currently loaded in the viewer
GlobalStateManager.prototype.clearProject = function() {

	// Clear main file from the viewer.
	this.clearFile();

	// Clear contents of file select
	document.getElementById('file_selection').innerHTML = '<option></option>';

	// Set current project to null
	this.currentProject = null;

	// Clear the hash parameters
	window.location.hash = '';

};

GlobalStateManager.prototype.enterRealtimeMode = function() {

	// Add the realtime class name to body
	document.getElementsByTagName('body')[0].className = 'realtime';

	// Load the realtime main project
	//this.loadProject('__realtime__');
	this.resetProject();

	// Load the realtime file in the viewer
	this.loadFile('__realtime__', '__realtime__')

};

GlobalStateManager.prototype.exitRealtimeMode = function () {

	// Remove the realtime class name from body
	document.getElementsByTagName('body')[0].className = '';

	// Reset & unload current main project
	this.resetProject();

	// Unsubscribe from realtime updates
	socket.emit('unsubscribe');

};

// Returns a new unique graph identifier
GlobalStateManager.prototype.getGraphIdentifier = function() {
	return this.nextGraphIdentifier++;
};

// Switches to a newly selected file in the main viewer. If project and filename
// parameters are provided, they will be used. Otherwise, the project & file
// dropdown selections will be used. If a callback is provided, it will be
// passed to the File constructor and called when the file is fully loaded.
GlobalStateManager.prototype.loadFile = function(filename='', project='', callback=null) {

	// If empty variables were provided, grab the dropdown selections
	if (!project) {
		let projselect = document.getElementById('project_selection');
		project = projselect.options[projselect.selectedIndex].value;
	}
	if (!filename) {

		// If there's a file pending load, use that. Otherwise, use file-select.
		if (this.filePendingLoad) {
			filename = this.filePendingLoad;
			this.filePendingLoad = null;
		} else {
			let fileselect = document.getElementById('file_selection');
			filename = fileselect.options[fileselect.selectedIndex].value;
		}

	}

	// If the filename is still empty at this point, clear the file & we're done.
	if (!filename) {
		this.clearFile();
		return;
	}

	// If this file is already loaded, we need not take further action
	if (this.currentProject && project === this.currentProject.name && this.currentFile && filename === this.currentFile.filename) {
		return false;
	}

	// Clear main file from the viewer
	this.clearFile();

	// If the project needs to be loaded first, load the project with this
	// function as a callback.
	if (!this.currentProject || project !== this.currentProject.name) {
		this.filePendingLoad = filename;
		this.loadProject(project, this.loadFile.bind(this));
		return;
	}

	// Change the selection & re-render the select-picker
	let fs = $('#file_selection');
	fs.val(filename);
	fs.selectpicker('refresh');

	// Load the file
	this.currentFile = new File(project, filename, callback);

	// Set hash parameters
	window.location.hash = "project="+project+"&file="+filename;

	return true;

};

// Switches to a newly selected project in the main viewer.
GlobalStateManager.prototype.loadProject = function(project='', callback=null) {

	// If empty project variable was provided, grab the dropdown selection
	if (project === '') {
		let projselect = document.getElementById('project_selection');
		project = projselect.options[projselect.selectedIndex].value;
	}

	// If the project is already loaded, we need not take further action
	if (this.currentProject && project === this.currentProject.name) {
		return false;
	}

	// Clear main project from the viewer
	this.clearProject();

	// Change the selection & re-render the select-picker
	let ps = $('#project_selection');
	ps.val(project);
	ps.selectpicker('refresh');

	// Load new project
	this.currentProject = new Project(project, callback);

	return true;

};

// Reset file select & clear currently loaded file from the main viewer.
GlobalStateManager.prototype.resetFile = function() {

	// Clear main file from the viewer
	this.clearFile();

	// Set the file selection to the initial/default value.
	document.getElementById('file_selection').selectedIndex = 0;

	// Re-render the select-picker
	$('#file_selection').selectpicker('refresh');

};

// Reset project select & clear currently loaded project from the main viewer.
GlobalStateManager.prototype.resetProject = function() {

	// Reset main file
	this.resetFile();

	// Clear main project from the viewer
	this.clearProject();

	// Set the project selection to the initial/default value.
	document.getElementById('project_selection').selectedIndex = 0;

};
