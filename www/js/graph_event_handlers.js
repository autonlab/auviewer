// Handle double-click for restoring the original zoom.
function handleDoubleClick(event, g, context) {
	g.updateOptions({
		dateWindow: globalXExtremes
	});
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
		endAnnotationHighlight(event, g, context);
	}
	else if (context.isZooming) {
		Dygraph.endZoom(event, g, context);
		updateCurrentViewData(g);
	}
	else if (context.isPanning) {
		if (context.medViewPanningMouseMoved) {
			updateCurrentViewData(g);
			context.medViewPanningMouseMoved = false;
		}
		Dygraph.endPan(event, g, context);
	}

}

// Handle shift+scroll or alt+scroll for zoom.
function handleMouseWheel(event, g, context) {

	// The event.ctrlKey is true when the user is using pinch-to-zoom gesture.
	if (event.ctrlKey || event.altKey || event.shiftKey) {

		var normal = event.detail ? event.detail * -1 : event.wheelDelta / 40;
		// For me the normalized value shows 0.075 for one click. If I took
		// that verbatim, it would be a 7.5%.
		var percentage = normal / 50;

		if (!(event.offsetX)){
			event.offsetX = event.layerX - event.target.offsetLeft;
		}

		var xPct = offsetToPercentage(g, event.offsetX);

		zoom(g, percentage, xPct);

		// If the ctrlKey is set, we are pinch-zooming. In this case, set a timeout
		// to update the current view's data. This is to prevent repeated,
		// overlapping calls in the midst of pinch-zooming. Otherwise, simply call
		// for the data update immediately.
		if (event.ctrlKey) {
			if (g.updateDataTimer != null) {
				clearTimeout(g.updateDataTimer);
			}
			g.updateDataTimer = setTimeout(function(){ g.updateDataTimer = null; updateCurrentViewData(g); }, 200);
		} else {
			updateCurrentViewData(g);
		}


		//updateCurrentViewData(g);
		event.preventDefault();

	}

}