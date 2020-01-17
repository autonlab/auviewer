'use strict';

/*
These event handlers rely on binding to either file or graph class instance.
 */

// Handle double-click for restoring the original zoom.
function handleDoubleClick(event, g, context) {
	('file' in this ? this.file.resetZoomToOutermost() : this.resetZoomToOutermost());
}

// Handle mouse-down for pan & zoom
function handleMouseDown(event, g, context) {

	context.initializeMouseDown(event, g, context);

	if (event.altKey) {
		startAnnotationHighlight(event, g, context);
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
		moveAnnotationHighlight(event, g, context);
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
		endAnnotationHighlight(event, g, context, this);
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
		g.updateDataTimer = setTimeout(function(){ g.updateDataTimer = null; file.updateCurrentViewData(); }, 200);


		//updateCurrentViewData(g);
		event.preventDefault();

	}

}