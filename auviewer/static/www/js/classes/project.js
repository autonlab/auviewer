'use strict';

/*
The Project class manages a project.
 */

function Project(payload) {

	// Project name & id
	this.id = payload['project_id'];
	this.name = payload['project_name'];

	// Populate the file dropdown select-picker
	let fileSelect = document.getElementById('file_selection');
	for (const f of payload['project_files']) {
		let opt = document.createElement('OPTION');
		opt.setAttribute('value', f[0]);
		opt.innerText = f[1];
		fileSelect.appendChild(opt);
	}
	$(fileSelect).selectpicker('refresh');

	// Provide the built-in template assets to TemplateSystem
	templateSystem.provideBuiltinTemplates(
		(payload.hasOwnProperty('builtin_default_project_template') && payload['builtin_default_project_template'] ? JSON.parse(payload['builtin_default_project_template']) : {}) || {},
		(payload.hasOwnProperty('builtin_default_interface_templates') && payload['builtin_default_interface_templates'] ? JSON.parse(payload['builtin_default_interface_templates']) : {}) || {},
	);

	// Provide the global template assets to TemplateSystem
	templateSystem.provideGlobalTemplates(
		(payload.hasOwnProperty('global_default_project_template') && payload['global_default_project_template'] ? JSON.parse(payload['global_default_project_template']) : {}) || {},
		(payload.hasOwnProperty('global_default_interface_templates') && payload['global_default_interface_templates'] ? JSON.parse(payload['global_default_interface_templates']) : {}) || {},
	);

	// Provide the projects template assets to TemplateSystem
	templateSystem.provideProjectTemplates(payload['project_id'],
		(payload.hasOwnProperty('project_template') && payload['project_template'] ? JSON.parse(payload['project_template']) : {}) || {},
		(payload.hasOwnProperty('interface_templates') && payload['interface_templates'] ? JSON.parse(payload['interface_templates']) : {}) || {}
	);

	// Holds the user's annotations across all files in the project
	this.annotations = null;

	// Instantiate the assignment manager
	this.assignmentsManager = new AssignmentsManager(this, payload['project_assignments']);

}

Project.prototype.getAnnotations = function(callback=null) {

	requestHandler.requestProjectAnnotations(this.id, (function(data) {

		// Initialize the project annotations to an array
		this.annotations = [];

		// Populate the project annotations
		if (Array.isArray(data) && data.length > 0) {
			for (let a of data) {
				this.annotations.push(new Annotation({valuesArrayFromBackend: a}, 'annotation'));
			}
		}

		// Call callback if provided
		if (callback) {
			callback();
		}

	}).bind(this));

};
