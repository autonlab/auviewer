'use strict';

/*
The TemplateSystem manages the hierarchical templates for interfaces, projects, and series. There are two tiers of
hierarchy. The first is builtin -> global. The second is project -> interface -> series.
 */

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
TemplateSystem.prototype.generateProjectTemplate = function(project_id) {

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
			(verifyObjectPropertyChain(this.project_templates, [project_id, 'project_template']) ? this.project_templates[project_id]['project_template'] : {}),

			// Any system-pushed specific-project template
			...(verifyObjectPropertyChain(this.dynamic, ['project_templates', project_id, '[]']) ? this.dynamic['project_templates'][project_id] : [])

		);

	} catch (err) {
		console.log("Error merging project template", err);
		project_template = this.builtin_default_project_template || {};
	}

	// The project template does not need the series definitions.
	// TODO: Temporarily disabling this
	// if (project_template.hasOwnProperty('series')) {
	// 	delete project_template['series'];
	// }

	// Cache the newly-generated project template
	if (!this.cached_templates.hasOwnProperty(project_id)) {
		this.cached_templates[project_id] = {};
	}
	this.cached_templates[project_id]['project_template'] = project_template;

	globalAppConfig.verbose && console.log("TemplateSystem.generateProjectTemplate() returning", project_template);

	return project_template;

};

// Class-internal helper function to generate, cache, and return series template.
TemplateSystem.prototype.generateSeriesTemplate = function(project_id, seriesName) {

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
			(verifyObjectPropertyChain(this.project_templates, [project_id, 'project_template', 'series', '_default']) ? this.project_templates[project_id]['project_template']['series']['_default'] : {}),

			// Any system-pushed specific-project default series templates
			...(verifyObjectPropertyChain(this.dynamic, ['project_templates', project_id, '[]']) ? this.dynamic['project_templates'][project_id].filter(proj => proj.hasOwnProperty('series') && proj['series'].hasOwnProperty('_default')).map(proj => proj['series']['_default']) : []),

			// The built-in default-project specific-series template
			(verifyObjectPropertyChain(this.builtin_default_project_template, ['series', seriesName]) ? this.builtin_default_project_template['series'][seriesName] : {}),

			// The global default-project specific-series template
			(verifyObjectPropertyChain(this.global_default_project_template, ['series', seriesName]) ? this.global_default_project_template['series'][seriesName] : {}),

			// The specific-project specific-series template
			(verifyObjectPropertyChain(this.project_templates, [project_id, 'project_template', 'series', seriesName]) ? this.project_templates[project_id]['project_template']['series'][seriesName] : {}),

			// Any system-pushed specific-project specific-series templates
			...(verifyObjectPropertyChain(this.dynamic, ['project_templates', project_id, '[]']) ? this.dynamic['project_templates'][project_id].filter(proj => proj.hasOwnProperty('series') && proj['series'].hasOwnProperty(seriesName)).map(proj => proj['series'][seriesName]) : [])
		);

	} catch (err) {
		console.log("Error merging series template", err);
		series_template = this.builtin_default_series_template || {};
	}

	// Cache the newly-generated series template
	if (!this.cached_templates.hasOwnProperty(project_id)) {
		this.cached_templates[project_id] = {};
	}
	if (!this.cached_templates[project_id].hasOwnProperty('series')) {
		this.cached_templates[project_id]['series'] = {};
	}
	this.cached_templates[project_id]['series'][seriesName] = series_template;

	// globalAppConfig.verbose && console.log("TemplateSystem.getSeriesTemplate("+seriesName+") returning", deepCopy(series_template));

	return series_template;

};

// Returns the final processed/merged template for the project.
TemplateSystem.prototype.getProjectTemplate = function(project_id) {
	return ( verifyObjectPropertyChain(this.cached_templates, [project_id, 'project_template']) ? this.cached_templates[project_id]['project_template'] : this.generateProjectTemplate(project_id) );
};

// Returns the final processed/merged template for the series.
TemplateSystem.prototype.getSeriesTemplate = function(project_id, seriesName) {
	return ( verifyObjectPropertyChain(this.cached_templates, [project_id, 'series', seriesName]) ? this.cached_templates[project_id]['series'][seriesName] : this.generateSeriesTemplate(project_id, seriesName) );
};

// Provide builtin templates.
TemplateSystem.prototype.provideBuiltinTemplates = function(builtin_default_project_template, builtin_default_interface_templates) {

	let t0 = performance.now();

	this.builtin_default_project_template = builtin_default_project_template || {};
	this.builtin_default_series_template = (verifyObjectPropertyChain(builtin_default_project_template, ['series', '_default']) ? builtin_default_project_template['series']['_default'] : {}) || {};
	this.builtin_default_interface_templates = builtin_default_interface_templates || {};
	globalAppConfig.verbose && console.log('TemplateSystem.provideBuiltinTemplates set builtin default project, series, and interface templates:', this.builtin_default_project_template, this.builtin_default_series_template, this.builtin_default_interface_templates);

	let tt = performance.now() - t0;

	globalAppConfig.performance && tt > globalAppConfig.performanceReportingThresholdTemplateSystem && console.log("TemplateSystem.provideBuiltinTemplates() took " + Math.round(tt) + "ms.");
};

// Provide global templates.
TemplateSystem.prototype.provideGlobalTemplates = function(global_default_project_template, global_default_interface_templates) {

	let t0 = performance.now();

	this.global_default_project_template = global_default_project_template || {};
	this.global_default_series_template = (verifyObjectPropertyChain(global_default_project_template, ['series', '_default']) ? global_default_project_template['series']['_default'] : {}) || {};
	this.global_default_interface_templates = global_default_interface_templates || {};
	globalAppConfig.verbose && console.log('TemplateSystem.provideGlobalTemplates set global default project, series, and interface templates:', this.global_default_project_template, this.global_default_series_template, this.global_default_interface_templates);

	let tt = performance.now() - t0;

	globalAppConfig.performance && tt > globalAppConfig.performanceReportingThresholdTemplateSystem && console.log("TemplateSystem.provideGlobalTemplates() took " + Math.round(tt) + "ms.");

};

// Provide a project's template and interface templates to TemplateSystem in the
// form of unparsed JSON strings.
TemplateSystem.prototype.provideProjectTemplates = function(name, project_template, interface_templates) {

	let t0 = performance.now();

	this.project_templates[name] = {
		'project_template': project_template || {},
		'interface_templates': interface_templates || {}
	};
	globalAppConfig.verbose && console.log('TemplateSystem.provideProjectTemplates set project "'+name+'" template:', this.project_templates[name]);

	let tt = performance.now() - t0;

	globalAppConfig.performance && tt > globalAppConfig.performanceReportingThresholdTemplateSystem && console.log("TemplateSystem.provideProjectTempaltes() took " + Math.round(tt) + "ms.");

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
	globalAppConfig.verbose && console.log('Results after push template add:', deepCopy(this.dynamic));

};