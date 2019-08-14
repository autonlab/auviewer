'use strict';

let annotations = [];

let maxAnnotationID = 0;

function Annotation(begin, end) {

	// Default the ID to a local, incremental identifier until we have a
	// permanent identifier from the backend.
	this.id = "local" + maxAnnotationID;

	// Increment the local identifier incrementation.
	maxAnnotationID++;

	this.begin = begin || 0;
	this.end = end || 0;

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

// Returns the index of the object in the annotations array, or -1 if not found.
Annotation.prototype.getIndex = function () {
	for (let i = 0; i < annotations.length; i++) {
		if (annotations[i].id == this.id) {
			return i;
		}
	}
	return -1;
};

// Sets the label of the annotation
Annotation.prototype.setLabel = function (label) {

	// Set the label
	this.label = label;

	// Trigger a redraw to show the annotation
	globalStateManager.currentFile.triggerRedraw();
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
								callingAnnotation.setLabel($$('annotationLabel').getValue());
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