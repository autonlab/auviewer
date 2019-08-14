let alertsHTTP = new XMLHttpRequest();

alertsHTTP.onreadystatechange = function() {

	if (this.readyState == 4 && this.status == 200) {

		// Parse the backend JSON response into a JS object
		let backendData = JSON.parse(alertsHTTP.responseText);

		console.log(backendData);

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

	series = document.getElementById("alert_gen_series_field").value;
	threshold = document.getElementById("alert_gen_threshold_field").value;
	duration = document.getElementById("alert_gen_duration_field").value;
	dutycycle = document.getElementById("alert_gen_dutycycle_field").value;
	maxgap = document.getElementById("alert_gen_maxgap_field").value;

	if(
		!series || !series.length || series.length < 1 ||
		!threshold || !threshold.length || threshold.length < 1 ||
		!duration || !duration.length || duration.length < 1 ||
		!dutycycle || !dutycycle.length || dutycycle.length < 1 ||
		!maxgap || !maxgap.length || maxgap.length < 1) {

		return;

	}

	annotations = [];
	alertsHTTP.open("GET", getAlertsURL +
		"?file=" + globalStateManager.currentFile.filename +
		"&series="+encodeURIComponent(series) +
		"&threshold="+encodeURIComponent(threshold) +
		"&duration="+encodeURIComponent(duration) +
		"&dutycycle="+encodeURIComponent(dutycycle) +
		"&maxgap="+encodeURIComponent(maxgap), true);
    alertsHTTP.send();

}