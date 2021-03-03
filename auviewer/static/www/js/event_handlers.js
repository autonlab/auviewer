'use strict';

/*
These event handlers rely on binding to either file or graph class instance.
 */

// Ends an annotation highlighting action in response to a mouse-up event.
function handleAnnotationHighlightEnd (event, g, context, fileOrGraph) {

	let left = Math.min(context.dragStartX, context.dragEndX);
	let right = Math.max(context.dragStartX, context.dragEndX);
	let from = g.toDataXCoord(left)/1000 - ('file' in fileOrGraph ? fileOrGraph.file.fileData.baseTime : fileOrGraph.fileData.baseTime);
	let to = g.toDataXCoord(right)/1000 - ('file' in fileOrGraph ? fileOrGraph.file.fileData.baseTime : fileOrGraph.fileData.baseTime);

	// Get a reference to the graph instance. Dygraphs implements the click
	// callback poorly, so we have to get it in a convoluted way.
	let graph = $(event.path[2]).data('graphClassInstance');

	// Warning if annotating a group
	if (graph.isGroup) {
		alert("You are annotating a group of series. Please select the individual series you wish to annotate from the Show/Hide Graphs interface.");
	}

	// Create a new annotation
	const destinationSet = globalStateManager.currentFile.getAnnotationSetByID('general');
	let annotation = new Annotation(destinationSet, {
		file_id: globalStateManager.currentFile.id,
		filename: globalStateManager.currentFile.name,
		series: graph.members[0],
		begin: from,
		end: to
	}, 'unsaved_annotation');
    destinationSet.addMember(annotation);

	// Show the annotation dialog
    annotation.showDialog();

	// Clear the grey rectangle that was drawn for the user interaction of spanning the annotation section.
	g.clearZoomRect_();

	// Reset context variables
	context.mvIsAnnotating = false;
	context.mvAnnotatingMoved = false;

	//DygraphInteraction.maybeTreatMouseOpAsClick(event, g, context);

	// The zoom rectangle is visibly clipped to the plot area, so its behavior
	// should be as well.
	// See http://code.google.com/p/dygraphs/issues/detail?id=280
	// let plotArea = g.getArea();
	// if (context.regionWidth >= 10 && context.dragDirection == utils.HORIZONTAL) {
	//   let left = Math.min(context.dragStartX, context.dragEndX),
	//       right = Math.max(context.dragStartX, context.dragEndX);
	//   left = Math.max(left, plotArea.x);
	//   right = Math.min(right, plotArea.x + plotArea.w);
	//   if (left < right) {
	//     g.doZoomX_(left, right);
	//   }
	//   context.cancelNextDblclick = true;
	// } else if (context.regionHeight >= 10 && context.dragDirection == utils.VERTICAL) {
	//   let top = Math.min(context.dragStartY, context.dragEndY),
	//       bottom = Math.max(context.dragStartY, context.dragEndY);
	//   top = Math.max(top, plotArea.y);
	//   bottom = Math.min(bottom, plotArea.y + plotArea.h);
	//   if (top < bottom) {
	//     g.doZoomY_(top, bottom);
	//   }
	//   context.cancelNextDblclick = true;
	// }
	context.dragStartX = null;
	context.dragStartY = null;

	// Trigger a redraw
	g.updateOptions({});
}

// Adjusts the annotation highlight in response to a mouse-move event.
function handleAnnotationHighlightMove (event, g, context) {

    // The user's mouse has now moved since starting an annotation draw.
	context.mvAnnotatingMoved = true;

	// context.dragEndX = utils.dragGetX_(event, context);
	// context.dragEndY = utils.dragGetY_(event, context);
	context.dragEndX = Dygraph.pageX(event) - context.px;
	context.dragEndY = Dygraph.pageY(event) - context.py;

	let xDelta = Math.abs(context.dragStartX - context.dragEndX);
	let yDelta = Math.abs(context.dragStartY - context.dragEndY);

	// drag direction threshold for y axis is twice as large as x axis
	//context.dragDirection = xDelta < yDelta / 2 ? utils.VERTICAL : utils.HORIZONTAL;
	context.dragDirection = xDelta < yDelta / 2 ? 2 : 1;

	g.drawZoomRect_(context.dragDirection, context.dragStartX, context.dragEndX, context.dragStartY, context.dragEndY, context.prevDragDirection, context.prevEndX, context.prevEndY);

	context.prevEndX = context.dragEndX;
	context.prevEndY = context.dragEndY;
	context.prevDragDirection = context.dragDirection;
}

// Begins an annotation highlighting action in response to a mouse-down event.
function handleAnnotationHighlightStart (event, g, context) {

    // Mark in our context that the user has begun drawing an annotation segment.
	context.mvIsAnnotating = true;

	// The user's mouse has not moved yet after starting an annotation draw.
	context.mvAnnotatingMoved = false;

}

// The click callback handler displays the annotation input form if the user
// clicks on an annotation. If multiple annotations are under the mouse-click,
// the first input form is displayed for the first annotation found.
function handleClick(e, x) {

	// Get reference to current file
	let file = globalStateManager.currentFile;

	// Get a reference to the graph instance. Dygraphs implements the click
	// callback poorly, so we have to get it in a convoluted way.
	let graph = $(e.path[2]).data('graphClassInstance');

	// console.log("Handling canvas click. # Annotations:", e.offsetX, file.annotationsAndPatternsToRender);

	let highestLayerFound = -1;
	let annotationFound = null;

	// Iterate through the annotations to look for annotations under the click
	for (let i = 0; i < file.annotationsAndPatternsToRender.length; i++) {

		let itemOffsetXLeft = file.annotationsAndPatternsToRender[i].offsetXLeft
		let itemOffsetXRight = file.annotationsAndPatternsToRender[i].offsetXRight

		// Minimum alert width is 3
		if (itemOffsetXRight-itemOffsetXLeft < 3) {
			itemOffsetXLeft--;
			itemOffsetXRight = itemOffsetXLeft + 3;
		}

		if (e.offsetX >= itemOffsetXLeft && e.offsetX <= itemOffsetXRight) {
			if (
				!file.annotationsAndPatternsToRender[i].series ||
				(!graph.isGroup && file.annotationsAndPatternsToRender[i].series === graph.fullName) ||
				(graph.isGroup && graph.members.includes(file.annotationsAndPatternsToRender[i].series))
			) {
				console.log("Found", file.annotationsAndPatternsToRender[i]);

				// We may find multiple annotations/patterns under the click.
				// Given multiple finds, we decide which to show based on which
				// would be showing to the user. This is based on the layering
				// of the rendering (see handleUnderlayRedraw). So, a higher
				// layer will win, and given two annotations in the same layer,
				// the later index (position in annotationsAndPatternsToRender)
				// will win.
				const newFindLayer = getAnnotationCategoryLayerNumber(classifyAnnotationInRelationToGraph(file.annotationsAndPatternsToRender[i], graph));
				if (newFindLayer >= highestLayerFound) {
					highestLayerFound = newFindLayer;
					annotationFound = file.annotationsAndPatternsToRender[i];
				}

			}
		}
	}

	// If an annotation was found, show its dialog
	if (annotationFound != null) {
		annotationFound.showDialog();
	}

}

// Handle double-click for restoring the original zoom.
function handleDoubleClick(event, g, context) {
	('file' in this ? this.file.resetZoomToOutermost() : this.resetZoomToOutermost());
}

// Handle mouse-down for pan & zoom
function handleMouseDown(event, g, context) {

	context.initializeMouseDown(event, g, context);

	if (event.altKey) {
		handleAnnotationHighlightStart(event, g, context);
	}
	else if (event.shiftKey) {
		Dygraph.startZoom(event, g, context);
	} else {
		context.medViewPanningMouseMoved = false;
		Dygraph.startPan(event, g, context);
	}

}

// Handle mouse-move for pan & zoom.
function handleMouseMove(event, g, context) {

	if (context.mvIsAnnotating) {
		handleAnnotationHighlightMove(event, g, context);
	}
	else if (context.isZooming) {
		Dygraph.moveZoom(event, g, context);
	}
	else if (context.isPanning) {
		context.medViewPanningMouseMoved = true;
		Dygraph.movePan(event, g, context);
	}

}

// Handle mouse-up for pan & zoom.
function handleMouseUp(event, g, context) {

	if (context.mvIsAnnotating) {
		handleAnnotationHighlightEnd(event, g, context, this);
	}
	else if (context.isZooming) {
		Dygraph.endZoom(event, g, context);
		if ('file' in this) {
			this.file.updateCurrentViewData();
		} else {
			this.updateCurrentViewData();
		}
	}
	else if (context.isPanning) {
		if (context.medViewPanningMouseMoved) {
			if ('file' in this) {
				this.file.updateCurrentViewData();
			} else {
				this.updateCurrentViewData();
			}
			context.medViewPanningMouseMoved = false;
		}
		Dygraph.endPan(event, g, context);
	}

}

// Handle shift+scroll or alt+scroll for zoom.
function handleMouseWheel(event, g, context) {

	// We allow the user to use either alt or shift plus the mousewheel to zoom.
	// We also allow the user to use pinch-to-zoom; the event.ctrlKey is true
	// when the user is using pinch-to-zoom gesture.
	if (event.ctrlKey || event.altKey || event.shiftKey) {

		let normal = event.detail ? event.detail * -1 : event.wheelDelta / 40;
		// For me the normalized value shows 0.075 for one click. If I took
		// that verbatim, it would be a 7.5%.
		let percentage = normal / 50;

		if (!(event.offsetX)){
			event.offsetX = event.layerX - event.target.offsetLeft;
		}

		let xPct = offsetToPercentage(g, event.offsetX);

		zoom(g, percentage, xPct);

		// Persist for timeout callback
		let file = 'file' in this ? this.file : this;

		// If we're zooming with the mouse-wheel or with pinch-to-zoom, we want
		// to set a timeout to update the current view's data. This is to prevent
		// repeated, overlapping calls in the midst of zooming.
		if (g.updateDataTimer != null) {
			clearTimeout(g.updateDataTimer);
		}
		g.updateDataTimer = setTimeout(function(){ g.updateDataTimer = null; file.updateCurrentViewData(); }, 300);


		//updateCurrentViewData(g);
		event.preventDefault();

	}

}

// This function is a plotter that plugs into dygraphs in order to plot a down-
// sampled data series. Plotting is not documented, so the best reference for
// plotting with dygraphs is to review http://dygraphs.com/tests/plotters.html
// and its source code.
function handlePlotting(e) {

	/*// We only want to run the plotter for the first series.
	if (e.seriesIndex !== 1) return;

	// We require two series for min & max.
	if (e.seriesCount != 3) {
	  throw "The medview plotter expects three y-values per series for downsample min, downsample max, and real value.";
	}*/

	// This is the official dygraphs way to plot all the series at once, per
	// source code of dygraphs.com/tests/plotters.html.
	if (e.seriesIndex !== 0) {
		return
	}

	// This is a reference to a proxy for the canvas element of the graph
	let cnv = e.drawingContext;

	// Holds positioning & dimensions (x, y, w, h) of the plot area, needed for
	// plotting points.
	let area = e.plotArea;

	// Line properties
	cnv.lineWidth = 1;

	// Plot each series, whether it be an individual series or a group of them.
	//console.log(e.allSeriesPoints);
	for (let i = 0; i + 2 < e.allSeriesPoints.length; i += 3) {
		
		// SERIES LINE - Plot line for the raw data column for the series, which
		// will be the third column of this series' set of three columns.
		if (this.template['drawLine'] && e.allSeriesPoints[i+2].length > 2) {

			cnv.strokeStyle = this.template['lineColor'];
			cnv.fillStyle = this.template['lineColor'];

			cnv.beginPath();

			let j = 0;

			// Get to the first non-NaN point and move there.
			for (; j < e.allSeriesPoints[i+2].length; j++) {
				if (!isNaN(e.allSeriesPoints[i+2][j].y)) {
					cnv.moveTo(e.allSeriesPoints[i+2][j].x * area.w + area.x, e.allSeriesPoints[i+2][j].y * area.h + area.y);
					break;
				}
			}

			// Iterate through rest of points and draw line.
			for (; j < e.allSeriesPoints[i+2].length; j++) {
				if (!isNaN(e.allSeriesPoints[i+2][j].y)) {
					cnv.lineTo(e.allSeriesPoints[i+2][j].x * area.w + area.x, e.allSeriesPoints[i+2][j].y * area.h + area.y);
				}
			}

			// Draw the line on the canvas
			cnv.stroke();

		}

		// SERIES DOTS - Plot dots for the raw data column for the series, which
		// will be thethird column of this series' set of three columns.
		if (this.template['drawDots']) {

			cnv.strokeStyle = this.template['dotColor'];
			cnv.fillStyle = this.template['dotColor'];

			for (let j = 0; j < e.allSeriesPoints[i + 2].length; j++) {

				if (isNaN(e.allSeriesPoints[i + 2][j].y)) {
					continue;
				}

				// cnv.fillRect(e.allSeriesPoints[i+2][j].x * area.w + area.x, e.allSeriesPoints[i+2][j].y * area.h + area.y, 2, 2)
				cnv.beginPath();
				cnv.arc(e.allSeriesPoints[i + 2][j].x * area.w + area.x, e.allSeriesPoints[i + 2][j].y * area.h + area.y, 1, 0, 2 * Math.PI);
				cnv.fill();

			}

		}

		// SERIES MIN-MAX - Plot the downsample min & max columns for the series,
		// which will be the first & second columns of this series' set of three
		// columns.
		cnv.strokeStyle = this.template['lineColor'];
		cnv.fillStyle = this.template['lineColor'];
		for (let j = 0; j < e.allSeriesPoints[i].length; j++) {

			if (isNaN(e.allSeriesPoints[i][j].y) || isNaN(e.allSeriesPoints[i+1][j].y)) {
				continue;
			}

			// There may be intervals wherein min==max, and to handle these, we must use a different drawing method.
			if (e.allSeriesPoints[i][j].y === e.allSeriesPoints[i+1][j].y) {

				cnv.fillRect(e.allSeriesPoints[i][j].x * area.w + area.x, e.allSeriesPoints[i][j].y * area.h + area.y, 1, 1)
				/*cnv.beginPath();
				cnv.arc(e.allSeriesPoints[i][j].x * area.w + area.x, e.allSeriesPoints[i][j].y * area.h + area.y, 2, 0, 2*Math.PI);
				cnv.fill();*/

			} else {

				// Begin a path (this instantiates a path object but does not draw it
				cnv.beginPath();

				// Start stroke at the min value
				cnv.moveTo(e.allSeriesPoints[i][j].x * area.w + area.x, e.allSeriesPoints[i][j].y * area.h + area.y);

				// End stroke at the max value
				cnv.lineTo(e.allSeriesPoints[i+1][j].x * area.w + area.x, e.allSeriesPoints[i+1][j].y * area.h + area.y);

				// Draw the line on the canvas
				cnv.stroke();

			}

		}

	}

}

// This is the callback function provided to dygraphs which draws the
// annotations on the canvas.
function handleUnderlayRedraw(canvas, area, g) {

	let file = globalStateManager.currentFile;

	let left, right, x, y, width, height;

	// Graph class instance
	const gci = $(g.graphDiv).parent().data('graphClassInstance');

	// console.log(canvas, area, g, Object.getOwnPropertyNames(g.setIndexByName_));

	// console.log("HI THERE", area, canvas)
	// canvas.strokeStyle = '#bb0000';
	// //canvas.fillRect(area.x, area.y+Math.floor(area.h/2), area.w, 1);
	// canvas.setLineDash([5,3]);
	// canvas.beginPath()
	// console.log("from", area.x, area.y+Math.floor(area.h/2))
	// console.log("to", area.x+area.w, Math.floor(area.h/2))
	// canvas.moveTo(area.x, area.y+Math.floor(area.h/2));
	// canvas.lineTo(area.x+area.w, Math.floor(area.h/2));
	// canvas.stroke();
	// canvas.setLineDash([]);

	// We need to make multiple passes to render in layers.
	for (let currentPassLayer = 0; currentPassLayer < 5; currentPassLayer++) {

		for (let i = 0; i < file.annotationsAndPatternsToRender.length; i++) {

			const category = classifyAnnotationInRelationToGraph(file.annotationsAndPatternsToRender[i], gci);
			if (category == null) {
				console.log("Error! Uncategorized/unexpected annotation type during graph in handleUnderlayRedraw():", file.annotationsAndPatternsToRender[i])
			}
			
			// This if statement controls which annotations/patterns are
			// included in each pass-through of the layering.
			if (currentPassLayer === getAnnotationCategoryLayerNumber(category)) {

				// // If this annotation does not belong to this series, move on.
				// if (file.annotations[i].series != null && !Object.getOwnPropertyNames(g.setIndexByName_).includes(file.annotations[i].series)) {
				// 	continue;
				// }

				left = g.toDomXCoord(new Date((file.annotationsAndPatternsToRender[i].begin + file.fileData.baseTime) * 1000));
				right = g.toDomXCoord(new Date((file.annotationsAndPatternsToRender[i].end + file.fileData.baseTime) * 1000));

				// Prepare the parameters we'll pass into fillRect. We impose a minimum
				// of 1px width so that, at any zoom level, the annotation is visible.
				x = left;
				y = area.y;
				width = right - left;
				if (width < 3) {
					width = 3
					x--;
				}
				height = area.h; //shortHighlights ? area.h/5*.85 : area.h;

				// Prepare styling for the section highlight.
				switch (category) {
					case 'own_annotation':
						canvas.fillStyle = this.template.ownAnnotationColor;
						break;
					case 'other_annotation':
						canvas.fillStyle = this.template.otherAnnotationColor;
						break;
					case 'own_pattern_not_target_assignment':
						canvas.fillStyle = this.template.ownPatternColor;
						break;
					case 'other_pattern_not_target_assignment':
						canvas.fillStyle = this.template.otherPatternColor;
						break;
					case 'own_pattern_target_assignment':
						canvas.fillStyle = this.template.ownCurrentWorkflowPatternColor;
						break;
					case 'other_pattern_target_assignment':
						canvas.fillStyle = this.template.otherCurrentWorkflowPatternColor;
						break;
					default:
						console.log("Error! Unexpected annotation category during graph in handleUnderlayRedraw():", file.annotationsAndPatternsToRender[i])
				}

				// Draw the section highlight.
				canvas.fillRect(x, y, width, height);

				// Set offsets for later click detection
				file.annotationsAndPatternsToRender[i].offsetXLeft = x;
				file.annotationsAndPatternsToRender[i].offsetXRight = x + width;

				// Draw annotation label text
				try {
					if (file.annotationsAndPatternsToRender[i].label.confidence) {
						canvas.font = "12px Arial";
						canvas.fillStyle = this.template.ownAnnotationLabelColor;
						canvas.textAlign = "center";
						canvas.fillText(file.annotationsAndPatternsToRender[i].label.confidence, x + (width / 2), y + 3 + height / 2/*area.y + (area.h * .1)*/);
					}
				} catch {}

			}

		}

	}

}
