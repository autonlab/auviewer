'use strict';

let globalAppConfig = {

	// Enable verbose debug output
	verbose: false,

	// Maximum data points to hold per data series for realtime mode
	M: 3000,

	// Report (in the browser console) performance times above this threshold,
	// in milliseconds.
	performanceReportingThresholdMS: 100,

	// Function for assembling paths. Do not modify unless necessary.
	// buildDir: function(subpath) { return this.serverProtocol+this.serverAddress+':'+this.serverPort+this.rootWebPath+subpath; },
	buildDir: function(subpath) { return this.rootWebPath+subpath; },
	
	// Backend address & port
	// serverProtocol: 'http://',
	// serverAddress: 'localhost',
	// serverPort: '8001',

	// A root directory structure from which the backend application is served.
	// Should have a leading but not a trailing slash. If no root directory,
	// should be empty string. You must also change the corresponding setting
	// in config.py. Examples:
	//   '/approot'
	//   '/app/root'
	//   ''
	rootWebPath: '',
	
	// Backend request URLs
	createAnnotationSubpath: '/create_annotation',
	deleteAnnotationSubpath: '/delete_annotation',
	detectAnomaliesSubpath: '/detect_anomalies',
	initialProjectPayloadSubpath: '/initial_project_payload',
	getProjectsSubpath: '/get_projects',
	initialFilePayloadSubpath: '/initial_file_payload',
	seriesRangedDataSubpath: '/series_ranged_data',
	updateAnnotationSubpath: '/update_annotation',
	
};

globalAppConfig.createAnnotationURL = globalAppConfig.buildDir(globalAppConfig.createAnnotationSubpath);
globalAppConfig.deleteAnnotationURL = globalAppConfig.buildDir(globalAppConfig.deleteAnnotationSubpath);
globalAppConfig.detectAnomaliesURL = globalAppConfig.buildDir(globalAppConfig.detectAnomaliesSubpath);
globalAppConfig.initialProjectPayloadURL = globalAppConfig.buildDir(globalAppConfig.initialProjectPayloadSubpath);
globalAppConfig.getProjectsURL = globalAppConfig.buildDir(globalAppConfig.getProjectsSubpath);
globalAppConfig.initialFilePayloadURL = globalAppConfig.buildDir(globalAppConfig.initialFilePayloadSubpath);
globalAppConfig.seriesRangedDataURL = globalAppConfig.buildDir(globalAppConfig.seriesRangedDataSubpath);
globalAppConfig.updateAnnotationURL = globalAppConfig.buildDir(globalAppConfig.updateAnnotationSubpath);