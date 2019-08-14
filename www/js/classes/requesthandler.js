'use strict';

function RequestHandler() {}

RequestHandler.prototype.requestAllSeriesAllData = function(filename, callback) {
	this.newRequest(callback, config.allSeriesAllDataURL, {
		file: encodeURIComponent(filename)
	});
};

RequestHandler.prototype.requestAllSeriesRangedData = function(filename, startTime, stopTime, callback) {

	this.newRequest(callback, config.dataWindowAllSeriesURL, {
		file: encodeURIComponent(filename),
		start: encodeURIComponent(startTime),
		stop: encodeURIComponent(stopTime)
	});

};

RequestHandler.prototype.requestFileList = function(callback) {
	this.newRequest(callback, config.getFilesURL, {});
};

RequestHandler.prototype.requestSingleSeriesRangedData = function(filename, series, startTime, stopTime, callback) {
	this.newRequest(callback, config.dataWindowSingleSeriesURL, {
		file: encodeURIComponent(filename),
		series: encodeURIComponent(series),
		start: encodeURIComponent(startTime),
		stop: encodeURIComponent(stopTime)
	});
};

// Executes a backend request
RequestHandler.prototype.newRequest = function(callback, path, params) {

	// Instantiate a new HTTP request object
	let req = new XMLHttpRequest();

	req.onreadystatechange = function() {

		if (this.readyState === 4 && this.status === 200) {

			// JSON-decode the response
			let data = JSON.parse(this.responseText);

			vo("Response received to " + path, data);

			// Call the callback with data
			callback(data);

		}

	};

	// Assemble the parameters on the path
	let keys = Object.keys(params);
	for (let i in keys) {
		if (i == 0) {
			path += '?';
		} else {
			path += '&';
		}
		path += keys[i] + '=' + params[keys[i]];
	}

	req.open("GET", path, true);
	req.send();

};