'use strict';

class Set {

	constructor(parent, id, name, description, membersArray, memberType, color, display) {

		if (parent instanceof Project) {
			this.parentProject = parent;
		} else if (parent instanceof File) {
			this.parentFile = parent;
		} else if (parent instanceof AssignmentsManager) {
			this.parentAssignmentManager = parent;
		} else {
			console.log("Error! Set constructor given parent that is neither Project nor File class instance.");
		}
		this.parentFile = parent;
		this.id = id;
		this.name = name;
		this.description = description;
		this.members = [];
		this.color = color;

		// Represents whether this set is currently displaying
		this.display = display;

		// DOM ID of the count table cell in the control panel table
		this.countTDID = localIDGenerator();

		// Instantiate the members
		for (const m of membersArray) {
			this.members.push(new Annotation(this, {valuesArrayFromBackend: m}, memberType))
		}

		// If initially displaying, add this set's members to the render set.
		if (this.display) {
			this.setDisplay(true);
		}

		// Persist this for the event handler
		const set = this;

		// If this set belongs to a file, add this set to the appropriate
		// control panel table.
		if (parent instanceof File) {
			try {
				const tr = document.createElement('tr');
				tr.innerHTML =
					'<td><input type="checkbox" ' + (this.display === true ? 'checked' : '') + '></td>\n' +
					'<td>' + this.name + '</td>' +
					'<td><div class="color-square" style="background-color: ' + this.color + ';"></div></td>' +
					'<td id="' + this.countTDID + '">' + this.members.length + '</td>';
				tr.onclick = function (event) {
					const cb = this.querySelector('input');
					if (event.target.type !== 'checkbox') {
						cb.checked = !cb.checked;
					}
					set.setDisplay(cb.checked);
				}
				document.getElementById(memberType + '_sets_cp_table').querySelector('tbody').appendChild(tr);
			} catch (e) {
				console.log("Unable to add row to control panel table.", this, e);
			}
		}

	}

	// Adds a a member to this set.
	addMember(annotation) {

		// Add the annotation
		this.members.push(annotation);

		// Update the count in the control panel table
		this.updateCount();

		// If this annotation set is currently displaying, add the new annotation to
		// the render annotations array.
		if (this.display) {
			this.parentFile.annotationsAndPatternsToRender.push(annotation);
		}
	};

	// Removes an annotation from the annotations array.
	deleteMember(member) {

		// Remove the annotation from the set's annotations array
		for (let i = 0; i < this.members.length; i++) {
			if (Object.is(this.members[i], member)) {
				this.members.splice(i, 1);
				break;
			}
		}

		// Update the count
		this.updateCount();

		// If currently displaying, remove the annotation from the render array
		if (this.display) {

			for (let i = 0; i < this.parentFile.annotationsAndPatternsToRender.length; i++) {
				if (Object.is(this.parentFile.annotationsAndPatternsToRender[i], member)) {
					this.parentFile.annotationsAndPatternsToRender.splice(i, 1);
					break;
				}
			}

			// Trigger redraw
			this.parentFile.triggerRedraw();

		}

	};

	// Set display status to true or false.
	// NOTE: This function is not idempotent. If setDisplay(true) is called
	// twice, the set will add itself to the render set twice. This is so that
	// the function can be used to rebuild the render set.
	setDisplay(status, suppressredraw=false) {
		if (status === true) {
			this.display = true;
			this.parentFile.annotationsAndPatternsToRender = this.parentFile.annotationsAndPatternsToRender.concat(this.members);
			!suppressredraw && this.parentFile.triggerRedraw();
		} else if (status === false) {
			this.display = false;
			this.parentFile.rebuildRenderSet();
			!suppressredraw && this.parentFile.triggerRedraw();
		} else {
			console.log("Error! Unexpected value passed to Set.setDisplay(status).")
		}
	};

	// Updates the control panel count for this annotation set.
	updateCount() {
		document.getElementById(this.countTDID).innerText = this.members.length.toString();
	};

}

class AnnotationSet extends Set {
	constructor(parentFile, id, name, description, annotationsArray, show) {
		super(parentFile, id, name, description, annotationsArray, 'annotation', parentFile.template.series._default.ownAnnotationColor, show);
	}
}

class PatternSet extends Set {
	constructor(parentFile, id, name, description, patternsArray, show) {
		super(parentFile, id, name, description, patternsArray, 'pattern', parentFile.template.series._default.ownPatternColor, show);
	}
}

class AssignmentSet extends Set {

	constructor(parentProject, id, name, description, patternsArray) {

		super(parentProject, id, name, description, patternsArray, 'pattern', '', false);

		// Holds index of the current target assignment, or null it not started
		this.currentTargetAssignmentIndex = null;

		// Initial panel state is stopped. Can be 'stopped' or 'started'. Only
		// the updatePanel function should change this parameter.
		this.panelState = 'stopped';

		this.render();
	}

	// Handles a report that an annotation was created for a pattern which
	// belongs to this assignment set.
	annotationCreatedForPattern(assignment_id, annotation) {

		for (const assignment of this.members) {
			if (assignment.id === assignment_id) {

				// Attach the new annotation to the assignment.
				assignment.related = annotation;

				// // If it's the current target assignment that was annotated,
				// // proceed to the next assignment.
				// if (Object.is(assignment, this.members[this.currentTargetAssignmentIndex])) {
				// 	this.nextPosition();
				// }

				break;
			}
		}

		// Update the assignment panel
		this.updatePanel();

	};

	// Returns the number of assignments that have been completed.
	getCompletedCount() {
		let count = 0;
		for (const pattern of this.members) {
			if (pattern.related != null) {
				count++;
			}
		}
		return count;
	};

	// Returns boolean indicating whether the assignment has begun.
	hasBegun() {
		return this.currentTargetAssignmentIndex != null;
	};

	// Go to the next incomplete assignment.
	nextIncompletePosition(pos) {

		// Preserve the position in case needed at the end
		const originalPos = this.currentTargetAssignmentIndex;

		// If a position is not specified, start at the next position
		if (pos == null) {
			pos = this.currentTargetAssignmentIndex+1;
		}

		// Find the next incomplete assignment
		for (this.currentTargetAssignmentIndex = pos; this.currentTargetAssignmentIndex < this.members.length && this.members[this.currentTargetAssignmentIndex].related != null; this.currentTargetAssignmentIndex++){}
		// If we got to the end, start from the beginning
		if (this.currentTargetAssignmentIndex >= this.members.length) {
			for (this.currentTargetAssignmentIndex = 0; this.currentTargetAssignmentIndex < this.members.length && this.members[this.currentTargetAssignmentIndex].related != null; this.currentTargetAssignmentIndex++){}
		}

		if (this.currentTargetAssignmentIndex === originalPos) {
			// We ended up at our own position, so this is the last remaining unannotated pattern
			this.currentTargetAssignmentIndex = originalPos;
			alert("You are at the last remaining unannotated pattern.")
		}
		else if (this.currentTargetAssignmentIndex < this.members.length) {
			// Found next unannotated pattern, so go to it
			this.members[this.currentTargetAssignmentIndex].goTo();
			this.updatePanel();
		} else {
			// There are no remaining unannotated patterns (including current position)
			this.currentTargetAssignmentIndex = originalPos;
			alert("There are no remaining unannotated patterns.")
		}
	};

	// Go to the previous incomplete assignment.
	prevIncompletePosition(pos) {

		// Preserve the position in case needed at the end
		const originalPos = this.currentTargetAssignmentIndex;

		// If a position is not specified, start just before the current position
		if (pos == null) {
			pos = this.currentTargetAssignmentIndex-1;
		}

		// Find the previous incomplete assignment
		for (this.currentTargetAssignmentIndex = pos; this.currentTargetAssignmentIndex >= 0 && this.members[this.currentTargetAssignmentIndex].related != null; this.currentTargetAssignmentIndex--){}
		// If we got to -1, start from the end
		if (this.currentTargetAssignmentIndex < 0) {
			for (this.currentTargetAssignmentIndex = this.members.length-1; this.currentTargetAssignmentIndex >= 0 && this.members[this.currentTargetAssignmentIndex].related != null; this.currentTargetAssignmentIndex--){}
		}

		if (this.currentTargetAssignmentIndex === originalPos) {
			// We ended up at our own position, so this is the last remaining unannotated pattern
			this.currentTargetAssignmentIndex = originalPos;
			alert("You are at the last remaining unannotated pattern.")
		}
		else if (this.currentTargetAssignmentIndex > -1) {
			// Found prev unannotated pattern, so go to it
			this.members[this.currentTargetAssignmentIndex].goTo();
			this.updatePanel();
		} else {
			// There are no remaining unannotated patterns (including current position)
			this.currentTargetAssignmentIndex = originalPos;
			alert("There are no remaining unannotated patterns.")
		}
	};

	// Go to the next assignment.
	nextPosition() {

		if (this.currentTargetAssignmentIndex === null) {
			this.resume();
		}
		if (++this.currentTargetAssignmentIndex >= this.members.length) {

			// The user reached the end of the assignments.
			this.stop();

			// If the assignment is complete, display congratulatory message
			alert("Congratulations, you've completed the assignment!");

		} else {
			this.members[this.currentTargetAssignmentIndex].goTo();
		}

		this.updatePanel();

	};

	// Go to the previous assignment.
	prevPosition() {

		if (this.currentTargetAssignmentIndex === null) {
			this.currentTargetAssignmentIndex = this.members.length - 1;
			this.members[this.currentTargetAssignmentIndex].goTo();
		}
		if (--this.currentTargetAssignmentIndex < 0) {
			// TODO: the entire assignment is complete
			this.stop();
		} else {
			this.members[this.currentTargetAssignmentIndex].goTo();
		}

		this.updatePanel();

	};
	
	render() {

		// Grab a reference to the assignment panel area
		const assignmentPanelArea = document.getElementById('assignmentPanelArea');

		// Persist this reference for event handlers
		const assignmentset = this;

		// Build & attach the panel content
		this.assignmentPanelDOMElement = document.createElement('div');
		this.assignmentPanelDOMElement.className = 'assignment-panel';
		this.assignmentPanelDOMElement.innerHTML =

			'<h5>' + this.name + '</h5>' +

			// '<div class="form-group">' +
				// '<label for="formControlRange">Example Range input</label>' +
				'<input type="range" class="form-control-range" id="formControlRange'+this.id+'" min="1" max="' + this.members.length + '" step="1" value="0" style="background: none; margin-top: 10px;">' +
				
				


				// '<div class="btn-group" style="float: right" role="group" aria-label="Next & previous buttons">' +
				// 	'<button type="button" class="btn btn-secondary btn-sm" id="prevAssignmentButton">Prev</button>' +
				// 	'<button type="button" class="btn btn-secondary btn-sm" id="nextAssignmentButton">Next</button>' +
				// '</div>' +

				// have a counter and range next to the range (e.g. "1/2")
				'<table style="width: 100%; margin-top: 5px; margin-bottom: 10px;"><tbody><tr>' +
					'<td style="width: 60%; font-size: 0.7em; color: #303030;">' +
						'Position<br><span class="positionNumber"></span> out of ' + this.members.length +
					'</td>' +
					'<td align="right">' +
						'<input type="number" name="positionInput" min="1" max="' + this.members.length + '" style="width: 60px;">' +
					'</td>' +
				'</tr></tbody></table>' +

			// '</div>' +

			'<div class="progress">' +
				'<div class="progress-bar" role="progressbar" aria-valuenow="" aria-valuemin="0" aria-valuemax="' + this.members.length + '"></div>' +
			'</div>' +

			'<table style="width: 100%; margin-top: 6px;"><tbody><tr>' +
				'<td style="width: 60%; font-size: 0.7em; color: #303030;">' +
					'Completed<br><span class="completedCount"></span> out of ' + this.members.length +
				'</td>' +
				'<td>' +
					'<div class="btn-group" style="float: right" role="group" aria-label="Next & previous buttons"></div>' +
				'</td>' +
			'</tr></tbody></table>';

		assignmentPanelArea.appendChild(this.assignmentPanelDOMElement);

		// Build button components which may be used in various states
		this.startButtonDOMElement = document.createElement('button');
		this.startButtonDOMElement.setAttribute('type', 'button');
		this.startButtonDOMElement.className = 'btn btn-sm btn-success';
		if (this.getCompletedCount() >= this.members.length) {
			this.startButtonDOMElement.classList.remove('btn-success');
			this.startButtonDOMElement.classList.add('btn-secondary');
			this.startButtonDOMElement.innerText = 'Complete!';
			this.assignmentPanelDOMElement.style.backgroundColor = '#ddd';
		} else {
			this.startButtonDOMElement.innerText = this.getCompletedCount() > 0 ? 'Resume' : 'Begin';
		}
		this.startButtonDOMElement.onclick = function () { assignmentset.resume(); };

		this.prevButtonDOMElement = document.createElement('button');
		this.prevButtonDOMElement.setAttribute('type', 'button');
		this.prevButtonDOMElement.setAttribute('title', 'Go to previous unannotated pattern');
		this.prevButtonDOMElement.className = 'btn btn-sm btn-secondary';
		this.prevButtonDOMElement.innerText = 'Prev';
		this.prevButtonDOMElement.onclick = function() { assignmentset.prevIncompletePosition(); };

		this.nextButtonDOMElement = document.createElement('button');
		this.nextButtonDOMElement.setAttribute('type', 'button');
		this.nextButtonDOMElement.setAttribute('title', 'Go to next unannotated pattern');
		this.nextButtonDOMElement.className = 'btn btn-sm btn-secondary';
		this.nextButtonDOMElement.innerText = 'Next';
		this.nextButtonDOMElement.onclick = function() { assignmentset.nextIncompletePosition(); };

		this.stopButtonDOMElement = document.createElement('button');
		this.stopButtonDOMElement.setAttribute('type', 'button');
		this.stopButtonDOMElement.className = 'btn btn-sm btn-danger';
		this.stopButtonDOMElement.innerHTML = '<i class="fa fa-stop" aria-hidden="true"></i>';
		this.stopButtonDOMElement.onclick = function() { assignmentset.stop(); };

		// Attach the start button
		this.assignmentPanelDOMElement.querySelector('.btn-group').appendChild(this.startButtonDOMElement);

		// Ensure that the assignment focus option is showing
		document.getElementById('assignmentFocusOption').style.display = 'inline-block';

		// Update panel numbers
		this.updatePanel();

		const postText = document.createElement('p');
		postText.className = "assignment-panel-bottom-label";
		postText.innerText = 'Assignment'
		assignmentPanelArea.appendChild(postText);

		// Attach event handler to the range input
		this.assignmentPanelDOMElement.querySelector('input[type="range"]').onmouseup = function() {
			assignmentset.setPosition(parseInt(this.value) - 1);
		};

		// Attach event handler to the position input
		this.assignmentPanelDOMElement.querySelector('input[name="positionInput"]').onchange = function() {

			// Output a dialog error if the position is out of range
			if (parseInt(this.value) < 1 || parseInt(this.value) > assignmentset.members.length) {
				alert('Position must be between 1 and ' + assignmentset.members.length);
				return;
			}

			assignmentset.setPosition(parseInt(this.value) - 1);
		};

		// Make the assignment panel area visible since we have at least one
		// assignment panel showing.
		assignmentPanelArea.style.display = 'block';
		
	};

	// Begin or resume the assignment set, optionally starting at a specific position.
	resume(pos) {

		if (this.hasBegun()) {
			console.log('Error! Assignment set resume() called when it was already started!');
			return;
		}

		// Inform the assignment manager we're now the current target assignment set
		// TODO: put other assignment sets to the stopped state
		this.parentAssignmentManager.currentTargetAssignmentSet = this;

		if (pos != null) {
			// If a specific starting position was provided, use it
			this.currentTargetAssignmentIndex = pos;
		} else if (this.getCompletedCount() >= this.members.length) {
			// If the assignment is already complete, start at the beginning
			this.currentTargetAssignmentIndex = 0;
		} else {
			// Otherwise, start at the first incomplete assignment
			for (this.currentTargetAssignmentIndex = 0; this.currentTargetAssignmentIndex < this.members.length && this.members[this.currentTargetAssignmentIndex].related != null; this.currentTargetAssignmentIndex++){}
		}
		if (this.currentTargetAssignmentIndex < this.members.length) {
			this.members[this.currentTargetAssignmentIndex].goTo();
			const btngrp = this.assignmentPanelDOMElement.querySelector('.btn-group');
			clearDOMElementContent(btngrp);
			btngrp.appendChild(this.stopButtonDOMElement);
			btngrp.appendChild(this.prevButtonDOMElement);
			btngrp.appendChild(this.nextButtonDOMElement);
		} else {
			// The entire assignment is complete
			this.stop();
			alert('Your assignment is complete!');
		}

		this.updatePanel();

	};

	// Go to position
	setPosition(pos) {
		console.log("SET POSITION", pos);
		if (!this.hasBegun()) {
			this.resume(pos);
		} else {
			this.currentTargetAssignmentIndex = pos;
			this.members[this.currentTargetAssignmentIndex].goTo();
			this.updatePanel();
		}
	};

	stop() {
		console.log("STOP")
		this.parentAssignmentManager.currentTargetAssignmentSet = null;
		this.currentTargetAssignmentIndex = null;
		const btngrp = this.assignmentPanelDOMElement.querySelector('.btn-group');
		clearDOMElementContent(btngrp);
		if (this.getCompletedCount() >= this.members.length) {
			this.startButtonDOMElement.classList.remove('btn-success');
			this.startButtonDOMElement.classList.add('btn-secondary');
			this.startButtonDOMElement.innerText = 'Complete!';
			this.assignmentPanelDOMElement.style.backgroundColor = '#ddd';
		} else {
			this.startButtonDOMElement.innerText = this.getCompletedCount() > 0 ? 'Resume' : 'Begin';
		}
		this.assignmentPanelDOMElement.querySelector('.btn-group').appendChild(this.startButtonDOMElement);
		if (globalStateManager.currentFile) {
			globalStateManager.currentFile.resetZoomToOutermost();
		}

		this.updatePanel();
	};

	updatePanel() {
		console.log("UPDATE PANEL")
		const completedCount = this.getCompletedCount();
		const pct = Math.round(100*completedCount/this.members.length);

		const pbardom = this.assignmentPanelDOMElement.querySelector('.progress-bar');
		pbardom.style.width = pct+'%';
		pbardom.setAttribute('aria-valuenow', completedCount);

		console.log('here', this.currentTargetAssignmentIndex)
		this.assignmentPanelDOMElement.querySelector('.positionNumber').innerText = this.currentTargetAssignmentIndex || this.currentTargetAssignmentIndex === 0 ? this.currentTargetAssignmentIndex+1 : '-';
		this.assignmentPanelDOMElement.querySelector('input[name=positionInput]').value = this.currentTargetAssignmentIndex || this.currentTargetAssignmentIndex === 0 ? this.currentTargetAssignmentIndex+1 : '';

		this.assignmentPanelDOMElement.querySelector('.completedCount').innerText = completedCount;

		// Update the range position
		this.assignmentPanelDOMElement.querySelector('input[type="range"]').value = this.currentTargetAssignmentIndex || this.currentTargetAssignmentIndex === 0 ? this.currentTargetAssignmentIndex+1 : 1;

	};

}