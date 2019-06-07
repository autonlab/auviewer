var annotations = [];

function Annotation(begin, end) {

    this.begin = begin || 0;
    this.end = end || 0;

}

//Annotation.prototype

function underlayCallbackHandler(canvas, area, g) {

	var bottom_left, top_right, left, right;
	console.log("Underlay starting");
	console.log(annotations);
	for (var i = 0; i < annotations.length; i++) {

		left = g.toDomXCoord(new Date(annotations[i].begin));
		right = g.toDomXCoord(new Date(annotations[i].end));
console.log(left, area.y, right, left, area.h);
		canvas.fillStyle = "rgba(255, 255, 102, 1.0)";
		canvas.fillRect(left, area.y, right - left, area.h);

	}

}

/* On-graph annotation event handlers. */

// Begins an annotation highlighting action in response to a mouse-down event.
function startAnnotationHighlight (event, g, context) {

    // Mark in our context that the user has begun drawing an annotation segment.
	context.mvIsAnnotating = true;

	// The user's mouse has not moved yet after starting an annotation draw.
	context.mvAnnotatingMoved = false;

}

// Adjusts the annotation highlight in response to a mouse-move event.
function moveAnnotationHighlight (event, g, context) {

    // The user's mouse has now moved since starting an annotation draw.
	context.mvAnnotatingMoved = true;

	// context.dragEndX = utils.dragGetX_(event, context);
	// context.dragEndY = utils.dragGetY_(event, context);
	context.dragEndX = Dygraph.pageX(event) - context.px;
	context.dragEndY = Dygraph.pageY(event) - context.py;

	var xDelta = Math.abs(context.dragStartX - context.dragEndX);
	var yDelta = Math.abs(context.dragStartY - context.dragEndY);

	// drag direction threshold for y axis is twice as large as x axis
	//context.dragDirection = xDelta < yDelta / 2 ? utils.VERTICAL : utils.HORIZONTAL;
	context.dragDirection = xDelta < yDelta / 2 ? 2 : 1;

	g.drawZoomRect_(context.dragDirection, context.dragStartX, context.dragEndX, context.dragStartY, context.dragEndY, context.prevDragDirection, context.prevEndX, context.prevEndY);

	context.prevEndX = context.dragEndX;
	context.prevEndY = context.dragEndY;
	context.prevDragDirection = context.dragDirection;
}

// Ends an annotation highlighting action in response to a mouse-up event.
function endAnnotationHighlight (event, g, context) {
	console.log(context);

	var left = Math.min(context.dragStartX, context.dragEndX);
	var right = Math.max(context.dragStartX, context.dragEndX);
	var from = g.toDataXCoord(left);
	var to = g.toDataXCoord(right);

	// Create a new annotation
	annotations.push(new Annotation(from, to));
	console.log(annotations);

	g.clearZoomRect_();
	context.mvIsAnnotating = false;
	context.mvAnnotatingMoved = false;
	//DygraphInteraction.maybeTreatMouseOpAsClick(event, g, context);

	// The zoom rectangle is visibly clipped to the plot area, so its behavior
	// should be as well.
	// See http://code.google.com/p/dygraphs/issues/detail?id=280
	// var plotArea = g.getArea();
	// if (context.regionWidth >= 10 && context.dragDirection == utils.HORIZONTAL) {
	//   var left = Math.min(context.dragStartX, context.dragEndX),
	//       right = Math.max(context.dragStartX, context.dragEndX);
	//   left = Math.max(left, plotArea.x);
	//   right = Math.min(right, plotArea.x + plotArea.w);
	//   if (left < right) {
	//     g.doZoomX_(left, right);
	//   }
	//   context.cancelNextDblclick = true;
	// } else if (context.regionHeight >= 10 && context.dragDirection == utils.VERTICAL) {
	//   var top = Math.min(context.dragStartY, context.dragEndY),
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