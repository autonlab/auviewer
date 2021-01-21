'use strict';

class AssignmentsManager {

	constructor(parentProject, projectAssignments) {

		this.parentProject = parentProject;

		this.currentTargetAssignmentSet = null;

		this.assignmentsets = [];
		for (const pa of projectAssignments) {
			this.assignmentsets.push(new AssignmentSet(this, pa.id, pa.name, pa.description, pa.patterns));
		}

		globalAppConfig.verbose && console.log("Assignment Manager instantiated.", this);

	}

	// Handles a report that an annotation was created for a pattern which
	// possibly belongs to an assignment set.
	annotationCreatedForPattern(assignment_set_id, assignment_id, annotation) {
		for (const assignmentSet of this.assignmentsets) {
			if (assignmentSet.id === assignment_set_id) {
				assignmentSet.annotationCreatedForPattern(assignment_id, annotation);
				return;
			}
		}
	}

}