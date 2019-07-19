import bisect
import numpy as np
from downsampleset import DownsampleSet
from cylib import generateThresholdAlerts
import time

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
        self.dss = DownsampleSet(self)
        
    def generateThresholdAlerts(self, threshold, duration, dutycycle, maxgap):
        # return generateThresholdAlerts(self.rawTimeOffsets, self.rawValues, 90, 300, .7, 60)
        return generateThresholdAlerts(self.rawTimeOffsets, self.rawValues, threshold, duration, dutycycle, maxgap)

    # Produces JSON output for the series at the maximum time range.
    def getFullOutputAllSeries(self):

        # Assemble the output data, either downsampled data, if available, or
        # raw data, if not.
        if len(self.dss.downsamples) > 0:
            
            print("Assembling full downsampled data for " + self.name + ".")
            
            data = self.dss.downsamples[0].tolist()

            print("Assembly complete for " + self.name + ".")
            
        else:
    
            print("Assembling full raw data for " + self.name + ".")
            
            nones = [None] * len(self.rawTimeOffsets)
            data = [list(i) for i in zip(self.rawTimeOffsets, nones, nones, self.rawValues)]

            print("Assembly complete for " + self.name + ".")
        
        return {
            "labels": ['Date/Offset', 'Min', 'Max', self.name],
            "data": data
        }

    # Produces JSON output for the series over a specified time range, with
    # starttime and stoptime being time offset floats in seconds.
    def getRangedOutput(self, starttime, stoptime):

        # Get the appropriate downsample for this time range
        ds = self.dss.getDownsample(starttime, stoptime)

        if isinstance(ds, np.ndarray):

            print("Assembling ranged downsampled data for " + self.name + ".")
            
            data = ds.tolist()

            print("Assembly complete for " + self.name + ".")

        else:

            print("Assembling ranged raw data for " + self.name + ".")

            # Find the start & stop indices based on the start & stop times.
            startIndex = np.searchsorted(self.rawTimeOffsets, starttime)
            stopIndex = np.searchsorted(self.rawTimeOffsets, stoptime, side='right')

            # Assemble the output data
            nones = [None] * (stopIndex - startIndex)
            data = [list(i) for i in zip(self.rawTimeOffsets[startIndex:stopIndex], nones, nones, self.rawValues[startIndex:stopIndex])]

            print("Assembly complete for " + self.name + ".")

        return {
            "labels": ['Date/Offset', 'Min', 'Max', self.name],
            "data": data
        }

    # Pulls the raw data for the series from the file into memory (self.rawTimeOffsets
    # and self.rawValues).
    def pullRawData(self):

        print("Reading raw series data into memory for " + self.name + ".")

        start = time.time()

        # Get reference to the series datastream from the HDF5 file
        data = self.fileparent.f[self.type][self.name]['data']

        self.rawTimeOffsets = data['time']
        self.rawValues = data['value'].astype(np.float64)

        end = time.time()

        print("Finished reading raw series data into memory for " + self.name + " (" + str(self.rawTimeOffsets.shape[0]) + " points). Took " + str(round(end - start, 5)) + "s.")
