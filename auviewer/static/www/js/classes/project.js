'use strict';

function Project(projname, callback=null) {

	// Holds the project name
	this.name = projname;

	// Holds the user's annotations across all files in the project
	this.annotations = null;

	// Request the list of files for the project
	requestHandler.requestInitialProjectPayload(this.name, function(data) {

		// Provide the projects template assets to TemplateSystem
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

		// Re-render the select-picker
		$(fileSelect).selectpicker('refresh');

		// If a callback was requested (provided to the File class
		// initializer), call it.
		if (callback) {
			callback();
		}

	});

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
