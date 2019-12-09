'use strict';

function RequestHandler() {}

RequestHandler.prototype.createAnnotation = function(filename, xBoundLeft, xBoundRight, seriesID, label, callback) {

	this._newRequest(callback, config.createAnnotationURL, {
		file: filename,
		xl: xBoundLeft,
		xr: xBoundRight,
		/*yt: ,
		yb: ,*/
		sid: seriesID,
		label: label
	});

};

RequestHandler.prototype.deleteAnnotation = function(id, filename, callback) {
	this._newRequest(callback, config.deleteAnnotationURL, {
		id: id,
		file: filename
	});
};

RequestHandler.prototype.requestAnomalyDetection = function(filename, seriesID, tlow, thigh, duration, persistence, maxgap, callback) {

	this._newRequest(callback, config.detectAnomaliesURL, {
		file: filename,
		series: seriesID,
		thresholdlow: tlow,
		thresholdhigh: thigh,
		duration: duration,
		persistence: persistence,
		maxgap: maxgap
	});

};

RequestHandler.prototype.requestInitialFilePayload = function(filename, callback) {
	this._newRequest(callback, config.initialFilePayloadURL, {
		file: filename
	});
};

RequestHandler.prototype.requestFileList = function(callback) {
	this._newRequest(callback, config.getFilesURL, {});
};

RequestHandler.prototype.requestSeriesRangedData = function(filename, series, startTime, stopTime, callback) {
	this._newRequest(callback, config.seriesRangedDataURL, {
		file: filename,
		s: series,
		start: startTime,
		stop: stopTime
	});
};

RequestHandler.prototype.updateAnnotation = function(id, filename, xBoundLeft, xBoundRight, seriesID, label, callback) {

	this._newRequest(callback, config.updateAnnotationURL, {
		id: id,
		file: filename,
		xl: xBoundLeft,
		xr: xBoundRight,
		/*yt: ,
		yb: ,*/
		sid: seriesID,
		label: label,
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
			let data = {};
			if (this.responseText.length > 0) {
				data = JSON.parse(this.responseText);
			}

			vo("Response received to " + path, data);

			// Call the callback with data
			if (typeof callback === 'function') {
				callback(data);
			} else {
				console.log("Important: Callback not provided to request handler.");
			}

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
		if (params[keys[i]] != null && params[keys[i]].constructor === Array) {
			for (let j = 0; j < params[keys[i]].length; j++) {
				if (j !== 0) {
					path += '&';
				}
				path += keys[i]+ '[]=' + encodeURIComponent(params[keys[i]][j]);
			}
		} else if (params[keys[i]] || params[keys[i]] === 0) {
			path += keys[i] + '=' + encodeURIComponent(params[keys[i]]);
		} else {
			path += keys[i] + '='
		}
	}

	req.open("GET", path, true);
	req.send();

};