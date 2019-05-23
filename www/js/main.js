// Holds the dom elements of instantiated graphs, keyed by series name
var graphDomElements = {};

// Holds the instantiated dygraphs, keyed by series name
var dygraphInstances = {};

/*
This will be a 2-dimensional array that holds the min ([0]) and max ([1])
x-value across all graphs currently displayed. This is calculated in the
convertToDateObjsAndUpdateExtremes() function. The values should hold
milliseconds since epoch, as this is the format specified for
options.dateWindow, though the values will intermediately be instances of the
Date object while the extremes are being calculated. This array may be
passed into the options.dateWindow parameter for a dygraph.
*/
var globalXExtremes = [];

var xhttp = new XMLHttpRequest();

// Creates a dygraph and adds it to the DOM
function addGraph(backendData, series) {

  // Create the dom element
  el = document.createElement("DIV");

  // Add the dom element to the global collection for later reference
  graphDomElements[series] = el;

  // Set element to graph css class
  el.className = "graph";

  // Attach new graph div to the DOM
  document.getElementById('graphs').appendChild(el);

  // Create the dygraph
  dygraphInstances[series] = new Dygraph(el, backendData[series].data, {
    colors: ['#5253FF'],
    dateWindow: globalXExtremes,
    interactionModel: {
      'mousedown': handleMouseDown,
      'mousemove': handleMouseMove,
      'mouseup': handleMouseUp,
      'dblclick': handleDoubleClick/*,
      'mousewheel': handleMouseWheel*/
    },
    labels: backendData[series].labels,
    plotter: downsamplePlotter,
    title: series
  });

}

// Convert all x values in a series to javascript Date objects, and also update
// the global x-axis extremes.
function convertToDateObjsAndUpdateExtremes(backendData, series) {

  // Go through all values in the series.
  for(var i = 0; i < backendData[series]['data'].length; i++) {

    // Convert the ISO8601-format string into a Date object.
    backendData[series]['data'][i][0] = new Date(backendData[series]['data'][i][0]);

    // Update global x-minimum if warranted
    if(globalXExtremes[0] == null || backendData[series]['data'][i][0] < globalXExtremes[0]) {
      globalXExtremes[0] = backendData[series]['data'][i][0]
    }

    // Update global x-maximum if warranted
    if(globalXExtremes[1] == null || backendData[series]['data'][i][0] > globalXExtremes[1]) {
      globalXExtremes[1] = backendData[series]['data'][i][0]
    }

  }
}

// This function is a plotter that plugs into dygraphs in order to plot a down-
// sampled data series. Plotting is not documented, so the best reference for
// plotting with dygraphs is to review http://dygraphs.com/tests/plotters.html
// and its source code.
function downsamplePlotter(e) {

  // This is the official dygraphs way to plot all the series at once, per
  // source code of dygraphs.com/tests/plotters.html.
  if (e.seriesIndex !== 0) return;

  // We require two series for min & max.
  if (e.seriesCount != 2) {
    throw "Downsampled plots require two values per point, min & max.";
  }

  // This is a reference to a proxy for the canvas element of the graph
  var cnv = e.drawingContext;

  // Holds positioning & dimensions (x, y, w, h) of the plot area, needed for
  // plotting points.
  var area = e.plotArea;

  // Line properties
  cnv.strokeStyle = '#5253FF';
  cnv.lineWidth = 0.6;

  // Plot all data points
  for (var i = 0; i < e.allSeriesPoints[0].length; i++) {

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

// Handle double-click for restoring the original zoom.
function handleDoubleClick(event, g, context) {
  g.updateOptions({
    dateWindow: globalXExtremes
  });
}

// Handle mouse-down for pan & zoom
function handleMouseDown(event, g, context) {
  context.initializeMouseDown(event, g, context);
  if (event.altKey || event.shiftKey) {
    Dygraph.startZoom(event, g, context);
  } else {
    Dygraph.startPan(event, g, context);
  }
}

// Handle mouse-move for pan & zoom.
function handleMouseMove(event, g, context) {
  if (context.isPanning) {
    Dygraph.movePan(event, g, context);
  } else if (context.isZooming) {
    Dygraph.moveZoom(event, g, context);
  }
}

// Handle mouse-up for pan & zoom.
function handleMouseUp(event, g, context) {
  if (context.isPanning) {
    Dygraph.endPan(event, g, context);
  } else if (context.isZooming) {
    Dygraph.endZoom(event, g, context);
  }
}

// Handle shift+scroll or alt+scroll for zoom.
/*function handleMouseWheel(event, g, context) {

  if (event.altKey || event.shiftKey) {

    var normal = event.detail ? event.detail * -1 : event.wheelDelta / 40;
    // For me the normalized value shows 0.075 for one click. If I took
    // that verbatim, it would be a 7.5%.
    var percentage = normal / 50;

    if (!(event.offsetX)){
      event.offsetX = event.layerX - event.target.offsetLeft;
    }

    var xPct = offsetToPercentage(g, event.offsetX);

    zoom(g, percentage, xPct);
    event.preventDefault();

  }

}*/

// Take the offset of a mouse event on the dygraph canvas and
// convert it to a percentages from the left.
function offsetToPercentage(g, offsetX) {
  // This is calculating the pixel offset of the leftmost date.
  var xOffset = g.toDomCoords(g.xAxisRange()[0], null)[0];

  // x y w and h are relative to the corner of the drawing area,
  // so that the upper corner of the drawing area is (0, 0).
  var x = offsetX - xOffset;

  // This is computing the rightmost pixel, effectively defining the width.
  var w = g.toDomCoords(g.xAxisRange()[1], null)[0] - xOffset;

  // Percentage from the left.
  var xPct = w === 0 ? 0 : (x / w);

  // The (1-) part below changes it from "% distance down from the top"
  // to "% distance up from the bottom".
  return xPct;
}

// Adjusts x inward by zoomInPercentage%
// Split it so the left axis gets xBias of that change and
// right gets (1-xBias) of that change.
//
// If a bias is missing it splits it down the middle.
function zoom(g, zoomInPercentage, xBias) {
  xBias = xBias || 0.5;
  function adjustAxis(axis, zoomInPercentage, bias) {
    var delta = axis[1] - axis[0];
    var increment = delta * zoomInPercentage;
    var foo = [increment * bias, increment * (1-bias)];
    return [ axis[0] + foo[0], axis[1] - foo[1] ];
  }

  g.updateOptions({
    dateWindow: adjustAxis(g.xAxisRange(), zoomInPercentage, xBias)
  });
}

xhttp.onreadystatechange = function() {
  if (this.readyState == 4 && this.status == 200) {

    // Parse the backend JSON response into a JS object
    var backendData = JSON.parse(xhttp.responseText);
    console.log(backendData);

    // Convert date strings to Date objects in all datasets and produce global
    // x-axis extremes. It is an obvious potential optimization to combine this
    // for loop and the subsequent one, but don't. Global x-axis extremes from
    // all datasets must be calculated before any graph is plotted so that the
    // default zoom can be set. There won't be that many graphs, so redundant
    // for loops are not costly.
    for(series in backendData) {
      convertToDateObjsAndUpdateExtremes(backendData, series);
    }

    // When the x-axis extremes have been calculated (as dates), convert them
    // to milliseconds since epoch, as this is what is specified in the options
    // reference: http://dygraphs.com/options.html#dateWindow
    globalXExtremes[0] = globalXExtremes[0].valueOf();
    globalXExtremes[1] = globalXExtremes[1].valueOf();

    // Create a graph for each series
    for(series in backendData) {
      addGraph(backendData, series);
    }

    // Synchronize all of the graphs
    /*var sync = Dygraph.synchronize(Object.values(dygraphInstances), {
      range: false,
      selection: true,
      zoom: true
    });*/

  }
};

xhttp.open("GET", "http://localhost:8003", true);
xhttp.send();
