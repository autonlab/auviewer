'use strict';

function GraphSelectionMenu(file) {

	// References the parent File instance
	this.file = file;

	// References the controls area DOM element
	this.controlsDomElement = document.getElementById('series_toggle_controls');

}

// Adds a checkbox control to toggle display of the data series.
GraphSelectionMenu.prototype.add = function(series, checked) {

	// Create an outer div
	let div = document.createElement('DIV');
	div.className = 'form-check';

	// Attach the div to the control panel
	this.controlsDomElement.appendChild(div);

	// Create the checkbox DOM element
	let checkbox = document.createElement('INPUT');
	checkbox.setAttribute('type', 'checkbox');
	checkbox.setAttribute('value', series);
	checkbox.className = 'form-check-input';
	checkbox.id = series;

	// Check the box if the series is showing
	checkbox.checked = (checked !== false);

	// Attach the event handler that will add & remove the graph
	checkbox.onclick = this.checkboxClickHandler.bind(this);

	// Attach the checkbox to the div
	div.appendChild(checkbox);

	// Create & attach the span element
	let label = document.createElement('LABEL');
	label.setAttribute('for', series);
	label.className = 'form-check-label';
	label.innerText = ' '+series;

	// Attach the label to the div
	div.appendChild(label);

};

GraphSelectionMenu.prototype.checkboxClickHandler = function(e) {

	try {
		if (e.target.checked) {
			this.file.graphs[e.target.value].show();
		} else {
			this.file.graphs[e.target.value].remove();
		}
	}
	catch(error) {
		console.log("Could not find graph for checkbox click handling.", error);
	}

};