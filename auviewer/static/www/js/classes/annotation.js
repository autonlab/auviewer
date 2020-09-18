'use strict';

// Annotation can represent an annotation or pattern.
function Annotation(parentSet, dataObjOrArray, type, forceIDReset=false) {

	// Holds a reference to the parent set (either AnnotationSet or PatternSet)
	this.parentSet = parentSet;

	// Grab a reference to the parent set array of annotations or patterns
	this.parentSetArray = this.parentSet.hasOwnProperty('annotations') ? this.parentSet.annotations : this.parentSet.patterns;

	// Set default values
	this.id = null;
	this.file_id = null;
	this.filename = null;
	this.series = null;
	this.begin = 0;
	this.end = 0;
	this.label = {};
	this.pattern_id = null;

	// Holds an object related to this item. For example, if this instance is an
	// Annotation, related may hold the Pattern it annotates.
	this.related = null;

	// Populate values from the object or array provided
	if (typeof dataObjOrArray === 'object' && dataObjOrArray !== null) {
		this.populateValuesFromObject(dataObjOrArray);
	} else {
		console.log('Error: Invalid data provided to annotation constructor (neither object nor array).', deepCopy(dataObjOrArray));
	}

	// Set the local ID if a backend ID was not provided
	if (forceIDReset || !this.hasOwnProperty('id') || !this.id) {
		this.id = localIDGenerator();
	}

	// Holds the type of the annotation. May be 'annotation', 'unsaved_annotation', or 'pattern'.
	this.type = type;

	// Validate the type value.
	if (this.type !== 'unsaved_annotation' && this.type !== 'annotation' && this.type !== 'pattern') {
		console.log('Error: An invalid type was provided to the annotation constructor: ' + this.type);
	}

}

// Cancel creation of a new annotation. This function removes the annotation
// from the global annotations array.
// TODO(gus): To be more robust, the process of editing an existing annotation
// should cache a copy of the pre-update annotation and, if update fails & the
// user cancels out of the dialog, it should revert to the previous values.
Annotation.prototype.cancel = function () {

	// If this was a new annotation, then delete it (in this case, the user is
	// cancelling the creation of the new annotation).
	if (this.type === 'unsaved_annotation') {
		this.parentSet.deleteMember(this);
	}

	// Remove the dialog from the UI
	this.hideDialog();

};

// Delete the annotation (only valid for this.type==='annotation').
Annotation.prototype.delete = function () {

	if (this.type === 'annotation') {

		console.log('Delete called. Sending request to backend.');

		// Send deletion request to the backend.
		requestHandler.deleteAnnotation(this.id, globalStateManager.currentFile.parentProject.id, globalStateManager.currentFile.id, function (data) {

			globalAppConfig.verbose && console.log('Delete response received from backend.', deepCopy(data));

			if (data.hasOwnProperty('success') && data['success'] === true) {
				this.parentSet.deleteMember(this);
				this.hideDialog();
			} else {
				console.log("Received an error while trying to delete annotation.");
				alert('There was an error trying to delete this annotation.');

			}

		}.bind(this));


	} else {
		console.log("Error: Delete called on annotation where this.type !== 'annotation' (current type is '"+this.type+"').");
	}
};

// Returns JS Date object corresponding to end date.
Annotation.prototype.getEndDate = function() {
	return new Date(this.end * 1000);
};

// Returns JS Date object corresponding to start date.
Annotation.prototype.getStartDate = function() {
	return new Date(this.begin * 1000);
};

// Go to the annotation by centering the graph plot at the annotation. If the
// annotation belongs to a file other than the currently-loaded file, it will
// first load the annotation's file.
Annotation.prototype.goTo = function() {

	let callback = (function() {

		console.log('callback running');

		/* Calculate the zoom window */

		// Total zoom window time to display
		let zwTotal = 6 * 60 * 60;

		// Total gap = total zoom window less the pattern duration
		let zwTotalGap = zwTotal - (this.end - this.begin);

		// Gap on either side
		let zwGapSingleSide = zwTotalGap / 2;

		// Compute the zoom window begin & end
		let zwBegin = (this.begin - zwGapSingleSide)*1000;
		let zwEnd = (this.end + zwGapSingleSide)*1000;

		// Zoom to the designated window
		globalStateManager.currentFile.zoomTo([zwBegin, zwEnd]);

		console.log('callback finished');

	}).bind(this);

	// Ensure we have the correct file loaded. If a new file is loaded, it will
	// call callback upon loading. If not, loadFile will return false, and we
	// will call the callback ourselves.
	if (!globalStateManager.loadFile(this.file_id, callback)) {
		callback();
	}

};

// Hide the new/edit annotation dialog.
Annotation.prototype.hideDialog = function () {
	let modal = $('#annotationModal');
	modal.removeData('callingAnnotation');
	modal.modal('hide');
};

// Populates annotation form values from the annotation instance values`.
Annotation.prototype.populateFormFromValues = function() {
	
	// Populate the annotation ID
	document.getElementById('annotationID').innerText = this.id;

	// Populate the file & series names
	document.getElementById('annotationFile').value = this.filename;
	document.getElementById('annotationSeries').value = this.series;

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

	// Uncheck all confidence selections
	$("input[name='annotationConfidence']").prop('checked', false);
	try {
		// Set the annotation confidence
		$("input[name='annotationConfidence'][value='"+this.label.confidence+"']").prop('checked', true);
	} catch {}

	// Clear the annotation notes
	$('#annotationNotes').val('');
	try {
		// Set the annotation notes
		$('#annotationNotes').val(this.label.notes);
	} catch {}

	// Clear the pattern notes
	$('#patternNotes').val('');
	try {
		// Set the pattern notes
		$('#patternNotes').val(this.related.label)
	} catch {}

};

// Populates annotation instance values from the annotation form values.
Annotation.prototype.populateValuesFromForm = function() {
	
	let annotationStartDate = new Date(document.getElementById('annotationStartDate').value + ' ' + document.getElementById('annotationStartTime').value);
	let annotationStartOffset = annotationStartDate.getTime()/1000;
	
	let annotationEndDate = new Date(document.getElementById('annotationEndDate').value + ' ' + document.getElementById('annotationEndTime').value);
	let annotationEndOffset = annotationEndDate.getTime()/1000;

	this.begin = annotationStartOffset;
	this.end = annotationEndOffset;

	this.label = {
		// label: $('#annotationLabel').val(),
		confidence: $("input[name='annotationConfidence']:checked").val(),
		notes: $('#annotationNotes').val()
	};

};

// Populates annotation instance values from an object. The object may have a
// property 'valuesArrayFromBackend' which is an array of the format provided
// by the backend.
Annotation.prototype.populateValuesFromObject = function (obj) {

	if (obj.hasOwnProperty('valuesArrayFromBackend')) {

		// We expect a 6-member array to be provided from the backend.
		if (!obj.valuesArrayFromBackend || !Array.isArray(obj.valuesArrayFromBackend)) {
			console.log('Error: Array provided to annotator was null or not array.');
			return;
		} else if (obj.valuesArrayFromBackend.length !== 10 && obj.valuesArrayFromBackend.length !== 20) {
			console.log('Error: Invalid array provided to annotator (size '+obj.valuesArrayFromBackend.length+').');
			return;
		}

		// Set values from the array
		this.id = obj.valuesArrayFromBackend[0];
		this.file_id = obj.valuesArrayFromBackend[1];
		this.filename = obj.valuesArrayFromBackend[2];
		this.series = obj.valuesArrayFromBackend[3]
		this.begin = obj.valuesArrayFromBackend[4];
		this.end = obj.valuesArrayFromBackend[5];
		try {
			this.label = JSON.parse(obj.valuesArrayFromBackend[8]);
		} catch (error) {
			this.label = obj.valuesArrayFromBackend[8];
		}
		this.pattern_id = obj.valuesArrayFromBackend[9];

		// If data for a related item was provided, instantiate it.
		if (obj.valuesArrayFromBackend.length === 20) {
			this.related = new Annotation(this.parentSet, {'valuesArrayFromBackend': obj.valuesArrayFromBackend.slice(10, 20)}, (this.type === 'annotation' || this.type === 'unsaved_annotation') ? 'pattern' : 'annotation');
		}

	}

	if (obj.hasOwnProperty('id')) {
		this.id = obj.id;
	}
	if (obj.hasOwnProperty('file_id')) {
		this.file_id = obj.file_id;
	}
	if (obj.hasOwnProperty('filename')) {
		this.filename = obj.filename;
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
	if (obj.hasOwnProperty('label')) {
		this.label = obj.label;
	}
	if (obj.hasOwnProperty('pattern_id')) {
		this.pattern_id = obj.pattern_id;
	}

};

// Either finalizes creation of a new annotation (if this.type==='unsaved_annotation'), or
// updates an existing annotation (if this.type==='annotation').
Annotation.prototype.save = function () {

	// We don't expect the save function to be called from an pattern annotation.
	if (this.type === 'pattern') {
		console.log("Error! Save dialog called from pattern annotation.");
		return;
	}

	// Pull values from form
	this.populateValuesFromForm();

	if (this.type === 'unsaved_annotation') {

		// Attempt to create the annotation in the backend
		requestHandler.createAnnotation(globalStateManager.currentFile.parentProject.id, globalStateManager.currentFile.id, this.begin, this.end, this.series, JSON.stringify(this.label), this.pattern_id, function (data) {

			if (data.hasOwnProperty('success') && data.success === true) {

				globalAppConfig.verbose && console.log("Annotation has been written.");

				// Set ID received from backend
				this.id = data.id;

				// Update type to 'annotation'
				this.type = 'annotation';

				// Hide the dialog
				this.hideDialog();

				// If this was an annotation of a pattern, report it to the
				// assignments manager (in case the pattern is an assignment).
				if (this.pattern_id != null) {
					globalStateManager.currentProject.assignmentsManager.annotationCreatedForPattern(this.related.parentSet.id, this.related.id, this);
				}

			} else {

				console.log("Error! Annotation creation failed.");
				alert('Annotation creation failed.');

			}

			// Trigger a redraw to show any changes to the annotation
			globalStateManager.currentFile.triggerRedraw();

		}.bind(this));

	} else if (this.type === 'annotation') {

		requestHandler.updateAnnotation(this.id, globalStateManager.currentFile.parentProject.id, globalStateManager.currentFile.id, this.begin, this.end, this.series, JSON.stringify(this.label), function (data) {

			if (data.hasOwnProperty('success') && data.success === true) {

				globalAppConfig.verbose && console.log("Annotation has been updated.");

				// Hide the dialog
				this.hideDialog();

			} else {

				console.log("Error! Annotation updated failed.");
				alert('Annotation update failed.');

			}

			// Trigger a redraw to show any changes to the annotation
			globalStateManager.currentFile.triggerRedraw();

		}.bind(this));

	}

};

// Show the annotation dialog to allow the user to create or edit an annotation.
Annotation.prototype.showDialog = function () {

	// If this is an pattern, create a new unsaved annotation, and have that show.
	if (this.type === 'pattern') {

		// Determine the destination annotation set for the new annotation
		const destinationAnnotationSet = this.parentSet.parentFile.getAnnotationSetByID(this.parentSet.id);

		// Create the new annotation
		const newAnnotation = new Annotation(destinationAnnotationSet, this, 'unsaved_annotation', true);

		// Set the pattern_id of the new annotation to this pattern
		newAnnotation.pattern_id = this.id;

		// Also attach this pattern as a related object of the new annotation
		newAnnotation.related = this;

		// Add the new annotation to its destination annotation set
		destinationAnnotationSet.addMember(newAnnotation);

		// Triger a redraw of the graphs
		this.parentSet.parentFile.triggerRedraw();

		// Have the new annotation show the dialog
		newAnnotation.showDialog();

		// Work here is done, so return.
		return;
	}

	let modal = $('#annotationModal');

	// Populate form values from this annotation
	this.populateFormFromValues();

	// Attach the calling annotation and the type to the dialog
	modal.data('callingAnnotation', this);

	if (this.type === 'unsaved_annotation') {

		// If we're creating a new annotation...

		// Set modal title, button labels, show/hide button(s)
		if (this.pattern_id) {
			$('#annotationModalTitle').text('New Annotation from Pattern');
		} else {
			$('#annotationModalTitle').text('New Annotation');
		}
		$('#annotationIDContainer').hide();
		$('#annotationModal button.saveButton').text('Create');
		$('#annotationModal button.deleteButton').hide();

	} else if (this.type === 'annotation') {

		// If we're editing...

		// Set modal title, button labels, show/hide button(s)
		$('#annotationModalTitle').text('Edit Annotation');
		$('#annotationIDContainer').show();
		$('#annotationModal button.saveButton').text('Save');
		$('#annotationModal button.deleteButton').show();

	}

	// Show the dialog to the user
	modal.modal('show');

};
