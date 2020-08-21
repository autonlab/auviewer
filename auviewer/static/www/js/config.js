'use strict';

let globalAppConfig = {

	// Enable verbose and/or performance debug output
	verbose: true,
	performance: true,

	// Maximum data points to hold per data series for realtime mode
	M: 3000,

	// Performance reporting thresholds, in milliseconds.
	performanceReportingThresholdGeneral: 100,
	performanceReportingThresholdTemplateSystem: 5,

	// Backend request URLs
	createAnnotationURL: 'create_annotation',
	deleteAnnotationURL: 'delete_annotation',
	detectPatternsURL: 'detect_patterns',
	initialFilePayloadURL: 'initial_file_payload',
	getProjectAnnotationsURL: 'get_project_annotations',
	seriesRangedDataURL: 'series_ranged_data',
	updateAnnotationURL: 'update_annotation',
	
};
