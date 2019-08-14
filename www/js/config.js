'use strict';

let config = {

	// Enable verbose debug output
	verbose: true,

	// Function for assembling paths. Do not modify unless necessary.
	buildDir: function(subpath) { return this.serverProtocol+this.serverAddress+':'+this.serverPort+this.rootWebPath+subpath; },
	
	// Backend address & port
	serverProtocol: 'http://',
	serverAddress: 'localhost',
	serverPort: '8001',

	// A root directory structure from which the backend application is served.
	// Should have a leading but not a trailing slash. If no root directory,
	// should be empty string. Examples:
	//   '/approot'
	//   '/app/rooot'
	//   ''
	// rootWebPath: '/auv',
	rootWebPath: '',
	
	// Backend request URLs
	allSeriesAllDataSubpath: '/all_data_all_series',
	dataWindowAllSeriesSubpath: '/data_window_all_series',
	dataWindowSingleSeriesSubpath: '/data_window_single_series',
	getAlertsSubpath: '/get_alerts',
	getFilesSubpath: '/get_files',
	
	// Series to display by default
	// defaultSeries: ['HR', 'RR', 'BP', 'SpO2', 'CVP', 'ArtWave'],
	defaultSeries: ['Numeric: HR.BeatToBeat', 'Numeric: RR.RR', 'Numeric: ART.Systolic', 'Numeric: ART.Diastolic', 'Numeric: SpO₂.SpO₂', 'CVP', 'ArtWave']
	
};

config.allSeriesAllDataURL = config.buildDir(config.allSeriesAllDataSubpath);
config.dataWindowAllSeriesURL = config.buildDir(config.dataWindowAllSeriesSubpath);
config.dataWindowSingleSeriesURL = config.buildDir(config.dataWindowSingleSeriesSubpath);
config.getAlertsURL = config.buildDir(config.getAlertsSubpath);
config.getFilesURL = config.buildDir(config.getFilesSubpath);