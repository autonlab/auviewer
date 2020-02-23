'use strict';

// Holds the next incremental local ID.
let maxLocalAnnotationID = 0;

// Annotation constructor.
function Annotation(dataObjOrArray, state) {

	// Set default values
	this.series = null;
	this.annotation = {};
	this.begin = 0;
	this.end = 0;

	// Populate values from the object or array provided
	if (typeof dataObjOrArray === 'object' && dataObjOrArray !== null) {
		this.populateValuesFromObject(dataObjOrArray);
	} else {
		console.log('Error: Invalid data provided to annotation constructor (neither object nor array).', deepCopy(dataObjOrArray));
	}

	// Set the local ID if a backend ID was not provided
	if (!this.hasOwnProperty('id') || this.id.length <= 0) {
		this.id = "local" + maxLocalAnnotationID++;
	}

	// Holds the state of the annotation. May be 'new', 'existing', or 'anomaly'.
	this.state = state;

	// Validate the state value.
	if (this.state !== 'new' && this.state !== 'existing' && this.state !== 'anomaly') {
		console.log('Error: An invalid state was provided to the annotation constructor: ' + this.state);
	}

}

// Cancel creation of a new annotation. This function removes the annotation
// from the global annotations array.
Annotation.prototype.cancel = function () {

	// If this was a new annotation, then delete it (in this case, the user is
	// cancelling the creation of the new annotation).
	if (this.state === 'new') {

		// Delete the local copy of the annotation.
		this.deleteLocal();

		// Trigger a redraw to remove the annotation
		globalStateManager.currentFile.triggerRedraw();

	}

	// Remove the dialog from the UI
	this.hideDialog();

};

// Delete the annotation (only valid for this.state==='existing').
Annotation.prototype.delete = function () {

	if (this.state === 'existing') {

		console.log('Delete called. Sending request to backend.');

		// Persist this for callback
		let annotation = this;

		// Send deletion request to the backend.
		requestHandler.deleteAnnotation(this.id, globalStateManager.currentFile.projname, globalStateManager.currentFile.filename, function (data) {

			globalAppConfig.verbose && console.log('Delete response received from backend.', deepCopy(data));

			if (data.hasOwnProperty('success') && data['success'] === true) {

				// Delete the local copy of the annotation.
				annotation.deleteLocal();

				// Trigger a redraw to remove the annotation
				globalStateManager.currentFile.triggerRedraw();

			} else {

				console.log("Received an error while trying to delete annotation.");

			}

		});

		// Hide the dialog modal.
		this.hideDialog();

	} else {
		console.log("Error: Delete called on annotation where this.state !== 'existing' (current state is '"+this.state+"').");
	}
};

// Deletes the local copy of the annotation from the array of annotations.
Annotation.prototype.deleteLocal = function() {

	let file = globalStateManager.currentFile;

	// Get this annotation's index in the global array
	let i = this.getIndex();

	// Remove the annotation from the global array
	file.annotations.splice(i, 1);

};

// Returns JS Date object corresponding to end date.
Annotation.prototype.getEndDate = function() {
	return new Date((this.end + globalStateManager.currentFile.fileData.baseTime) * 1000);
};

// Returns JS Date object corresponding to start date.
Annotation.prototype.getStartDate = function() {
	return new Date((this.begin + globalStateManager.currentFile.fileData.baseTime) * 1000);
};

// Returns the index of the object in the annotations array, or -1 if not found.
Annotation.prototype.getIndex = function () {
	let file = globalStateManager.currentFile;
	for (let i = 0; i < file.annotations.length; i++) {
		if (file.annotations[i].id === this.id) {
			return i;
		}
	}
	return -1;
};

// Hide the new/edit annotation dialog.
Annotation.prototype.hideDialog = function () {
	let modal = $('#annotationModal');
	modal.removeData('callingAnnotation');
	modal.modal('hide');
};

// Populates annotation form values from the annotation instance values`.
Annotation.prototype.populateFormFromValues = function() {

	// Populate annotation start date & time fields
	let annotationStartDate = this.getStartDate();
	let annotationStartDateStrings = getHTML5DateTimeStringsFromDate(annotationStartDate);
	document.getElementById('annotationStartDate').value = annotationStartDateStrings[0];
	document.getElementById('annotationStartTime').value = annotationStartDateStrings[1];


	// Populate annotation end date & time fields
	let annotationEndDate = this.getEndDate();
	let annotationEndDateStrings = getHTML5DateTimeStringsFromDate(annotationEndDate);
	document.getElementById('annotationEndDate').value = annotationEndDateStrings[0];
	document.getElementById('annotationEndTime').value = annotationEndDateStrings[1];

	// if (this.annotation.hasOwnProperty('label')) {
	// 	// Set the annotation label
	// 	$('#annotationLabel').val(this.annotation.label);
	// } else {
	// 	// Set the annotation label to the first option
	// 	$('#annotationLabel').val($('#annotationLabel option:first').val());
	// }

	if (this.annotation.hasOwnProperty('confidence')) {
		// Set the annotation confidence
		$("input[name='annotationConfidence'][value='"+this.annotation.confidence+"']").prop('checked', true);
	} else {
		// Uncheck all confidence selections
		$("input[name='annotationConfidence']").prop('checked', false);
	}

	if (this.annotation.hasOwnProperty('notes')) {
		// Set the annotation notes
		$('#annotationNotes').val(this.annotation.notes);
	} else {
		// Clear the annotation notes
		$('#annotationNotes').val('');
	}

};

// Populates annotation instance values from the annotation form values.
Annotation.prototype.populateValuesFromForm = function() {
	
	let annotationStartDate = new Date(document.getElementById('annotationStartDate').value + ' ' + document.getElementById('annotationStartTime').value);
	let annotationStartOffset = annotationStartDate.getTime()/1000 - globalStateManager.currentFile.fileData.baseTime;
	
	let annotationEndDate = new Date(document.getElementById('annotationEndDate').value + ' ' + document.getElementById('annotationEndTime').value);
	let annotationEndOffset = annotationEndDate.getTime()/1000 - globalStateManager.currentFile.fileData.baseTime;

	this.begin = annotationStartOffset;
	this.end = annotationEndOffset;

	this.annotation = {
		// label: $('#annotationLabel').val(),
		confidence: $("input[name='annotationConfidence']:checked").val(),
		notes: $('#annotationNotes').val()
	};

};

// Populates annotation instance values from an object. The object may have a
// property 'values' which is an array of the format provided by the backend.
Annotation.prototype.populateValuesFromObject = function (obj) {

	if (obj.hasOwnProperty('valuesArrayFromBackend')) {

		// We expect a 6-member array to be provided from the backend.
		if (!obj.valuesArrayFromBackend || !Array.isArray(obj.valuesArrayFromBackend)) {
			console.log('Error: Array provided to annotator was null or not array.');
			return;
		} else if (obj.valuesArrayFromBackend.length !== 6) {
			console.log('Error: Invalid array provided to annotator (size '+obj.valuesArrayFromBackend.length+').');
			return;
		}

		// Set values from the array
		this.id = obj.valuesArrayFromBackend[0];
		this.begin = obj.valuesArrayFromBackend[1];
		this.end = obj.valuesArrayFromBackend[2];
		this.annotation = JSON.parse(obj.valuesArrayFromBackend[5]);

	}

	if (obj.hasOwnProperty('id')) {
		this.id = obj.id;
	}
	if (obj.hasOwnProperty('series')) {
		this.series = obj.series;
	}
	if (obj.hasOwnProperty('begin')) {
		this.begin = obj.begin;
	}
	if (obj.hasOwnProperty('end')) {
		this.end = obj.end;
	}
	if (obj.hasOwnProperty('annotation')) {
		this.annotation = obj.annotation;
	}

};

// Either finalizes creation of a new annotation (if this.state==='new'), or
// saves an existing annotation (if this.state==='existing').
Annotation.prototype.save = function () {

	// Pull values from form
	this.populateValuesFromForm();

	// Persist the this variable for the event handler.
	let annotation = this;

	if (this.state === 'new' || this.state === 'anomaly') {

		// TODO(gus): Handle null current file, make file determination more robust.
		requestHandler.createAnnotation(globalStateManager.currentFile.projname, globalStateManager.currentFile.filename, this.begin, this.end, '' /* TODO(gus) */, JSON.stringify(this.annotation), function (data) {

			if (data.hasOwnProperty('success') && data.success === true) {

				globalAppConfig.verbose && console.log("Annotation has been written.");

				// Set ID received from backend
				annotation.id = data.id;

				// Update state to 'existing'
				annotation.state = 'existing';

			} else {

				globalAppConfig.verbose && console.log("Annotation creation failed.");

				// If this was a new annotation, delete the local copy.
				// Otherwise (if it was a detected anomaly), leave it be.
				if (this.state === 'new') {
					this.deleteLocal();
				}

			}

			// Trigger a redraw to show any changes to the annotation
			globalStateManager.currentFile.triggerRedraw();

		});

	} else if (this.state === 'existing') {

		requestHandler.updateAnnotation(this.id, globalStateManager.currentFile.projname, globalStateManager.currentFile.filename, this.begin, this.end, '', JSON.stringify(this.annotation), function (data) {

			if (data.hasOwnProperty('success') && data.success === true) {

				globalAppConfig.verbose && console.log("Annotation has been updated.");

			} else {

				 globalAppConfig.verbose && console.log("Annotation updated failed.");
				 this.deleteLocal();

			}

			// Trigger a redraw to show any changes to the annotation
			globalStateManager.currentFile.triggerRedraw();

		});

	}

	// Hide the dialog
	this.hideDialog();

};

// Show the new/edit annotation dialog. State may be 'create' or 'edit'.
Annotation.prototype.showDialog = function () {

	let modal = $('#annotationModal');

	// Populate form from values
	this.populateFormFromValues();

	// Attach the calling annotation and the state to the dialog
	modal.data('callingAnnotation', this);

	if (this.state === 'new') {

		// If we're creating a new annotation...

		// Set modal title, button labels, show/hide button(s)
		$('#annotationModalTitle').text('New Annotation');
		$('#annotationModal button.saveButton').text('Create');
		$('#annotationModal button.deleteButton').hide();

	} else if (this.state === 'existing') {

		// If we're editing...

		// Set modal title, button labels, show/hide button(s)
		$('#annotationModalTitle').text('Edit Annotation');
		$('#annotationModal button.saveButton').text('Save');
		$('#annotationModal button.deleteButton').show();

	} else if (this.state === 'anomaly') {

		// If this is an anomaly...

		// Set modal title, button labels, show/hide button(s)
		$('#annotationModalTitle').text('New Annotation from Anomaly');
		$('#annotationModal button.saveButton').text('Create');
		$('#annotationModal button.deleteButton').hide();

	}

	// Show the dialog to the user
	modal.modal('show');

};
