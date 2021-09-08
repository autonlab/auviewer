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
	updateThresholdURL: 'update_threshold',
	previewThresholdsURL: 'preview_threshold_change',
	detectPatternsURL: 'detect_patterns',
	featurizeURL: 'featurize',
	initialFilePayloadURL: 'initial_file_payload',
	createSupervisorPrecomputerUrl: 'create_supervisor_precomputer',
	initialSupervisorPayloadURL: 'initial_supervisor_payload',
	querySupervisorSeriesURL: 'query_supervisor_series',
	updateSupervisorTimeSegmentURL: 'update_supervisor_time_segment',
	getProjectAnnotationsURL: 'get_project_annotations',
	seriesRangedDataURL: 'series_ranged_data',
	updateAnnotationURL: 'update_annotation',
	
};
