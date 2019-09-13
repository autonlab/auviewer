'use strict';

let annotations = [];

let maxAnnotationID = 0;

function Annotation(begin, end, label='') {

	// Default the ID to a local, incremental identifier until we have a
	// permanent identifier from the backend.
	this.id = "local" + maxAnnotationID;

	// Increment the local identifier incrementation.
	maxAnnotationID++;

	this.begin = begin || 0;
	this.end = end || 0;

	if (label.length > 0) {
		this.label = label;
	}

}

// Cancel creation of a new annotation. This function removes the annotation
// from the global annotations array.
Annotation.prototype.cancel = function () {

	// Get this annotation's index in the global array
	let i = this.getIndex();

	// Remove the annotation from the global array
	annotations.splice(i, 1);

	// Trigger a redraw to remove the annotation
	globalStateManager.currentFile.triggerRedraw();

	$('#annotationModal').modal('hide');

};

// Sets the label of the annotation and finalizes.
Annotation.prototype.finalize = function () {

	// Retrieve and setthe selected label
	let annotationSelect = document.getElementById('annotationLabel');
	this.label = annotationSelect.options[annotationSelect.selectedIndex].value;

	// Trigger a redraw to show the annotation
	globalStateManager.currentFile.triggerRedraw();

	// TODO(gus): Handle null current file, make file determination more robust.
	requestHandler.writeAnnotation(globalStateManager.currentFile.filename, this.begin, this.end, '' /* TODO(gus) */, this.label, function(data) {
		vo("Annotation has been written.");
	});

	// Hide the dialog
	this.hideDialog();

};

// Returns the index of the object in the annotations array, or -1 if not found.
Annotation.prototype.getIndex = function () {
	for (let i = 0; i < annotations.length; i++) {
		if (annotations[i].id == this.id) {
			return i;
		}
	}
	return -1;
};

// Hide the new/edit annotation dialog.
Annotation.prototype.hideDialog = function () {
	$('#annotationModal').removeData('callingAnnotation');
	$('#annotationModal').removeData('state');
	$('#annotationModal').modal('hide');
};

// Show the new/edit annotation dialog. State may be 'create' or 'edit'.
Annotation.prototype.showDialog = function (state) {

	// For any state, set the begin & end values
	$('#annotationStart').val(this.begin);
	$('#annotationEnd').val(this.end);

	// Attach the calling annotation and the state to the dialog
	$('#annotationModal').data('callingAnnotation', this);
	$('#annotationModal').data('state', state);

	// If we're editing, take certain further actions
	if (state === 'edit') {

		// Set the label
		$('#annotationLabel').val(this.label);

		// For now, disable all form fields
		$('#annotationLabel').prop('disabled', true);
		$('#annotationStart').prop('disabled', true);
		$('#annotationEnd').prop('disabled', true);
	}

	// Show the dialog to the user
	$('#annotationModal').modal('show');

};