'use strict';

function TemplateSystem(default_project_config, default_interfaces_config) {

	// Attach the default configs
	this.default_project_template = default_project_config;
	this.default_series_template = (default_project_config.hasOwnProperty('series') && default_project_config['series'].hasOwnProperty('default') ? default_project_config['series']['default'] : {});
	this.default_interfaces_templates = default_interfaces_config;

	// Holds all project assets (project and project interface templates).
	this.projects = {};

	// Holds a cache of project & series configs.
	this.cache = {};

	// Holds dynamic templates that are propagated by an agent through the server
	this.dynamic = {
		global_templates: [],
		project_templates: {},
		interface_templates: {},
		project_interface_templates: {}
	};

}

// Class-internal helper function to generate, cache, and return project template.
TemplateSystem.prototype.generateProjectTemplate = function(projectName) {

	// Holds the project template we will return.
	let project_template;

	// Attempt to generate a new merged template
	try {
		project_template = mergeDeep({},
			this.default_project_config,
			(verifyObjectPropertyChain(this.projects, [projectName, 'project_template']) ? this.projects[projectName]['project_template'] : {})
		);
	} catch (err) {
		console.log("Error merging project template", err);
		project_template = this.default_project_template || {};
	}

	// The project template does not need the series definitions.
	if (project_template.hasOwnProperty('series')) {
		delete project_template['series'];
	}

	// Cache the newly-generated project template
	if (!this.cache.hasOwnProperty(projectName)) {
		this.cache[projectName] = {};
	}
	this.cache[projectName]['project_template'] = project_template;

	vo("TemplateSystem.generateProjectTemplate() returning", project_template);

	return project_template;

};

// Class-internal helper function to generate, cache, and return series template.
TemplateSystem.prototype.generateSeriesTemplate = function(projectName, seriesName) {

	// Holds the series template we will return.
	let series_template;

	// Attempt to generate a new merged template
	try {
		series_template = mergeDeep({},
			this.default_series_template,
			(verifyObjectPropertyChain(this.projects, [projectName, 'project_template', 'series', 'default']) ? this.projects[projectName]['project_template']['series']['default'] : {}),
			(verifyObjectPropertyChain(this.projects, [projectName, 'project_template', 'series', seriesName]) ? this.projects[projectName]['project_template']['series'][seriesName] : {})
		);
	} catch (err) {
		console.log("Error merging series template", err);
		series_template = this.default_series_template || {};
	}

	// Cache the newly-generated series template
	if (!this.cache.hasOwnProperty(projectName)) {
		this.cache[projectName] = {};
	}
	if (!this.cache[projectName].hasOwnProperty('series')) {
		this.cache[projectName]['series'] = {};
	}
	this.cache[projectName]['series'][seriesName] = series_template;

	vo("TemplateSystem.getSeriesTemplate() returning", series_template);

	return series_template;

};

// Returns the final processed/merged template for the project.
TemplateSystem.prototype.getProjectTemplate = function(projectName) {
	return ( verifyObjectPropertyChain(this.cache, [projectName, 'project_template']) ? this.cache[projectName]['project_template'] : this.generateProjectTemplate(projectName) );
};

// Returns the final processed/merged template for the series.
TemplateSystem.prototype.getSeriesTemplate = function(projectName, seriesName) {
	return ( verifyObjectPropertyChain(this.cache, [projectName, 'series', seriesName]) ? this.cache[projectName]['series'][seriesName] : this.generateSeriesTemplate(projectName, seriesName) );
};

// Provide a project's template and interface templates to TemplateSystem in the
// form of unparsed JSON strings.
TemplateSystem.prototype.provideProjectTemplates = function(name, project_template, interface_templates) {

	this.projects[name] = {
		'project_template': JSON.parse(project_template) || {},
		'interface_templates': JSON.parse(interface_templates) || {}
	};

	console.log(this);

};

// Provide a template from a dynamic source (i.e. a template received from a
// push from the server. There are four types of templates that may be provided:
// global, project, interface, and project_interface. The type will be inferred
// from the presence of the optional parameters project & intfc. If neither
// is provided, it's global; the rest can be deduced.
TemplateSystem.prototype.provideDynamicTemplate = function(type, template, project='', intfc='') {

	// TODO(gus): Add template structure check

	if (!project && !intfc) {
		// Global template
		this.dynamic.global_templates.push(template);
	}
	else if (project) {
		// Project template
		if (!verifyObjectPropertyChain(this.dynamic.project_templates, [project])) {
			this.dynamic.project_templates[project] = [];
		}
		this.dynamic.project_templates[project].push(template);

	}
	else if (intfc) {
		// Interface template
		if (!verifyObjectPropertyChain(this.dynamic.interface_templates, [intfc])) {
			this.dynamic.interface_templates[intfc] = {};
		}
		this.dynamic.interface_templates[intfc].push(template);
	}
	else {
		// Project interface template
		if (!verifyObjectPropertyChain(this.dynamic.project_interface_templates, [project])) {
			this.dynamic.project_interface_templates[project] = {};
		}
		if (!verifyObjectPropertyChain(this.dynamic.project_interface_templates[project], [intfc])) {
			this.dynamic.project_interface_templates[project][intfc] = [];
		}
		this.dynamic.project_interface_templates[project][intfc].push(template);
	}

};