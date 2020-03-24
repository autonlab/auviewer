'use strict';

function TemplateSystem() {
	
	// Default placeholders
	this.builtin_default_project_template = {};
	this.builtin_default_interface_templates = {};
	this.builtin_default_series_template = {};
	this.global_default_project_template = {};
	this.global_default_interface_templates = {};
	this.global_default_series_template = {};

	// Holds all project assets (project and project interface templates).
	this.project_templates = {};

	// Holds a cache of project & series configs.
	this.cached_templates = {};

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

			// Built-in default project template
			this.builtin_default_project_template,

			// Global default project template
			this.global_default_project_template,

			// The specific-project template
			(verifyObjectPropertyChain(this.project_templates, [projectName, 'project_template']) ? this.project_templates[projectName]['project_template'] : {}),

			// Any system-pushed specific-project template
			...(verifyObjectPropertyChain(this.dynamic, ['project_templates', projectName, '[]']) ? this.dynamic['project_templates'][projectName] : [])

		);

	} catch (err) {
		console.log("Error merging project template", err);
		project_template = this.builtin_default_project_template || {};
	}

	// The project template does not need the series definitions.
	if (project_template.hasOwnProperty('series')) {
		delete project_template['series'];
	}

	// Cache the newly-generated project template
	if (!this.cached_templates.hasOwnProperty(projectName)) {
		this.cached_templates[projectName] = {};
	}
	this.cached_templates[projectName]['project_template'] = project_template;

	globalAppConfig.verbose && console.log("TemplateSystem.generateProjectTemplate() returning", project_template);

	return project_template;

};

// Class-internal helper function to generate, cache, and return series template.
TemplateSystem.prototype.generateSeriesTemplate = function(projectName, seriesName) {

	// Holds the series template we will return.
	let series_template;

	// Attempt to generate a new merged template
	try {

		series_template = mergeDeep({},

			// The built-in default series template
			this.builtin_default_series_template,

			// The global default series template
			this.global_default_series_template,

			// The specific-project default series template
			(verifyObjectPropertyChain(this.project_templates, [projectName, 'project_template', 'series', 'default']) ? this.project_templates[projectName]['project_template']['series']['default'] : {}),

			// Any system-pushed specific-project default series templates
			...(verifyObjectPropertyChain(this.dynamic, ['project_templates', projectName, '[]']) ? this.dynamic['project_templates'][projectName].filter(proj => proj.hasOwnProperty('series') && proj['series'].hasOwnProperty('default')).map(proj => proj['series']['default']) : []),

			// The built-in default-project specific-series template
			(verifyObjectPropertyChain(this.builtin_default_project_template, ['series', seriesName]) ? this.builtin_default_project_template['series'][seriesName] : {}),

			// The global default-project specific-series template
			(verifyObjectPropertyChain(this.global_default_project_template, ['series', seriesName]) ? this.global_default_project_template['series'][seriesName] : {}),

			// The specific-project specific-series template
			(verifyObjectPropertyChain(this.project_templates, [projectName, 'project_template', 'series', seriesName]) ? this.project_templates[projectName]['project_template']['series'][seriesName] : {}),

			// Any system-pushed specific-project specific-series templates
			...(verifyObjectPropertyChain(this.dynamic, ['project_templates', projectName, '[]']) ? this.dynamic['project_templates'][projectName].filter(proj => proj.hasOwnProperty('series') && proj['series'].hasOwnProperty(seriesName)).map(proj => proj['series'][seriesName]) : [])
		);

	} catch (err) {
		console.log("Error merging series template", err);
		series_template = this.builtin_default_series_template || {};
	}

	// Cache the newly-generated series template
	if (!this.cached_templates.hasOwnProperty(projectName)) {
		this.cached_templates[projectName] = {};
	}
	if (!this.cached_templates[projectName].hasOwnProperty('series')) {
		this.cached_templates[projectName]['series'] = {};
	}
	this.cached_templates[projectName]['series'][seriesName] = series_template;

	// globalAppConfig.verbose && console.log("TemplateSystem.getSeriesTemplate("+seriesName+") returning", deepCopy(series_template));

	return series_template;

};

// Returns the final processed/merged template for the project.
TemplateSystem.prototype.getProjectTemplate = function(projectName) {
	return ( verifyObjectPropertyChain(this.cached_templates, [projectName, 'project_template']) ? this.cached_templates[projectName]['project_template'] : this.generateProjectTemplate(projectName) );
};

// Returns the final processed/merged template for the series.
TemplateSystem.prototype.getSeriesTemplate = function(projectName, seriesName) {
	return ( verifyObjectPropertyChain(this.cached_templates, [projectName, 'series', seriesName]) ? this.cached_templates[projectName]['series'][seriesName] : this.generateSeriesTemplate(projectName, seriesName) );
};

// Provide builtin templates.
TemplateSystem.prototype.provideBuiltinTemplates = function(builtin_default_project_template, builtin_default_interface_templates) {
	this.builtin_default_project_template = builtin_default_project_template || {};
	this.builtin_default_series_template = (verifyObjectPropertyChain(builtin_default_project_template, ['series', 'default']) ? builtin_default_project_template['series']['default'] : {}) || {};
	this.builtin_default_interface_templates = builtin_default_interface_templates || {};
	globalAppConfig.verbose && console.log('TemplateSystem.provideBuiltinTemplates set builtin default project, series, and interface templates:', this.builtin_default_project_template, this.builtin_default_series_template, this.builtin_default_interface_templates);
};

// Provide global templates.
TemplateSystem.prototype.provideGlobalTemplates = function(global_default_project_template, global_default_interface_templates) {
	this.global_default_project_template = global_default_project_template || {};
	this.global_default_series_template = (verifyObjectPropertyChain(global_default_project_template, ['series', 'default']) ? global_default_project_template['series']['default'] : {}) || {};
	this.global_default_interface_templates = global_default_interface_templates || {};
	globalAppConfig.verbose && console.log('TemplateSystem.provideGlobalTemplates set global default project, series, and interface templates:', this.global_default_project_template, this.global_default_series_template, this.global_default_interface_templates);
};

// Provide a project's template and interface templates to TemplateSystem in the
// form of unparsed JSON strings.
TemplateSystem.prototype.provideProjectTemplates = function(name, project_template, interface_templates) {

	this.project_templates[name] = {
		'project_template': project_template || {},
		'interface_templates': interface_templates || {}
	};

};

// Provide a template from a dynamic source (i.e. a template received from a
// push from the server). There are four types of templates that may be provided:
// global, project, interface, and project_interface. The type will be inferred
// from the presence of the optional parameters project & intfc. If neither
// is provided, it's global; the rest can be deduced.
TemplateSystem.prototype.providePushTemplate = function(template, project='', intfc='') {

	// Log the request
	globalAppConfig.verbose && console.log('TemplateSystem.providePushTemplate received project:', project, 'intfc:', intfc, 'template:', deepCopy(template));

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

	// Log the new dynamic templates.
	globalAppConfig.verbose && console.log('After push template add:', deepCopy(this.dynamic));

};