'use strict';

let config = {

	// Enable verbose debug output
	verbose: true,

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
	allSeriesAllDataSubpath: '/all_series_all_data',
	allSeriesRangedDataSubpath: '/all_series_ranged_data',
	singleSeriesRangedDataSubpath: '/single_series_ranged_data',
	getAlertsSubpath: '/get_alerts',
	getFilesSubpath: '/get_files',
	writeAnnotationSubpath: '/write_annotation',
	
	// Series to display by default
	// defaultSeries: ['HR', 'RR', 'BP', 'SpO2', 'CVP', 'ArtWave'],
	defaultSeries: ['numerics/HR.BeatToBeat/data', 'numerics/RR.RR/data', 'numerics/ART.Systolic/data', 'numerics/ART.Diastolic/data', 'numerics/SpO₂.SpO₂/data', 'CVP/data', 'ArtWave/data']
	
};

config.allSeriesAllDataURL = config.buildDir(config.allSeriesAllDataSubpath);
config.allSeriesRangedDataURL = config.buildDir(config.allSeriesRangedDataSubpath);
config.singleSeriesRangedDataURL = config.buildDir(config.singleSeriesRangedDataSubpath);
config.getAlertsURL = config.buildDir(config.getAlertsSubpath);
config.getFilesURL = config.buildDir(config.getFilesSubpath);
config.writeAnnotationURL = config.buildDir(config.writeAnnotationSubpath);