'use strict';

/*
The GlobalStateManager is a global singleton that manages application state.
 */

// Class declaration
function GlobalStateManager() {

	// Holds the currently-selected project
	this.currentProject = null;

	// Holds the currently-selected file
	this.currentFile = null;

	// Length of time to display for realtime graphs, in seconds
	this.realtimeTimeWindow = 600;

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

};

// Returns a new unique graph identifier
GlobalStateManager.prototype.getGraphIdentifier = function() {
	return this.nextGraphIdentifier++;
};

// Switches to a newly selected file in the main viewer. If project and filename
// parameters are provided, they will be used. Otherwise, the project & file
// dropdown selections will be used. If a callback is provided, it will be
// passed to the File constructor and called when the file is fully loaded.
GlobalStateManager.prototype.loadFile = function(id='', callback=null) {

	// If file ID is empty, grab the dropdown selection
	if (!id) {
		let fileselect = document.getElementById('file_selection');
		id = fileselect.options[fileselect.selectedIndex].value;
	}

	// If the file ID is still empty at this point, clear the file & we're done.
	if (!id) {
		this.clearFile();
		return false;
	}

	// If this file is already loaded, we need not take further action
	if (this.currentFile && id === this.currentFile.id) {
		return false;
	}

	// Clear main file from the viewer
	this.clearFile();

	// Change the selection & re-render the select-picker
	let fs = $('#file_selection');
	fs.val(id);
	fs.selectpicker('refresh');

	// Load the file
	this.currentFile = new File(this.currentProject, Number(id), callback);

	// Set hash parameters
	window.location.hash = "file_id="+id;

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
