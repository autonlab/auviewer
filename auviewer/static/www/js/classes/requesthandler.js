'use strict';

// Class declaration
function RequestHandler() {}

RequestHandler.prototype.createAnnotation = function(projname, filename, xBoundLeft, xBoundRight, seriesID, label, callback) {

	this._newRequest(callback, globalAppConfig.createAnnotationURL, {
		project: projname,
		file: filename,
		xl: xBoundLeft,
		xr: xBoundRight,
		/*yt: ,
		yb: ,*/
		sid: seriesID,
		label: label
	});

};

RequestHandler.prototype.deleteAnnotation = function(id, projname, filename, callback) {
	this._newRequest(callback, globalAppConfig.deleteAnnotationURL, {
		id: id,
		project: projname,
		file: filename
	});
};

RequestHandler.prototype.requestAnomalyDetection = function(projname, filename, type, seriesID, tlow, thigh, duration, persistence, maxgap, callback) {

	this._newRequest(callback, globalAppConfig.detectAnomaliesURL, {
		project: projname,
		file: filename,
		type: type,
		series: seriesID,
		thresholdlow: tlow,
		thresholdhigh: thigh,
		duration: duration,
		persistence: persistence,
		maxgap: maxgap
	});

};

RequestHandler.prototype.requestInitialFilePayload = function(projname, filename, callback) {
	this._newRequest(callback, globalAppConfig.initialFilePayloadURL, {
		project: projname,
		file: filename
	});
};

RequestHandler.prototype.requestInitialProjectPayload = function(projname, callback) {
	this._newRequest(callback, globalAppConfig.initialProjectPayloadURL, {
		project: projname
	});
};

RequestHandler.prototype.requestProjectAnnotations = function(projname, callback) {
	this._newRequest(callback, globalAppConfig.getProjectAnnotationsURL, {
		project: projname
	})
};

RequestHandler.prototype.requestProjectsList = function(callback) {
	this._newRequest(callback, globalAppConfig.getProjectsURL, {});
};

RequestHandler.prototype.requestSeriesRangedData = function(projname, filename, series, startTime, stopTime, callback) {
	this._newRequest(callback, globalAppConfig.seriesRangedDataURL, {
		project: projname,
		file: filename,
		s: series,
		start: startTime,
		stop: stopTime
	});
};

RequestHandler.prototype.updateAnnotation = function(id, projname, filename, xBoundLeft, xBoundRight, seriesID, label, callback) {

	this._newRequest(callback, globalAppConfig.updateAnnotationURL, {
		id: id,
		project: projname,
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

			globalAppConfig.verbose && console.log("Response received to " + path, deepCopy(data));

			// Call the callback with data
			if (typeof callback === 'function') {
				let t0 = performance.now();
				callback(data);
				let tt = performance.now() - t0;
				globalAppConfig.verbose && tt > globalAppConfig.performanceReportingThresholdMS && console.log("Request callback took " + Math.round(tt) + "ms:", path, params);
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