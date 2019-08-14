'use strict';

let requestHandler = new RequestHandler();
let globalStateManager = new GlobalStateManager();











// This function is a plotter that plugs into dygraphs in order to plot a down-
// sampled data series. Plotting is not documented, so the best reference for
// plotting with dygraphs is to review http://dygraphs.com/tests/plotters.html
// and its source code.
function downsamplePlotter(e) {

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
	cnv.strokeStyle = '#171717';//'#5253FF';
	cnv.fillStyle = '#171717';//'#5253FF';
	cnv.lineWidth = 1;

	// Plot all raw value data points
	for (let i = 0; i < e.allSeriesPoints[2].length; i++) {

		//cnv.fillRect(e.allSeriesPoints[2][i].x * area.w + area.x, e.allSeriesPoints[2][i].y * area.h + area.y, 2, 2)
		cnv.beginPath();
		cnv.arc(e.allSeriesPoints[2][i].x * area.w + area.x, e.allSeriesPoints[2][i].y * area.h + area.y, 1, 0, 2*Math.PI);
		cnv.fill();

	}

	// Plot all downsample intervals
	for (let i = 0; i < e.allSeriesPoints[0].length; i++) {

		// There may be intervals wherein min==max, and to handle these, we must use a different drawing method.
		if (e.allSeriesPoints[0][i].y == e.allSeriesPoints[1][i].y) {

			cnv.fillRect(e.allSeriesPoints[0][i].x * area.w + area.x, e.allSeriesPoints[0][i].y * area.h + area.y, 1, 1)
			/*cnv.beginPath();
			cnv.arc(e.allSeriesPoints[0][i].x * area.w + area.x, e.allSeriesPoints[0][i].y * area.h + area.y, 2, 0, 2*Math.PI);
			cnv.fill();*/

		} else {

			// Begin a path (this instantiates a path object but does not draw it
			cnv.beginPath();

			// Start stroke at the min value
			cnv.moveTo(e.allSeriesPoints[0][i].x * area.w + area.x, e.allSeriesPoints[0][i].y * area.h + area.y);

			// End stroke at the max value
			cnv.lineTo(e.allSeriesPoints[1][i].x * area.w + area.x, e.allSeriesPoints[1][i].y * area.h + area.y);

			// Draw the line on the canvas
			cnv.stroke();

		}

	}

}
