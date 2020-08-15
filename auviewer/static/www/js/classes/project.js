'use strict';

function Project(id, projname) {

	// Project name & id
	this.id = id;
	this.name = projname;

	// Holds the user's annotations across all files in the project
	this.annotations = null;

}

Project.prototype.getAnnotations = function(callback=null) {

	requestHandler.requestProjectAnnotations(this.name, (function(data) {

		// Initialize the project annotations to an array
		this.annotations = [];

		// Populate the project annotations
		if (Array.isArray(data) && data.length > 0) {
			for (let a of data) {
				this.annotations.push(new Annotation({valuesArrayFromBackend: a}, 'existing'));
			}
		}

		// Call callback if provided
		if (callback) {
			callback();
		}

	}).bind(this));

};
