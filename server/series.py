import bisect
# import datetime as dt
from downsamples import Downsamples

# Simplejson package is required in order to "ignore" NaN values and implicitly convert them into null values.
# RFC JSON spec left out NaN values, even though ES5 supports them (https://www.ecma-international.org/ecma-262/5.1/#sec-4.3.23).
# By default, Python "json" module will allow & json-encode NaN values, but the Chrome JS engine will throw an error when trying to parse them.
# Simplejson package, with ignore_nan=True, will implicitly convert NaN values into null values.
# Find "ignore_nan" here: https://simplejson.readthedocs.io/en/latest/
import simplejson as json

# Represents a single time series of data.
class Series:

    # Reads a series into memory and builds the downsampling. Type is either
    # 'numeric' or 'waveform'. Fileparent is a reference to the File class
    # instance which contains the Series.
    def __init__(self, type, name, fileparent):

        # Holds the type
        self.type = type

        # Holds the series name
        self.name = name

        # Holds a reference to the file parent which contains the series
        self.fileparent = fileparent

        # Pull raw data into memory
        self.pullRawData()

        # Holds the downsample set
        self.downsamples = Downsamples(self)

    # Returns a reference to the series' h5py dataset object.
    def getData(self):

        return self.fileparent.f[self.type][self.name]['data']

    # Produces JSON output for the series at the maximum time range.
    def getFullOutputAllSeries(self):

        # # Will hold the data points ready for output
        # data = []
        #
        # # Assemble the data points
        # for i in self.downsampleSet.downsamples[0].intervals:
        #     data.append([i.time.isoformat(), i.min, i.max, None])

        # Assemble the output data
        data = [[i.time, i.min, i.max, None] for i in self.downsampleSet.downsamples[0].intervals]

        return {
            "labels": ['Date/Offset', 'Min', 'Max', self.name],
            "data": data
        }

    # Produces JSON output for the series over a specified time range, with
    # starttime and stoptime being time offset floats in seconds.
    def getRangedOutput(self, starttime, stoptime):

        # Get the appropriate downsample for this time range
        ds = self.downsampleSet.getDownsample(starttime, stoptime)

        if ds:

            print("Assembling downsampled data for " + self.name + ".")

            # Get the intervals within this time range
            intervals = ds.getIntervals(starttime, stoptime)

            # # Will hold the data points ready for output
            # data = []
            #
            # # Assemble the data points
            # for i in intervals:
            #     data.append([i.time.isoformat(), i.min, i.max, None])

            # Assemble the output data
            data = [[i.time, i.min, i.max, None] for i in intervals]

            return {
                "labels": ['Date/Offset', 'Min', 'Max', self.name],
                "data": data
            }

        else:

            print("Assembling raw data for " + self.name + ".")

            # Determine the index of the first point to transmit for the view.
            # To do this, find the first point which occurs after the starttime
            # and take the index prior to that as the starting data point.
            startPointIndex = bisect.bisect(self.rawTimeOffsets, starttime) - 1
            if startPointIndex < 0:
                startPointIndex = 0

            print("Calculated start index at: " + str(startPointIndex))

            # Determine the index of the last point to transmit for the view. To
            # To do this, find the first interval which occurs after the stoptime
            # and take the index prior to that as the starting data point.
            stopPointIndex = bisect.bisect(self.rawTimeOffsets, stoptime) - 1
            if stopPointIndex < 0:
                stopPointIndex = 0

            print("Calculated start index at: " + str(stopPointIndex))

            # Will hold the data points ready for output
            # data = []

            # Assemble the data points
            # i = startPointIndex
            # while i <= stopPointIndex:
            #     data.append([self.rawTimeOffsets[i], None, None, self.rawValues[i]])
            #     i = i + 1

            # Assemble the output data
            # TODO(gus): Try to get this from the file instead of relying on it being in memory.
            nones = [None]*(stopPointIndex-startPointIndex)
            tuples = zip(self.rawTimeOffsets[startPointIndex:(stopPointIndex+1)], nones, nones, self.rawValues[startPointIndex:(stopPointIndex+1)])
            data = [list(i) for i in tuples]

            print("Assembly complete for " + self.name + ".")

            return {
                "labels": ['Date/Offset', 'Min', 'Max', self.name],
                "data": data
            }

    # Pulls the raw data for the series from the file into memory (self.rawTimeOffsets
    # and self.rawValues).
    def pullRawData(self):

        print("Reading raw series data into memory for " + self.name + ".")

        # Get reference to the series datastream from the HDF5 file
        data = self.getData()

        self.rawTimeOffsets = data['datetime'][()]
        self.rawValues = data['value'][()]

        print("Finished reading raw series data into memory for " + self.name + " (" + str(self.rawTimeOffsets.shape[0]) + " points).")
