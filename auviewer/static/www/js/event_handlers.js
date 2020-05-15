'use strict';

/*
These event handlers rely on binding to either file or graph class instance.
 */

// Ends an annotation highlighting action in response to a mouse-up event.
function handleAnnotationHighlightEnd (event, g, context, fileOrGraph) {

	let file = globalStateManager.currentFile;

	let left = Math.min(context.dragStartX, context.dragEndX);
	let right = Math.max(context.dragStartX, context.dragEndX);
	let from = g.toDataXCoord(left)/1000 - ('file' in fileOrGraph ? fileOrGraph.file.fileData.baseTime : fileOrGraph.fileData.baseTime);
	let to = g.toDataXCoord(right)/1000 - ('file' in fileOrGraph ? fileOrGraph.file.fileData.baseTime : fileOrGraph.fileData.baseTime);

	// Get a reference to the graph instance. Dygraphs implements the click
	// callback poorly, so we have to get it in a convoluted way.
	let graph = $(event.path[2]).data('graphClassInstance');

	// Create a new annotation
	let annotation = new Annotation({
		file: globalStateManager.currentFile.filename,
		series: (Array.isArray(graph.series) ? graph.series.join(', ') : graph.series),
		begin: from,
		end: to
	}, 'new');
    file.annotations.push(annotation);

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

	// Iterate through the annotations to look for an annotation under the click
	for (let i = 0; i < file.annotations.length; i++) {
		if (e.offsetX >= file.annotations[i].offsetXLeft && e.offsetX <= file.annotations[i].offsetXRight) {
			if (
				!file.annotations[i].series ||
				file.annotations[i].state !== 'anomaly' ||
				(!graph.isGroup && file.annotations[i].series === graph.series) ||
				(graph.isGroup && graph.series.includes(file.annotations[i].series))
			) {
				file.annotations[i].showDialog();
				break;
			}
		}
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
		if (this.config['drawLine'] && e.allSeriesPoints[i+2].length > 2) {

			cnv.strokeStyle = this.config['lineColor'];
			cnv.fillStyle = this.config['lineColor'];

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
		if (this.config['drawDots']) {

			cnv.strokeStyle = this.config['dotColor'];
			cnv.fillStyle = this.config['dotColor'];

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
		cnv.strokeStyle = this.config['lineColor'];
		cnv.fillStyle = this.config['lineColor'];
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

	//globalAppConfig.verbose && console.log("handleUnderlayRedraw()");

	let file = globalStateManager.currentFile;

	let left, right, x, y, width, height;

	// console.log(canvas, area, g, Object.getOwnPropertyNames(g.setIndexByName_));

	// We need to make multiple passes to render in layers.
	// Layer 0: Anomalies detected on self graph
	// Layer 1: Anomalies detected on other graph
	// Layer 2: New & existing annotations (new annotations will naturally be rendered above existing by array order)
	for (let layer = 0; layer < 4; layer++) {

		for (let i = 0; i < file.annotations.length; i++) {

			if (
				(layer === 0 && file.annotations[i].state === 'anomaly' && file.annotations[i].series != null && !Object.getOwnPropertyNames(g.setIndexByName_).includes(file.annotations[i].series)) ||
				(layer === 1 && file.annotations[i].state === 'anomaly' && !(file.annotations[i].series != null && !Object.getOwnPropertyNames(g.setIndexByName_).includes(file.annotations[i].series))) ||
				(layer === 2 && (file.annotations[i].state === 'new' || file.annotations[i].state === 'existing'))
			) {

				// // If this annotation does not belong to this series, move on.
				// if (file.annotations[i].series != null && !Object.getOwnPropertyNames(g.setIndexByName_).includes(file.annotations[i].series)) {
				// 	continue;
				// }

				left = g.toDomXCoord(new Date((file.annotations[i].begin + file.fileData.baseTime) * 1000));
				right = g.toDomXCoord(new Date((file.annotations[i].end + file.fileData.baseTime) * 1000));

				// Prepare the parameters we'll pass into fillRect. We impose a minimum
				// of 1px width so that, at any zoom level, the annotation is visible.
				x = left;
				y = area.y;
				width = Math.max(1, right - left);
				height = area.h;

				// Prepare styling for the section highlight.
				if (file.annotations[i].state === 'anomaly') {

					if (i === file.annotationWorkflowCurrentIndex && file.annotations[i].series != null && !Object.getOwnPropertyNames(g.setIndexByName_).includes(file.annotations[i].series)) {
						// Current workflow anomaly from another series.
						canvas.fillStyle = this.config.otherCurrentWorkflowAnomalyColor;
					} else if (i === file.annotationWorkflowCurrentIndex) {
						// Current workflow anomaly that belongs to this series.
						canvas.fillStyle = this.config.ownCurrentWorkflowAnomalyColor;
					} else if (file.annotations[i].series != null && !Object.getOwnPropertyNames(g.setIndexByName_).includes(file.annotations[i].series)) {
						// Anomaly from another series.
						canvas.fillStyle = this.config.otherAnomalyColor;
					} else {
						// Anomaly that belongs to this series.
						canvas.fillStyle = this.config.ownAnomalyColor;
					}

				} else {
					// Anomaly
					canvas.fillStyle = this.config.ownAnnotationColor;
				}

				// Draw the section highlight.
				canvas.fillRect(x, y, width, height);
				file.annotations[i].offsetXLeft = x;
				file.annotations[i].offsetXRight = x + width;

				// Draw annotation label text
				if (file.annotations[i].annotation.confidence) {
					canvas.font = "12px Arial";
					//canvas.fillStyle = "#fff";
					canvas.fillStyle = this.config.ownAnnotationLabelColor;
					canvas.textAlign = "center";
					canvas.fillText(file.annotations[i].annotation.confidence, x + (width / 2), area.y + (area.h * .1));
				}

			}

		}

	}

}
