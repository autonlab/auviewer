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
	submitVoteSegmentsURL: 'create_vote_segments',
	deleteVoteSegmentsURL: 'delete_vote_segments',
	detectPatternsURL: 'detect_patterns',
	featurizeURL: 'featurize',
	initialFilePayloadURL: 'initial_file_payload',
	uploadCustomSegmentsURL: 'upload_custom_segments',
	initialSupervisorPayloadURL: 'initial_supervisor_payload',
	initialEvaluatorPayloadURL: 'initial_evaluator_payload',
	requestLabelerStatsURL: 'get_labeler_statistics',
	querySupervisorSeriesURL: 'query_supervisor_series',
	getVotesURL: 'get_votes',
	getSegmentsURL: 'get_segments',
	getProjectAnnotationsURL: 'get_project_annotations',
	seriesRangedDataURL: 'series_ranged_data',
	updateAnnotationURL: 'update_annotation',
	getLabelersURL: 'get_labelers',
	getLabelsURL: 'get_labels'
	
};