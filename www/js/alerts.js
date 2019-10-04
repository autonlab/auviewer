'use strict';

let alertsHTTP = new XMLHttpRequest();

alertsHTTP.onreadystatechange = function() {

	if (this.readyState == 4 && this.status == 200) {

		// Parse the backend JSON response into a JS object
		let backendData = JSON.parse(alertsHTTP.responseText);

		for (let i in backendData) {
			annotations.push(new Annotation(backendData[i][0], backendData[i][1]));
		}

		globalStateManager.currentFile.triggerRedraw();

	}

};

function clearAlerts() {
	annotations = [];
	globalStateManager.currentFile.triggerRedraw();
}

function generateAlerts() {

	let series = document.getElementById("alert_gen_series_field").value;
	let thresholdlow = document.getElementById("alert_gen_threshold_low_field").value;
	let thresholdhigh = document.getElementById("alert_gen_threshold_high_field").value;
	let duration = document.getElementById("alert_gen_duration_field").value;
	let dutycycle = document.getElementById("alert_gen_dutycycle_field").value;
	let maxgap = document.getElementById("alert_gen_maxgap_field").value;

	// These parameters are required.
	if(
		!series || !series.length || series.length < 1 ||
		!duration || !duration.length || duration.length < 1 ||
		!dutycycle || !dutycycle.length || dutycycle.length < 1 ||
		!maxgap || !maxgap.length || maxgap.length < 1) {

		return;

	}

	// Either threshold low or threshold high or both is required.
	if(
		(!thresholdlow || !thresholdlow.length || thresholdlow.length < 1) &&
		(!thresholdhigh || !thresholdhigh.length || thresholdhigh.length < 1)) {
		return;
	}

	annotations = [];
	alertsHTTP.open("GET", config.getAlertsURL +
		"?file=" + globalStateManager.currentFile.filename +
		"&series="+encodeURIComponent(series) +
		"&thresholdlow="+encodeURIComponent(thresholdlow) +
		"&thresholdhigh="+encodeURIComponent(thresholdhigh) +
		"&duration="+encodeURIComponent(duration) +
		"&dutycycle="+encodeURIComponent(dutycycle) +
		"&maxgap="+encodeURIComponent(maxgap), true);
    alertsHTTP.send();

}