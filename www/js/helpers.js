'use strict';

// Creates a merged time series dataset of the series specified by groupSeries,
// pulling data from data.
function createMergedTimeSeries(groupSeries, data) {

	// Verify that all series members of the group are present.
	for (let s of groupSeries) {
		if (!data.hasOwnProperty(s)) {
			return
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
				(iterationIndexPointers[i] < data[groupSeries[i]].data.length && data[groupSeries[i]].data[iterationIndexPointers[i]][0] < data[groupSeries[seriesIndexWithEarliest]].data[iterationIndexPointers[seriesIndexWithEarliest]][0])) {
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
			if (data[groupSeries[i]].data[iterationIndexPointers[i]][0] === newRow[0]) {
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
console.log(combinedSeries);
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

// This is a specialized and temporoary function that pads a 3-column 2d array /
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