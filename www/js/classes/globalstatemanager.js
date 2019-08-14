'use strict';

function GlobalStateManager() {

	// Holds the currently-selected file
	this.currentFile = null;

}

GlobalStateManager.prototype.newMainFile = function() {

	if (this.currentFile !== null) {
		this.currentFile.destroy();
	}

	let fileselect = document.getElementById('file_selection');
	this.currentFile = new File(fileselect.options[fileselect.selectedIndex].value);

};