var config = {

	// Enable verbose debug output
	verbose: true,

	// Function for assembling paths. Do not modify unless necessary.
	buildDir: function(dir) { return serverProtocol+serverAddress+serverPort+rootDir+dir; },
	
	// Backend address & port
	serverProtocol: 'http://',
	serverAddress: 'localhost',
	serverPort: '8001',

	// A root directory structure from which the backend application is served.
	// Should have a leading but not a trailing slash. If no root directory,
	// should be single slash. Examples:
	//   '/approot'
	//   '/app/rooot'
	//   '/'
	rootDir: '/auv',
	
	// Backend request URLs
	allSeriesAllDataURL: buildDir('/all_data_all_series'),
	dataWindowAllSeriesURL: buildDir('/data_window_all_series'),
	dataWindowSingleSeriesURL: buildDir('/data_window_single_series'),
	getAlertsURL: buildDir('/get_alerts'),
	getFilesURL: buildDir('/get_files'),
	
	// Series to display by default
	// defaultSeries: ['HR', 'RR', 'BP', 'SpO2', 'CVP', 'ArtWave'],
	defaultSeries: ['Numeric: HR.BeatToBeat', 'Numeric: RR.RR', 'Numeric: ART.Systolic', 'Numeric: ART.Diastolic', 'Numeric: SpO₂.SpO₂', 'CVP', 'ArtWave']
	
};