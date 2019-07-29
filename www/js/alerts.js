var alertshttp = new XMLHttpRequest();

alertshttp.onreadystatechange = function() {

	if (this.readyState == 4 && this.status == 200) {

		// Parse the backend JSON response into a JS object
		var backendData = JSON.parse(alertshttp.responseText);

		console.log(backendData);

		for (var i in backendData) {
			annotations.push(new Annotation(backendData[i][0], backendData[i][1]));
		}

		triggerRedraw();

	}

};

function clearAlerts() {
	annotations = [];
	triggerRedraw();
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
	alertshttp.open("GET", getAlertsURL +
		"?series="+encodeURIComponent(series) +
		"&threshold="+encodeURIComponent(threshold) +
		"&duration="+encodeURIComponent(duration) +
		"&dutycycle="+encodeURIComponent(dutycycle) +
		"&maxgap="+encodeURIComponent(maxgap), true);
    alertshttp.send();

}