'use strict';

let config = {

	// Enable verbose debug output
	verbose: true,

	// Maximum data points to hold per data series for realtime mode
	M: 3000,

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
	getFilesSubpath: '/get_files',
	getProjectsSubpath: '/get_projects',
	initialFilePayloadSubpath: '/initial_file_payload',
	seriesRangedDataSubpath: '/series_ranged_data',
	updateAnnotationSubpath: '/update_annotation',
	
};

config.createAnnotationURL = config.buildDir(config.createAnnotationSubpath);
config.deleteAnnotationURL = config.buildDir(config.deleteAnnotationSubpath);
config.detectAnomaliesURL = config.buildDir(config.detectAnomaliesSubpath);
config.getFilesURL = config.buildDir(config.getFilesSubpath);
config.getProjectsURL = config.buildDir(config.getProjectsSubpath);
config.initialFilePayloadURL = config.buildDir(config.initialFilePayloadSubpath);
config.seriesRangedDataURL = config.buildDir(config.seriesRangedDataSubpath);
config.updateAnnotationURL = config.buildDir(config.updateAnnotationSubpath);