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

// Deletes the annotation from the global annotations array.
Annotation.prototype.delete = function () {

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

	$('#annotationModal').modal('hide');

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

Annotation.prototype.showDialog = function () {

	$('#annotationStart').val(this.begin);
	$('#annotationEnd').val(this.end);
	$('#annotationModal').data('callingAnnotation', this);
	$('#annotationModal').modal('show');

};