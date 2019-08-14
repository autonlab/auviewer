// Ends an annotation highlighting action in response to a mouse-up event.
function endAnnotationHighlight (event, g, context) {

	let left = Math.min(context.dragStartX, context.dragEndX);
	let right = Math.max(context.dragStartX, context.dragEndX);
	let from = g.toDataXCoord(left);
	let to = g.toDataXCoord(right);

	// Create a new annotation
	let annotation = new Annotation(from, to);
    annotations.push(annotation);

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
	console.log('underlay');
	let left, right, x, y, width, height;

	for (let i = 0; i < annotations.length; i++) {

		left = g.toDomXCoord(new Date(annotations[i].begin));
		right = g.toDomXCoord(new Date(annotations[i].end));

        // Prepare the parameters we'll pass into fillRect. We impose a minimum
        // of 1px width so that, at any zoom level, the annotation is visible.
        x = left;
        y = area.y;
        width = Math.max(1, right - left);
        height = area.h;

        // Draw the annotation highlight.
		//canvas.fillStyle = "rgba(255, 255, 102, 1.0)";
		//canvas.fillStyle = "#4B89BF";
		//canvas.fillStyle = "#D91414";
		//canvas.fillStyle = "#768FA6";
		canvas.fillStyle = "rgba(0,72,182,0.73)";
		canvas.fillRect(x, y, width, height);

		// Draw annotation label text
		if (annotations[i].label) {
			canvas.font = "12px Arial";
			//canvas.fillStyle = "#0000e6";
			canvas.fillStyle = "#221E40";
			canvas.textAlign = "center";
			canvas.fillText(annotations[i].label, x + (width / 2), area.y + (area.h * .1));
		}

	}

}
