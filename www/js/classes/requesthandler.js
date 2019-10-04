'use strict';

function RequestHandler() {}

RequestHandler.prototype.requestInitialFilePayload = function(filename, callback) {
	this._newRequest(callback, config.initialFilePayloadURL, {
		file: filename
	});
};

RequestHandler.prototype.requestAllSeriesRangedData = function(filename, startTime, stopTime, callback) {

	this._newRequest(callback, config.allSeriesRangedDataURL, {
		file: filename,
		start: startTime,
		stop: stopTime
	});

};

RequestHandler.prototype.requestFileList = function(callback) {
	this._newRequest(callback, config.getFilesURL, {});
};

RequestHandler.prototype.requestMultiSeriesRangedData = function(filename, series, startTime, stopTime, callback) {
	this._newRequest(callback, config.multiSeriesRangedDataURL, {
		file: filename,
		s: series,
		start: startTime,
		stop: stopTime
	});
};

RequestHandler.prototype.requestSingleSeriesRangedData = function(filename, series, startTime, stopTime, callback) {
	this._newRequest(callback, config.singleSeriesRangedDataURL, {
		file: filename,
		series: series,
		start: startTime,
		stop: stopTime
	});
};

RequestHandler.prototype.writeAnnotation = function(filename, xBoundLeft, xBoundRight, seriesID, label, callback) {

	this._newRequest(callback, config.writeAnnotationURL, {
		file: encodeURIComponent(filename),
		xl: encodeURIComponent(xBoundLeft),
		xr: encodeURIComponent(xBoundRight),
		/*yt: encodeURIComponent(),
		yb: encodeURIComponent(),*/
		sid: encodeURIComponent(seriesID),
		label: encodeURIComponent(label),
	});

};

// Executes a backend request. Takes an object params with name/value pairs.
// The value may be either a string/string-convertible value or an array of
// such values. In the latter case, the array will be passed in as a GET
// parameter array of values.
RequestHandler.prototype._newRequest = function(callback, path, params) {

	// Instantiate a new HTTP request object
	let req = new XMLHttpRequest();

	req.onreadystatechange = function() {

		if (this.readyState === 4 && this.status === 200) {

			// JSON-decode the response
			let data = {}
			if (this.responseText.length > 0) {
				data = JSON.parse(this.responseText);
			}

			vo("Response received to " + path, data);

			// Call the callback with data
			callback(data);

		}

	};

	// Assemble the parameters on the path
	let keys = Object.keys(params);
	for (let i = 0; i < keys.length; i++) {
		if (i === 0) {
			path += '?';
		} else {
			path += '&';
		}
		if (params[keys[i]].constructor === Array) {
			for (let j = 0; j < params[keys[i]].length; j++) {
				if (j !== 0) {
					path += '&';
				}
				path += keys[i]+ '[]=' + encodeURIComponent(params[keys[i]][j]);
			}
		} else {
			path += keys[i] + '=' + encodeURIComponent(params[keys[i]]);
		}
	}

	req.open("GET", path, true);
	req.send();

};