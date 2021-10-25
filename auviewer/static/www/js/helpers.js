'use strict';

function classifyAnnotationInRelationToGraph(annotation, graph) {

	// Establish the current assignment pattern ID, if any
	const currentAssignmentID = getCurrentTargetAssignmentID();
	
	// Determine if the annotation/pattern series matches this current graph
	const annotationBelongsToThisGraph = annotation.series && graph.members.includes(annotation.series);

	// Determine if the pattern is the current workflow pattern
	const currentWorkflowPattern = annotation.id === currentAssignmentID || annotation.pattern_id === currentAssignmentID;

	if (currentAssignmentID && !currentWorkflowPattern && document.getElementById('assignmentFocusOption').checked) {
		return 'do_not_render';
	} else if (annotation.type === 'pattern') {
		if (annotationBelongsToThisGraph) {
			if (currentWorkflowPattern) {
				return 'own_pattern_target_assignment';
			} else {
				return 'own_pattern_not_target_assignment';
			}
		} else {
			if (currentWorkflowPattern) {
				return 'other_pattern_target_assignment';
			} else {
				return 'other_pattern_not_target_assignment';
			}
		}
	} else if (annotation.type === 'unsaved_annotation' || annotation.type === 'annotation') {
		if (annotationBelongsToThisGraph) {
			return 'own_annotation';
		} else {
			return 'other_annotation';
		}
	} else {
		return null;
	}
	
}

// Given a DOM element, clears all of its contents.
// See: https://jsperf.com/innerhtml-vs-removechild/15
function clearDOMElementContent(de) {
	try {
		while (de.firstChild) {
			de.removeChild(de.firstChild);
		}
	} catch (e) {
		console.log("Exception while clearing dom element content:", e);
	}
}

// Converts the first column of the series to date object, based on first
// column and basetime being in being in milliseconds.
function convertFirstColumnToDate(data, baseTime) {
	for (let i in data) {
			// Convert the ISO8601-format string into a Date object.
			data[i][0] = new Date((data[i][0] + baseTime) * 1000);
		}
}

// Creates a merged time series dataset of the series specified by groupSeries,
// pulling data from data. Assumes the datasets are in chronological order and
// that rows are distinct (i.e. there are not repeated times & values).
function createMergedTimeSeries(groupSeries, data) {

	// // Verify that all series members of the group are present.
	// for (let s of groupSeries) {
	// 	if (!data.hasOwnProperty(s)) {
	// 		return
	// 	}
	// }

	// For any member series that is not present, create an empty array
	// representing its data.
	for (let s of groupSeries) {
		if (!data.hasOwnProperty(s)) {
			data[s] = [];
		}
	}

	// Calculate the number of columns in the combined table. Each
	// series requires 3 columns (min, max, raw), and additionally
	// there will be the single time column.
	const numColumns = groupSeries.length * 3 + 1;

	// Create our array of iteration pointers
	let iterationIndexPointers = [];
	for (let i = 0; i < groupSeries.length; i++) {
		iterationIndexPointers.push(0);
	}

	// Allocate the combined series array
	let combinedSeries = [];

	// In the loop, this will hold the group index indicating which
	// series' current member has the earliest time.
	let seriesIndexWithEarliest;

	while (true) {

		// Determine which array's current member has the earliest time. We
		// start and column 1 to skip the time column.
		seriesIndexWithEarliest = 0;
		for (let i = 1; i < groupSeries.length; i++) {
			if (iterationIndexPointers[seriesIndexWithEarliest] >= data[groupSeries[seriesIndexWithEarliest]].data.length ||
				(iterationIndexPointers[i] < data[groupSeries[i]].data.length && data[groupSeries[i]].data[iterationIndexPointers[i]][0].valueOf() < data[groupSeries[seriesIndexWithEarliest]].data[iterationIndexPointers[seriesIndexWithEarliest]][0].valueOf())) {
				seriesIndexWithEarliest = i;
			}
		}

		// Create an array representing the row to be added
		let newRow = [];

		// Set the row's time, and default the column values to null.
		newRow[0] = data[groupSeries[seriesIndexWithEarliest]].data[iterationIndexPointers[seriesIndexWithEarliest]][0];
		for (let i = 1; i < numColumns; i++) {
			newRow[i] = null;
		}

		// Set the row's appropriate column value with the
		// earliest-in-time series we found.
		newRow[3*seriesIndexWithEarliest + 1] = data[groupSeries[seriesIndexWithEarliest]].data[iterationIndexPointers[seriesIndexWithEarliest]][1];
		newRow[3*seriesIndexWithEarliest + 2] = data[groupSeries[seriesIndexWithEarliest]].data[iterationIndexPointers[seriesIndexWithEarliest]][2];
		newRow[3*seriesIndexWithEarliest + 3] = data[groupSeries[seriesIndexWithEarliest]].data[iterationIndexPointers[seriesIndexWithEarliest]][3];
		iterationIndexPointers[seriesIndexWithEarliest]++;

		// If any subsequent series have an equal time, add their
		// column values as well and increment their iteration index
		// pointers.
		for (let i = seriesIndexWithEarliest + 1; i < groupSeries.length; i++) {

			if (iterationIndexPointers[i] < data[groupSeries[i]].data.length && data[groupSeries[i]].data[iterationIndexPointers[i]][0].valueOf() === newRow[0].valueOf()) {
				newRow[3*i + 1] = data[groupSeries[i]].data[iterationIndexPointers[i]][1];
				newRow[3*i + 2] = data[groupSeries[i]].data[iterationIndexPointers[i]][2];
				newRow[3*i + 3] = data[groupSeries[i]].data[iterationIndexPointers[i]][3];
				iterationIndexPointers[i]++;
			}
		}

		// Add the new row to the combined series.
		combinedSeries.push(newRow);

		// Determine if we have reached the end of all series.
		let allSeriesHaveEnded = true;
		for (let i = 0; i < iterationIndexPointers.length; i++) {
			if (iterationIndexPointers[i] < data[groupSeries[i]].data.length) {
				allSeriesHaveEnded = false;
				break;
			}
		}

		// If all series have ended, break the loop.
		if (allSeriesHaveEnded) {
			break;
		}

	}

	return combinedSeries;

}

// Meshes a subset of time-series data into a superset, where the subset
// replaces the span of time it represents in the superset. Assumes first column
// is time, both sets are ordered by time, and both sets have the same number of
// columns. A new meshed data set is returned, and originals are unmodified.
function createMeshedTimeSeries(superset, subset) {

	// If the subset is empty, return the superset
	if (typeof subset === 'undefined' ||
		subset.constructor !== Array ||
		subset.length < 1) {
		return superset;
	}

	// If the superset is empty, return the subset
	if (typeof superset === 'undefined' ||
		superset.constructor !== Array ||
		superset.length < 1) {
		return subset;
	}
	
	// We expect each array to have at least two columns and have the same
	// number of columns.
	if (superset[0].constructor !== Array ||
		subset[0].constructor !== Array ||
		superset[0].length < 2 ||
		subset[0].length < 2 ||
		superset[0].length !== subset[0].length) {
		return;
	}

	// Will hold the relevant places to slice the outerDataset.
	let sliceIndexFirstSegment = 0;
	let sliceIndexSecondSegment = 0;

	// Determine outerDataset index of the data point just after innerDataset
	// starts. We will find the index just *after* the last data point before
	// innerDataset starts. However, that's okay, because sliceIndexFirstSegment
	// will be the second parameter in a slice call, which indicates an element
	// that will not be included in the resulting array.
	// TODO(gus): Convert this to binary search.
	while (sliceIndexFirstSegment < superset.length && superset[sliceIndexFirstSegment][0] < subset[0][0]) {
		sliceIndexFirstSegment++;
	}

	// Determine outerDataset index of the data point just after innerDataset ends.
	sliceIndexSecondSegment = sliceIndexFirstSegment;
	while (sliceIndexSecondSegment < superset.length && superset[sliceIndexSecondSegment][0] <= subset[subset.length-1][0]) {
		sliceIndexSecondSegment++;
	}

	// Return the meshed dataset.
	return superset.slice(0, sliceIndexFirstSegment).concat(subset, superset.slice(sliceIndexSecondSegment));

}

// Returns a deep copy of any JSON-serializable variable.
function deepCopy(o) {
	return JSON.parse(JSON.stringify(o));
}

function getAnnotationCategoryLayerNumber(category) {
	switch (category) {
		case 'do_not_render': return -1; break;
		case 'other_pattern_not_target_assignment': return 0; break;
		case 'own_pattern_not_target_assignment': return 1; break;
		case 'other_annotation': return 2; break;
		case 'own_annotation': return 4; break;
		case 'own_pattern_target_assignment':
		case 'other_pattern_target_assignment': return 3; break;
		default: console.log("Error! Unrecognized category provided to getAnnotationCategoryLayerNumber():", category);
	}
}

// Returns the current target assignment ID or null
function getCurrentTargetAssignmentID() {
	const proj = globalStateManager.currentProject;
	try {
		return proj.assignmentsManager.currentTargetAssignmentSet.members[proj.assignmentsManager.currentTargetAssignmentSet.currentTargetAssignmentIndex].id;
	} catch {}
	return null;
}

// Returns a 2-member array with date & time strings that can be provided to an
// HTML5 input form field of type date & time respectively. Format will be
// ['2020-12-15', '01:27:36'].
function getHTML5DateTimeStringsFromDate(d) {

	// Date string
	let ds = d.getFullYear().toString() + '-' + (d.getMonth()+1).toString().padStart(2, '0') + '-' + d.getDate().toString().padStart(2, '0');

	// Time string
	let ts = d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0') + ':' + d.getSeconds().toString().padStart(2, '0') + '.' + d.getMilliseconds().toString().padStart(3, 0);

	// Return them in array
	return [ds, ts];
}

// Holds the next incremental local ID.
let localIDTracker = 0;

// Generate an incrementing unique local id
function localIDGenerator() {
	return "local" + localIDTracker++
}

/**
 * Simple object check. Taken from @Salakar's SO answer at:
 * https://stackoverflow.com/questions/27936772/how-to-deep-merge-instead-of-shallow-merge
 * @param item
 * @returns {boolean}
 */
function isObject(item) {
  return (item && typeof item === 'object' && !Array.isArray(item));
}

/**
 * Deep merge two objects. Taken from @Salakar's SO answer at:
 * https://stackoverflow.com/questions/27936772/how-to-deep-merge-instead-of-shallow-merge
 * @param target
 * @param ...sources
 */
function mergeDeep(target, ...sources) {
  if (!sources.length) return target;
  const source = sources.shift();

  if (isObject(target) && isObject(source)) {
    for (const key in source) {
      if (isObject(source[key])) {
        if (!target[key]) Object.assign(target, { [key]: {} });
        mergeDeep(target[key], source[key]);
      } else {
        Object.assign(target, { [key]: source[key] });
      }
    }
  }

  return mergeDeep(target, ...sources);
}

// Take the offset of a mouse event on the dygraph canvas and
// convert it to a percentages from the left.
function offsetToPercentage(g, offsetX) {
	// This is calculating the pixel offset of the leftmost date.
	let xOffset = g.toDomCoords(g.xAxisRange()[0], null)[0];

	// x y w and h are relative to the corner of the drawing area,
	// so that the upper corner of the drawing area is (0, 0).
	let x = offsetX - xOffset;

	// This is computing the rightmost pixel, effectively defining the width.
	let w = g.toDomCoords(g.xAxisRange()[1], null)[0] - xOffset;

	// Percentage from the left.
	// The (1-) part below changes it from "% distance down from the top"
	// to "% distance up from the bottom".
	return w === 0 ? 0 : (x / w);
}

// This is a specialized and temporary function that pads a 3-column 2d array /
// set of data points with an additional, 4th column of null values. It modifies
// the original array if it is 3 columns; otherwise, nothing is changed.
// TODO(gus): Remove later; this is temporary.
function padDataIfNeeded(data) {

	// Return if there are no data points
	if (typeof data === 'undefined' || data.length < 1) {
		return;
	}

	// Return if padding is not necessary
	if (data[0].length !== 3) {
		return;
	}

	for (let i in data) {
		data[i].push(null);
	}

}

function showFeaturizationPanel(s) {
	globalAppConfig.verbose && console.log('showFeaturizationPanel('+s+') called.');

	const panel = $$('featurize_window');
	if (panel) {
		panel.show()
	} else {

		// Setup handler
		const featurize = function() {

			$$('featurize_window').showProgress();

			const vals = $$('featurize_form').getValues();
			const featurizer = vals['_featurizer'];
			delete vals['_featurizer'];
			const series = vals['_series']
			delete vals['_series']
			const params = vals;

			// Grab the x-axis range from the last showing graph (all graphs should be
			// showing the same range since they are synchronized).
			const f = globalStateManager.currentFile;
			const g = f.getGraphForSeries(series);
			let xRange = null;
			try {
				xRange = g.dygraphInstance.xAxisRange();
			} catch (error) {
				// The graph may not be showing
				try {
					xRange = f.getFirstShowingGraph().xAxisRange();
				} catch (error) {
					// No graphs may be showing
					xRange = f.getOutermostZoomWindow();
				}
			}
			const left = xRange[0]/1000-f.fileData.baseTime;
			const right = xRange[1]/1000-f.fileData.baseTime;

			requestHandler.featurize(globalStateManager.currentProject.id, globalStateManager.currentFile.id, series, featurizer, left, right, params, function(data) {
				$$('featurize_window').hideProgress();

				if (!data['success']) {
					console.log('Featurization was not successful.');
					let msg = 'Featurization was not successful.';
					if (data.hasOwnProperty('error_message')) {
						msg = data['error_message'];
					}
					alert(msg);
					return;
				}
				globalStateManager.currentFile.addTemporaryFeatureGraph(data);
			});
		}

		// Assemble the array of available featurizers for the dropdown menu
		let featurizerOptions = [];
		for (const fid of Object.getOwnPropertyNames(featurizersPayload)) {
			featurizerOptions.push({
				id: fid,
				value: featurizersPayload[fid]['name'],
			});
		}

		let seriesOptions = Object.getOwnPropertyNames(globalStateManager.currentFile.graphs);

		webix.ui({
			view: 'window',
			id: 'featurize_window',
			close: true,
			head: "Featurize",
			move: true,
			position: 'center',
			width: 400,
			body: {
				view: 'form',
				//width: 650,
				//height: 500,
				id: 'featurize_form',
				on: { onSubmit: featurize },
				elements: [
					{
						view: "combo",
						id: 'featuze_window_featurizer_dropdown',
						//width:300,
						labelWidth: 'auto',
						label: 'Featurizer',
						name: "_featurizer",
						options: featurizerOptions,
						suggest: {
							data: featurizerOptions,
							filter: function(obj, filter) {
								return obj.value.toLowerCase().indexOf(filter.toLowerCase()) != -1;
							}
						},
						on: {
							onChange: function () {
								const featurizerID = this.getValue();
								if (featurizersPayload.hasOwnProperty(featurizerID) && featurizersPayload[featurizerID]['fields'].length > 0) {
									const fieldset = {
										view: 'fieldset',
										id: 'featurizer_params_fieldset',
										label: 'Featurizer Parameters',
										paddingY: 40,
										body: {
											rows: featurizersPayload[featurizerID]['fields'],
										}
									};
									if ($$('featurizer_params_fieldset')) {
										// The fieldset exists, so replace it.
										const x = webix.ui(fieldset, $$('featurize_form'), $$('featurizer_params_fieldset'));
									} else {
										// The fieldset doesn't exist, so add it.
										const pos = $$("featurize_form").index($$("featurize_window_generate_button"));
										$$('featurize_form').addView(fieldset, pos)
									}
								} else {
									console.log("Error: Couldn't find featurizer ID '" + featurizerID + "' payload!", featurizersPayload)
									$$('featurize_form').removeView('featurizer_params_fieldset');
								}
							}
						}
					},
					{
						view: "combo",
						id: 'featurize_window_series_dropdown',
						//width:300,
						labelWidth: 'auto',
						label: 'Series',
						name: "_series",
						options: seriesOptions,
						suggest: {
							data: seriesOptions,
							filter: function(obj, filter) {
								return obj.value.toLowerCase().indexOf(filter.toLowerCase()) != -1;
							}
						},
					},
					{
						view: 'fieldset',
						id: 'rw_params_fieldset',
						label: 'Rolling Window Parameters',
						paddingY: 48,
						body: {
							rows: [
								{
									view: 'text',
									label: 'Window Size (e.g. 10ms, 3s, 5min)',
									//labelWidth: 250,
									labelWidth: 'auto',
									labelAlign: 'left',
									inputAlign: 'right',
									name: 'window_size',
									id: 'window_size',
									// width: 120,
									on: {
										onFocus: function () {
											this.getInputNode().select()
										}
									},
								},
							],
						},
					},
					{
						view: 'button',
						id: 'featurize_window_generate_button',
						value: 'Generate',
						tooltip: 'Generate the featurization and display in the viewer when ready.',
						click: featurize
					},
				]
			},
		}).show();
	}

	$$('featurize_window_series_dropdown').setValue(s)

	webix.extend($$("featurize_window"), webix.ProgressBar);

}

// Show the graph control panel for a given graph series (which corresponds to file.graphs[].fullName of the
// corresponding Graph class instance).
function showGraphControlPanel(s) {
	const g = globalStateManager.currentFile.getGraphForSeries(s);
	const dg = g.dygraphInstance;

	// Setup some handlers
	const updateRange = function() {
		const vals = $$('graph_range_form_'+s).getValues();
		g.dygraphInstance.updateOptions({
			valueRange: [vals['ymin'], vals['ymax']],
		});
	};
	const updateHeight = function() {
		const vals = $$('graph_height_form_'+s).getValues();
		g.graphWrapperDomElement.style.height = vals['height'] + 'px';
		if (g.isShowing()) {
			g.hide();
			g.show();
		}
	};

	const panel = $$('graph_config_window_'+s);
	if (panel) {
		panel.show()
	} else {
		webix.ui({
			view: 'window',
			id: 'graph_config_window_'+s,
			close: true,
			head: "Graph Options &mdash; "+g.shortName,
			move: true,
			//resize: true,
			//height: 250,
			//width: 200,
			position: 'center',
			body: {
				cols: [
					{
						view: 'form',
						id: 'graph_range_form_'+s,
						on: { onSubmit: updateRange },
						elements: [
							{view: 'template', template: 'Y-Axis Range', type: 'header', borderless: true},
							{
								view: 'text',
								label: 'y min',
								name: 'ymin',
								width: 200,
								value: dg.axes_[0].valueRange[0],
								on: { onFocus: function() { this.getInputNode().select() } },
							},
							{
								view: 'text',
								label: 'y max',
								name: 'ymax',
								width: 200,
								value: dg.axes_[0].valueRange[1],
								on: { onFocus: function() { this.getInputNode().select() } },
							},
							{
								view: 'button', value: 'Update', click: updateRange
							},
						]
					},
					{
						view: 'form',
						id: 'graph_height_form_'+s,
						on: { onSubmit: updateHeight },
						elements: [
							{view: 'template', template: 'Graph Height', type: 'header', borderless: true},
							{
								view: 'text',
								label: 'Height (px)',
								name: 'height',
								width: 150,
								value: g.graphWrapperDomElement.style.height.slice(0, -2),
								on: { onFocus: function() { this.getInputNode().select() } },
							},
							{
								view: 'button', value: 'Update', click: updateHeight
							},
						]
					},
				]
			},
		}).show();
	}
}

// Returns a simplified name of the series, with the path components removed and
// the column removed. E.g. /path/to/series:col becomes series:col. If the col
// name is "value", it is omitted.
function simpleSeriesName(fullname) {

	let s = fullname.split('/');
	let simplifiedTitle = s[s.length-1];

	// If the simplified title is "seriesname:value", simplify further to remove :value.
	s = simplifiedTitle.split(':');
	if (s.length === 2 && s[1] === "value") {
		simplifiedTitle = s[0];
	}

	return simplifiedTitle

}

// Verifies that an object has a nested hierarchy of properties. For example,
// given props = ['a', 'b', 'c'], the function will return true if the given
// object has obj['a']['b']['c'] and false otherwise.
function verifyObjectPropertyChain(obj, props) {

	if (!Array.isArray(props) || props.length < 1) {
		return true;
	} else if (Array.isArray(obj) && props[0] === '[]') {
		let ret = true;
		for (const arrObj of obj) {
			if (!verifyObjectPropertyChain(arrObj, props.slice(1))) {
				ret = false;
			}
		}
		return ret;
	} else if (typeof obj === 'object' && obj !== null && obj.hasOwnProperty(props[0])) {
		return verifyObjectPropertyChain(obj[props[0]], props.slice(1));
	} else {
		return false;
	}

}

// Adjusts x inward by zoomInPercentage%
// Split it so the left axis gets xBias of that change and
// right gets (1-xBias) of that change.
//
// If a bias is missing it splits it down the middle.
function zoom(g, zoomInPercentage, xBias) {
	xBias = xBias || 0.5;
	let axis = g.xAxisRange();
	let delta = axis[1] - axis[0];
	let increment = delta * zoomInPercentage;
	let foo = [increment * xBias, increment * (1-xBias)];
	g.updateOptions({
		dateWindow: [ axis[0] + foo[0], axis[1] - foo[1] ]
	});
}