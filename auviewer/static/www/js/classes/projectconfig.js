'use strict'

function ProjectConfig () {

	this.projects = {};

	this.defaultConfig = JSON.parse()

}

ProjectConfig.prototype.get = function(project_name) {

	if (this.projects.hasOwnProperty(project_name)) {
		return this.projects[project_name];
	} else {

	}

};