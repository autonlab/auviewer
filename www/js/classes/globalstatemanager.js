'use strict';

// Class declaration
function GlobalStateManager() {

	// Holds the currently-selected project
	this.currentProject = null;

	// Holds the currently-selected file
	this.currentFile = null;

}

// Switches to a newly selected file in the main viewer.
GlobalStateManager.prototype.newMainFile = function() {

	if (this.currentFile !== null) {
		this.currentFile.destroy();
	}

	let fileselect = document.getElementById('file_selection');
	this.currentFile = new File(this.currentProject.name, fileselect.options[fileselect.selectedIndex].value);

};

// Switches to a newly selected project in the main viewer.
GlobalStateManager.prototype.newMainProject = function() {

	// Clear current file if there is one
	if (this.currentFile !== null) {
		this.currentFile.destroy();
	}

	let fileSelect = document.getElementById('file_selection');

	// Clear contents of file select
	document.getElementById('file_selection').innerHTML = '<option></option>';

	let projectselect = document.getElementById('project_selection');
	this.currentProject = new Project(projectselect.options[projectselect.selectedIndex].value);

	// Request the list of files for the project
	requestHandler.requestFileList(this.currentProject.name, function(data) {

		for (let i in data) {

			let opt = document.createElement('OPTION');
			opt.setAttribute('value', data[i]);
			opt.innerText = data[i];
			fileSelect.appendChild(opt);

		}

	});

};