'use strict';

// Verify we're serving Chrome browser
if (navigator.userAgent.indexOf("Chrome") === -1) {

	const body = document.getElementsByTagName("BODY")[0];

	// Clear all body elements
	// See: https://jsperf.com/innerhtml-vs-removechild/15
	while (body.firstChild) {
		body.removeChild(body.firstChild);
	}

	// Add user notice
	body.innerHTML =
		'<!-- Browser warning -->\n' +
		'<div style="position: absolute; z-index: 9999999999; width: 100%; height: 100%; background-color: white; display: flex; justify-content: center; align-items: center;">\n' +
		'\t<div style="width: 100%; text-align: center;">\n' +
		'\t\t<h1>Please use Chrome to view this web app.</h1><h6>Unfortunately, the charting library we use at this time is incompatible with other browsers.</h6>\n' +
		'\t</div>\n' +
		'</div>';

	throw new Error("Please use Chrome browser to view this web app. Unfortunately, the charting library we use at this time is incompatible with other browsers.");

}

// Attach event handlers to the annotation modal
$('#annotationModal button.saveButton').click(function() {
	$('#annotationModal').data('callingAnnotation').save();
});
$('#annotationModal button.cancelButton').click(function() {
	$('#annotationModal').data('callingAnnotation').cancel();
});
$('#annotationModal button.deleteButton').click(function() {
	if (confirm("Are you sure you want to delete this annotation?")) {
		$('#annotationModal').data('callingAnnotation').delete();
	}
});

$('#annotationsListModal').on('show.bs.modal', function (e) {

	// Clear previous annotation list
	// See: https://jsperf.com/innerhtml-vs-removechild/15
	const tbody = this.querySelector('tbody');
	while (tbody.firstChild) {
		tbody.removeChild(tbody.firstChild);
	}

	let modal = this;

	let rowClickHandler = function() {
		$(modal).modal('hide');
		$(this).data('annotation').goTo();
	};

	if (globalStateManager.currentFile && globalStateManager.currentFile.hasOwnProperty('annotations')) {

		for (let a of globalStateManager.currentFile.annotations) {

			if (a.type === 'annotation') {

				// Create the dom element
				let tr = document.createElement('tr');

				// Attach the annotation to the dom element for use by the click
				// handler, then attach the click handler.
				$(tr).data('annotation', a);
				tr.addEventListener("click", rowClickHandler);

				// Display content of the row
				tr.innerHTML =
					'<th scope="row">' + a.id + '</th>' +
					'<td>' + a.getStartDate().toLocaleString() + '</td>' +
					'<td>' + a.getEndDate().toLocaleString() + '</td>' +
					'<td>' + JSON.stringify(a.label) + '</td>';
				tbody.appendChild(tr);
			}

		}

	}

});

function populateAllAnnotationsModal() {

	const modal = document.getElementById('allAnnotationsListModal')

	// Clear previous annotation list
	// See: https://jsperf.com/innerhtml-vs-removechild/15
	const tbody = modal.querySelector('tbody');
	while (tbody.firstChild) {
		tbody.removeChild(tbody.firstChild);
	}

	const rowClickHandler = function() {
		$(modal).modal('hide');
		$(this).data('annotation').goTo();
	};

	if (globalStateManager.currentProject && Array.isArray(globalStateManager.currentProject.annotations)) {

		for (let a of globalStateManager.currentProject.annotations) {

			if (a.type === 'annotation') {

				// Create the dom element
				let tr = document.createElement('tr');

				// Attach the annotation to the dom element for use by the click
				// handler, then attach the click handler.
				$(tr).data('annotation', a);
				tr.addEventListener("click", rowClickHandler);

				// Display content of the row
				tr.innerHTML =
					'<th scope="row">' + a.id + '</th>' +
					'<td>' + a.filename + '</td>' +
					'<td>' + a.getStartDate().toLocaleString() + '</td>' +
					'<td>' + a.getEndDate().toLocaleString() + '</td>' +
					'<td>' + JSON.stringify(a.label) + '</td>';
				tbody.appendChild(tr);
			}

		}

	}

}

$('#allAnnotationsListModal').on('show.bs.modal', function (e) {

	if (globalStateManager.currentProject && Array.isArray(globalStateManager.currentProject.annotations)) {

		populateAllAnnotationsModal();

	} else if (globalStateManager.currentProject) {

		// Request project annotations
		globalStateManager.currentProject.getAnnotations(populateAllAnnotationsModal);

	}

});

let requestHandler = new RequestHandler();
let globalStateManager = new GlobalStateManager();
let templateSystem = new TemplateSystem();

// Instantiate the current project with the payload
globalStateManager.currentProject = new Project(payload)

// Detect & handle hash variables
var hash = window.location.hash.substr(1);
var result = hash.split('&').reduce(function (result, item) {
    var parts = item.split('=');
    result[parts[0]] = parts[1];
    return result;
}, {});
if (result.hasOwnProperty('file_id')) {
	globalStateManager.loadFile(result['file_id'])
}