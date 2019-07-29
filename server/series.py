import bisect
import numpy as np
from rawdata import RawData
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
    def __init__(self, name, h5path, fileparent):

        # Holds the ordered (hierarchical) list of groups and, ultimately,
        # dataset to which the series belongs. So, this is like a folder path,
        # where the first element is the outermost group name and the last
        # element is the dataset name of the series.
        self.h5path = h5path

        # Holds the series name
        self.name = name

        # Holds a reference to the file parent which contains the series
        self.fileparent = fileparent
        
        # Initialize raw data to None
        self.rawTimeOffsets = None
        self.rawValues = None

        # # Pull raw data for the series into memory
        # self.pullRawDataIntoMemory()
        
        # Holds the raw data set
        self.rd = RawData(self)

        # Holds the downsample set
        self.dss = DownsampleSet(self)
        
    def generateThresholdAlerts(self, threshold, duration, dutycycle, maxgap):
        
        # Pull raw data for the series into memory
        self.pullRawDataIntoMemory()
        
        # Run through the data and generate alerts
        alerts = generateThresholdAlerts(self.rawTimeOffsets, self.rawValues, threshold, duration, dutycycle, maxgap)

        # Remove raw data for the series fromm memory
        self.removeRawDataFromMemory()
        
        return alerts

    # Produces JSON output for the series at the maximum time range.
    def getFullOutput(self):
    
        print("Assembling full output for " + self.name + ".")
    
        # Attempt to retrieve the full downsample output
        downsampleFullOutput = self.dss.getFullOutput()
    
        # Set data either to the retrieved downsample or to the raw data
        if downsampleFullOutput is not None:
            data = downsampleFullOutput.tolist()
        else:
            # nones = [None] * len(self.rawTimeOffsets)
            # data = [list(i) for i in zip(self.rawTimeOffsets, nones, nones, self.rawValues)]

            # Get reference to the series datastream from the HDF5 file
            dataset = self.fileparent.f.get('/'.join(self.h5path))
            
            nones = [None] * self.rd.len
            data = [list(i) for i in zip(dataset['time'][()], nones, nones, dataset['value'].astype(np.float64)[()])]
        
        # Return the JSON-ready output object
        return {
            "labels": ['Date/Offset', 'Min', 'Max', self.name],
            "data": data
        }

    # Produces JSON output for the series over a specified time range, with
    # starttime and stoptime being time offset floats in seconds.
    def getRangedOutput(self, starttime, stoptime):

        # Get the appropriate downsample for this time range
        ds = self.dss.getRangedOutput(starttime, stoptime)

        if isinstance(ds, np.ndarray):

            print("Assembling ranged downsampled data for " + self.name + ".")
            
            data = ds.tolist()

            print("Assembly complete for " + self.name + ".")

        else:

            print("Assembling ranged raw data for " + self.name + ".")

            data = self.rd.getRangedOutput(starttime, stoptime)

            print("Assembly complete for " + self.name + ".")

        # Return the JSON-ready output object
        return {
            "labels": ['Date/Offset', 'Min', 'Max', self.name],
            "data": data
        }

    # Process and store all downsamples for the series.
    def processAndStore(self):
        
        print("Processing & storing all downsamples for the series " + self.name)
        start = time.time()

        # Pull raw data for the series into memory
        self.pullRawDataIntoMemory()

        # Build & store to file all downsamples for the series
        self.dss.processAndStore()
        
        # Remove raw data for the series fromm memory
        self.removeRawDataFromMemory()

        end = time.time()
        print("Completed processing & storing all downsamples for the series " + self.name + ". Took " + str(round((end - start) / 60, 3)) + " minutes.")

    # Pulls the raw data for the series from the file into memory (self.rawTimeOffsets
    # and self.rawValues).
    def pullRawDataIntoMemory(self):

        print("Reading raw series data into memory for " + self.name + ".")
        start = time.time()

        # Get reference to the series datastream from the HDF5 file
        dataset = self.fileparent.f.get('/'.join(self.h5path))[()]

        self.rawTimeOffsets = dataset['time']
        self.rawValues = dataset['value'].astype(np.float64)

        end = time.time()
        print("Finished reading raw series data into memory for " + self.name + " (" + str(self.rawTimeOffsets.shape[0]) + " points). Took " + str(round(end - start, 5)) + "s.")
        
    def removeRawDataFromMemory(self):
    
        # Initialize raw data to None
        self.rawTimeOffsets = None
        self.rawValues = None
