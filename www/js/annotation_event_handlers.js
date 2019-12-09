'use strict';

let useRandomAnomalyColors = false;
let seriesAnomalyColors = {};

// The click callback handler displays the annotation input form if the user
// clicks on an annotation. If multiple annotations are under the mouse-click,
// the first input form is displayed for the first annotation found.
function clickCallbackHandler(e, x) {

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
				(!graph.isGroup && file.annotations[i].series === graph.series) ||
				(graph.isGroup && graph.series.includes(file.annotations[i].series))
			) {
				file.annotations[i].showDialog();
				break;
			}
		}
	}

}

// Ends an annotation highlighting action in response to a mouse-up event.
function endAnnotationHighlight (event, g, context, fileOrGraph) {

	let file = globalStateManager.currentFile;

	let left = Math.min(context.dragStartX, context.dragEndX);
	let right = Math.max(context.dragStartX, context.dragEndX);
	let from = g.toDataXCoord(left)/1000 - ('file' in fileOrGraph ? fileOrGraph.file.fileData.baseTime : fileOrGraph.fileData.baseTime);
	let to = g.toDataXCoord(right)/1000 - ('file' in fileOrGraph ? fileOrGraph.file.fileData.baseTime : fileOrGraph.fileData.baseTime);

	// Create a new annotation
	let annotation = new Annotation({
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
function moveAnnotationHighlight (event, g, context) {

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
function startAnnotationHighlight (event, g, context) {

    // Mark in our context that the user has begun drawing an annotation segment.
	context.mvIsAnnotating = true;

	// The user's mouse has not moved yet after starting an annotation draw.
	context.mvAnnotatingMoved = false;

}

// This is the callback function provided to dygraphs which draws the
// annotations on the canvas.
function underlayCallbackHandler(canvas, area, g) {

	let file = globalStateManager.currentFile;

	let left, right, x, y, width, height;

	// console.log(canvas);
	// console.log(area);
	// console.log(g);
	// console.log(Object.getOwnPropertyNames(g.setIndexByName_));

	// We need to make multiple passes to render in layers.
	// Layer 0: Anomalies detected on self graph
	// Layer 1: Anomalies detected on other graph
	// Layer 2: New & existing annotations (new annotations will naturally be rendered above existing by array order)
	for (let layer = 0; layer < 4; layer++) {

		for (let i = 0; i < file.annotations.length; i++) {

			if (
				(layer == 0 && file.annotations[i].state == 'anomaly' && file.annotations[i].series != null && !Object.getOwnPropertyNames(g.setIndexByName_).includes(file.annotations[i].series)) ||
				(layer == 1 && file.annotations[i].state == 'anomaly' && !(file.annotations[i].series != null && !Object.getOwnPropertyNames(g.setIndexByName_).includes(file.annotations[i].series))) ||
				(layer == 2 && (file.annotations[i].state == 'new' || file.annotations[i].state == 'existing'))
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

				// Draw the annotation highlight.
				if (file.annotations[i].state === 'anomaly') {
					if (useRandomAnomalyColors) {
						if (!seriesAnomalyColors.hasOwnProperty(file.annotations[i].series)) {
							seriesAnomalyColors[file.annotations[i].series] = randomColor();
							console.log(file.annotations[i].series, seriesAnomalyColors[file.annotations[i].series]);
						}
						canvas.fillStyle = seriesAnomalyColors[file.annotations[i].series];
					} else {
						if (file.annotations[i].series != null && !Object.getOwnPropertyNames(g.setIndexByName_).includes(file.annotations[i].series)) {
							// Use a lighter color to highlight anomalies from
							// other series.
							canvas.fillStyle = '#f5d4ab';
						} else {
							// If the anomaly belongs to this series, use a
							// the darker orange.
							canvas.fillStyle = '#f7a438';
						}
					}
				} else {
					canvas.fillStyle = "rgba(0,72,182,0.73)";
				}
				canvas.fillRect(x, y, width, height);
				file.annotations[i].offsetXLeft = x;
				file.annotations[i].offsetXRight = x + width;

				// Draw annotation label text
				if (file.annotations[i].annotation.confidence) {
					canvas.font = "12px Arial";
					canvas.fillStyle = "#fff";
					canvas.textAlign = "center";
					canvas.fillText(file.annotations[i].annotation.confidence, x + (width / 2), area.y + (area.h * .1));
				}

			}

		}

	}

}
