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
};

// Sets the label of the annotation and finalizes.
Annotation.prototype.finalize = function (label) {

	// Set the label
	this.label = label;

	// Trigger a redraw to show the annotation
	globalStateManager.currentFile.triggerRedraw();

	// TODO(gus): Handle null current file, make file determination more robust.
	requestHandler.writeAnnotation(globalStateManager.currentFile.filename, this.begin, this.end, '' /* TODO(gus) */, this.label, function(data) {
		vo("Annotation has been written.");
	});
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

	let callingAnnotation = this;

	webix.ui({
		view: "window",
		id: "annotationPopup",
		height: 250,
		width: 300,
		position: "center",
		head: "Annotation",
		move: true,
		body: {
			view: "form",
			scroll: false,
			width: 300,
			elements: [
				{
					view: "select",
					label: "Label",
					id: "annotationLabel",
					options: ["ConditionC", "Artifact"]
				},
				{
					cols: [
						{
							view: "button",
							value: "Confirm",
							align: "center",
							css: "webix_primary",
							click: function () {
								console.log($$('annotationLabel'));
								callingAnnotation.finalize($$('annotationLabel').getValue());
								$$('annotationPopup').hide();
								console.log(annotations);
							}
						},
						{
							view: "button",
							value: "Cancel",
							click: function () {
								callingAnnotation.delete();
								$$('annotationPopup').hide();
							}
						}
					]
				}
			]
		}
	}).show();

};