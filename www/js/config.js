'use strict';

let globalAppConfig = {

	// Enable verbose debug output
	verbose: false,

	// Maximum data points to hold per data series for realtime mode
	M: 3000,

	// Report (in the browser console) performance times above this threshold,
	// in milliseconds.
	performanceReportingThresholdMS: 100,
	
	// Backend request URLs
	createAnnotationURL: 'create_annotation',
	deleteAnnotationURL: 'delete_annotation',
	detectAnomaliesURL: 'detect_anomalies',
	initialProjectPayloadURL: 'initial_project_payload',
	getProjectsURL: 'get_projects',
	initialFilePayloadURL: 'initial_file_payload',
	seriesRangedDataURL: 'series_ranged_data',
	updateAnnotationURL: 'update_annotation',
	
};
