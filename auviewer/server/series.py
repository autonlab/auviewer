from collections import deque
import numpy as np
import pandas as pd
import time
import psutil
from threading import Lock
from copy import copy

from . import config
from .rawdata import RawData
from .downsampleset import DownsampleSet
from .cylib import generateThresholdAlerts

# Represents a single time series of data.
class Series:

    # Reads a series into memory and builds the downsampling. Fileparent is a reference
    # to the File class instance which contains the Series.
    def __init__(self, ds, timecol, valcol, fileparent):

        # The series ID is the dataset path in the HDF5 file
        self.id = f'{ds.name}:{valcol}'

        # Holds the ordered (hierarchical) list of groups and, ultimately,
        # dataset to which the series belongs. So, this is like a folder path,
        # where the first element is the outermost group name and the last
        # element is the dataset name of the series.
        self.h5path = [e for e in ds.name.split('/') if len(e) > 0]

        # Holds the ordered (hierarchical) list of groups where downsamples will
        # be stored in the processed file.
        self.h5pathDownsample = copy(self.h5path)
        self.h5pathDownsample.append(valcol)

        # Holds the time & value column names in the HDF dataset
        self.timecol = timecol
        self.valcol = valcol

        # Holds a reference to the file parent which contains the series
        self.fileparent = fileparent

        # Initialize raw data in memory
        self.initializeRawDataInMemory()

        # # Pull raw data for the series into memory
        # self.pullRawDataIntoMemory()

        if self.fileparent.mode() == 'file':

            # Holds the raw data set
            self.rd = RawData(self)

            # Holds the downsample set
            self.dss = DownsampleSet(self)

        elif self.fileparent.mode() == 'realtime':

            self.dequeLock = Lock()

    # Add data to the series (e.g. for realtime). The data is assumed to occur
    # after any existing data. The data parameter should be a dict of lists as
    # follows:
    #
    #   {
    #     'times': [ t1, t2, ... , tn ],
    #     'values': [ v1, v2, ... , vn ]
    #   }
    def addData(self, data):

        # ATW: TODO: Reimplement.
        raise Exception('Data appending is currently unsupported.')

        if not isinstance(data, dict) or not isinstance(data['times'], list) or not isinstance(data['values'], list):
            print('HERE', type(data), type(data['times']), type(data['values']), data)
            raise Exception('Invalid seriesData parameter received for series.addData().')

        # Add the new times & values.
        # TODO(gus): Once connected, check whether this is most efficient way to
        # join lists.
        # self.rawTimes = self.rawTimes + data['times']
        # self.rawValues = self.rawValues + data['values']
        with self.dequeLock:
            self.rawTimes.extend(data['times'])
            self.rawValues.extend(data['values'])

        return

    def generateThresholdAlerts(self, thresholdlow, thresholdhigh, mode, duration, persistence, maxgap):

        # Pull raw data for the series into memory
        self.pullRawDataIntoMemory()

        # Run through the data and generate alerts
        alerts = generateThresholdAlerts(self.rawTimes, self.rawValues, thresholdlow, thresholdhigh, mode, duration, persistence, maxgap)

        # Remove raw data for the series fromm memory
        self.initializeRawDataInMemory()

        return alerts

    # Produces JSON output for the series at the maximum time range.
    def getFullOutput(self):

        print("Assembling full output for " + self.id + ".")

        if self.fileparent.mode() == 'realtime':

            with self.dequeLock:
                nones = [None] * len(self.rawTimes)
                data = [list(i) for i in zip(self.rawTimes, nones, nones, self.rawValues)]
            output_type = 'real'

        elif self.fileparent.mode() == 'file':

            # Attempt to retrieve the full downsample output
            downsampleFullOutput = self.dss.getFullOutput()

            # Set data either to the retrieved downsample or to the raw data
            if downsampleFullOutput is not None:

                print("(downsampled output)")

                data = downsampleFullOutput.to_records(index=False).tolist()
                output_type = 'downsample'

            else:

                print("(raw data output)")

                # Get reference to the series datastream from the HDF5 file
                dataset = self.fileparent.f['/'.join(self.h5path)][()]
                nones = [None] * self.rd.len
                data = [list(i) for i in zip(dataset[self.timecol].values.astype(np.float64), nones, nones, dataset[self.valcol].values.astype(np.float64))]
                output_type = 'real'

        else:

            # Having reached this point, the mode is invalid.
            raise Exception('Invalid mode found for fileparent in series.getFullOutput():', self.fileparent.mode())

        print("Completed assembly of full output for " + self.id + ".")

        # Return the JSON-ready output object
        return {
            "id": self.id,
            "labels": ['Date/Offset', 'Min', 'Max', self.id],
            "data": data,
            "output_type": output_type
        }

    # Produces JSON output for the series over a specified time range, with
    # starttime and stoptime being time offset floats in seconds.
    def getRangedOutput(self, starttime, stoptime):

        print("Assembling ranged output for " + self.id + ".")

        # Getting ranged output is not supported in realtime-mode.
        if self.fileparent.mode() == 'realtime':
            raise Exception('series.getRangedOutput() is not available in realtime-mode.')

        # Get the appropriate downsample for this time range
        ds = self.dss.getRangedOutput(starttime, stoptime)

        if isinstance(ds, pd.DataFrame):
            print("(downsampled output)")
            data = ds.to_records(index=False).tolist()
            output_type = 'downsample'

        else:
            print("(raw data output)")
            data = self.rd.getRangedOutput(starttime, stoptime)
            output_type = 'real'

        print("Completed assembly of ranged output for " + self.id + ".")

        # Return the JSON-ready output object
        return {
            "id": self.id,
            "labels": ['Date/Offset', 'Min', 'Max', self.id],
            "data": data,
            "output_type": output_type
        }

    # Process and store all downsamples for the series.
    def processAndStore(self):

        p = psutil.Process()

        print("Processing & storing all downsamples for the series " + self.id)
        start = time.time()

        print("MEM PRE-PULLD: " + str(p.memory_full_info().uss / 1024 / 1024) + " MB")

        # Pull raw data for the series into memory
        self.pullRawDataIntoMemory()

        print("MEM AFT-PULLD: "+str(p.memory_full_info().uss/1024/1024)+" MB")

        # Build & store to file all downsamples for the series
        self.dss.processAndStore()

        print("MEM AFT-DSPRC: " + str(p.memory_full_info().uss / 1024 / 1024) + " MB")

        # Remove raw data for the series fromm memory
        self.initializeRawDataInMemory()

        print("MEM AFT-REMVD: " + str(p.memory_full_info().uss / 1024 / 1024) + " MB")

        end = time.time()
        print("Completed processing & storing all downsamples for the series " + self.id + ". Took " + str(round((end - start) / 60, 3)) + " minutes.")

    # Pulls the raw data for the series from the file into memory (self.rawTimeOffsets
    # and self.rawValues).
    def pullRawDataIntoMemory(self):

        print("Reading raw series data into memory for " + self.id + ".")
        start = time.time()

        # If we're in realtime mode, this procedure is not applicable.
        if self.fileparent.mode() == 'realtime':
            print("Reading raw series n/a since we're in mem mode. Returning.")
            return

        # Get reference to the series datastream from the HDF5 file
        dataset = self.fileparent.f['/'.join(self.h5path)][()]

        self.rawTimes = dataset[self.timecol].values.astype(np.float64)
        self.rawValues = dataset[self.valcol].values.astype(np.float64)

        end = time.time()
        print("Finished reading raw series data into memory for " + self.id + " (" + str(self.rawTimes.shape[0]) + " points). Took " + str(round(end - start, 5)) + "s.")

    # Initializes the raw data stored for the series in memory and thereby
    # removes it from memory.
    def initializeRawDataInMemory(self):

        # Initialize raw data
        # self.rawTimes = []
        # self.rawValues = []
        self.rawTimes = deque(maxlen=config.M)
        self.rawValues = deque(maxlen=config.M)