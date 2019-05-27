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
      'dblclick': handleDoubleClick,
      'mousewheel': handleMouseWheel
    },
    labels: backendData[series].labels,
    series: {
      'Min': { plotter: downsamplePlotter },
      'Max': { plotter: downsamplePlotter }
    },
    title: series
  });

  // Attach the original dataset to the graph for later use
  dygraphInstances[series].originalDataset = backendData[series].data

}

// Converts all x values in a data array to javascript Date objects.
function convertToDateObjs(data) {

  // Go through all values in the series.
  for(var i = 0; i < data.length; i++) {

    // Convert the ISO8601-format string into a Date object.
    data[i][0] = new Date(data[i][0]);

  }
}

// Converts all x values in a data array to javascript Date objects, and also
// updates the global x-axis extremes.
function convertToDateObjsAndUpdateExtremes(data) {

  // Go through all values in the series.
  for(var i = 0; i < data.length; i++) {

    // Convert the ISO8601-format string into a Date object.
    data[i][0] = new Date(data[i][0]);

    // Update global x-minimum if warranted
    if(globalXExtremes[0] == null || data[i][0] < globalXExtremes[0]) {
      globalXExtremes[0] = data[i][0]
    }

    // Update global x-maximum if warranted
    if(globalXExtremes[1] == null || data[i][0] > globalXExtremes[1]) {
      globalXExtremes[1] = data[i][0]
    }

  }
}

// This function is a plotter that plugs into dygraphs in order to plot a down-
// sampled data series. Plotting is not documented, so the best reference for
// plotting with dygraphs is to review http://dygraphs.com/tests/plotters.html
// and its source code.
function downsamplePlotter(e) {

  // We only want to run the plotter for the first series.
  if (e.seriesIndex !== 1) return;

  // We require two series for min & max.
  if (e.seriesCount != 3) {
    throw "The medview plotter expects three y-values per series for downsample min, downsample max, and real value.";
  }

  // This is a reference to a proxy for the canvas element of the graph
  var cnv = e.drawingContext;

  // Holds positioning & dimensions (x, y, w, h) of the plot area, needed for
  // plotting points.
  var area = e.plotArea;

  // Line properties
  cnv.strokeStyle = '#5253FF';
  cnv.fillStyle = '#5253FF';
  cnv.lineWidth = 1;

  // Plot all data points
  for (var i = 0; i < e.allSeriesPoints[0].length; i++) {

    // There may be intervals wherein min==max, and to handle these, we must use a different drawing method.
    if (e.allSeriesPoints[0][i].y == e.allSeriesPoints[1][i].y) {

      cnv.fillRect(e.allSeriesPoints[0][i].x * area.w + area.x, e.allSeriesPoints[0][i].y * area.h + area.y, 1, 1)

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

// Produces a meshed dataset consisting of the outerDataset and innerDataset,
// with  innerDataset replacing its time range of data points in outerDataset.
function getDownsampleMesh(outerDataset, innerDataset) {
  
  // We expect non-empty arrays
  if (outerDataset.length < 1 || innerDataset.length < 1) {
    return;
  }

  // Will hold the relevant places to slice the outerDataset.
  var sliceIndexFirstSegment = 0;
  var sliceIndexSecondSegment = 0;

  // Determine outerDataset index of the data point just after innerDataset
  // starts. We will find the index just *after* the last data point before
  // innerDataset starts. However, that's okay, because sliceIndexFirstSegment
  // will be the second parameter in a slice call, which indicates an element
  // that will not be included in the resulting array.
  while (sliceIndexFirstSegment < outerDataset.length && outerDataset[sliceIndexFirstSegment][0].getTime() < innerDataset[0][0].getTime()) {
    sliceIndexFirstSegment++;
  }

  // Determine outerDataset index of the data point just after innerDataset ends.
  sliceIndexSecondSegment = sliceIndexFirstSegment;
  while (sliceIndexSecondSegment < outerDataset.length && outerDataset[sliceIndexSecondSegment][0].getTime() <= innerDataset[innerDataset.length-1][0].getTime()) {
    sliceIndexSecondSegment++;
  }

  // Return the joined dataset with the innerDataset replacing the relevant
  // section of outerDataset.
  return outerDataset.slice(0, sliceIndexFirstSegment).concat(innerDataset, outerDataset.slice(sliceIndexSecondSegment));

}

// Handle double-click for restoring the original zoom.
function handleDoubleClick(event, g, context) {
  g.updateOptions({
    dateWindow: globalXExtremes,
    file: g.originalDataset
  });
}

// Handle mouse-down for pan & zoom
function handleMouseDown(event, g, context) {
  context.initializeMouseDown(event, g, context);
  if (event.altKey || event.shiftKey) {
    Dygraph.startZoom(event, g, context);
  } else {
    context.medViewPanningMouseMoved = false;
    Dygraph.startPan(event, g, context);
  }
}

// Handle mouse-move for pan & zoom.
function handleMouseMove(event, g, context) {
  if (context.isPanning) {
    context.medViewPanningMouseMoved = true;
    Dygraph.movePan(event, g, context);
  } else if (context.isZooming) {
    Dygraph.moveZoom(event, g, context);
  }
}

// Handle mouse-up for pan & zoom.
function handleMouseUp(event, g, context) {
  if (context.isPanning) {
    if (context.medViewPanningMouseMoved) {
      updateCurrentViewData(g);
      context.medViewPanningMouseMoved = false;
    }
    Dygraph.endPan(event, g, context);
  } else if (context.isZooming) {
    Dygraph.endZoom(event, g, context);
    updateCurrentViewData(g);
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

// Will request and update the current view of the graph with new data that is
// appropriately downsampled (or not).
function updateCurrentViewData(graph) {

  // Get the x-axis range
  var xRange = graph.xAxisRange();

  console.log("Requesting data for view.");

  // Setup our async http call.
  var x = new XMLHttpRequest();

  // Setup our callback handler.
  x.onreadystatechange = function() {

    if (this.readyState == 4 && this.status == 200) {

      console.log("Applying data to view.");

      // Parse the backend JSON response into a JS object
      var backendData = JSON.parse(x.responseText);

      console.log(backendData);

      // Process the new data for each series.
      for(series in backendData) {

        // Convert date strings to Date objects in all datasets.
        convertToDateObjs(backendData[series]['data']);

        var meshedData = getDownsampleMesh(dygraphInstances[series].originalDataset, backendData[series]['data']);

        console.log(meshedData);

        // Update the graph data, and redraw
        dygraphInstances[series].updateOptions({
          file: meshedData
        });

      }

    }

  }

  // Send the async request
  x.open("GET", "http://localhost:8003?start="+xRange[0]+"&stop="+xRange[1], true);
  x.send();

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
      convertToDateObjsAndUpdateExtremes(backendData[series]['data']);
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

    // Synchronize all of the graphs, if there are more than one.
    if (Object.keys(dygraphInstances).length > 1) {
      var sync = Dygraph.synchronize(Object.values(dygraphInstances), {
        range: false,
        selection: true,
        zoom: true
      });
    }

  }

};

xhttp.open("GET", "http://localhost:8003", true);
xhttp.send();
