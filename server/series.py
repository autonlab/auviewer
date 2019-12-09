import numpy as np
from rawdata import RawData
from downsampleset import DownsampleSet
from cylib import generateThresholdAlerts
import time
import psutil

# Represents a single time series of data.
class Series:

    # Reads a series into memory and builds the downsampling. Type is either
    # 'numeric' or 'waveform'. Fileparent is a reference to the File class
    # instance which contains the Series.
    def __init__(self, h5path, fileparent):
        
        # The series ID is the dataset path in the HDF5 file
        self.id = '/'.join(h5path)

        # Holds the ordered (hierarchical) list of groups and, ultimately,
        # dataset to which the series belongs. So, this is like a folder path,
        # where the first element is the outermost group name and the last
        # element is the dataset name of the series.
        self.h5path = h5path

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
        
    def generateThresholdAlerts(self, thresholdlow, thresholdhigh, mode, duration, persistence, maxgap):
        
        # Pull raw data for the series into memory
        self.pullRawDataIntoMemory()
        
        # Run through the data and generate alerts
        alerts = generateThresholdAlerts(self.rawTimeOffsets, self.rawValues, thresholdlow, thresholdhigh, mode, duration, persistence, maxgap)

        # Remove raw data for the series fromm memory
        self.removeRawDataFromMemory()
        
        return alerts

    # Produces JSON output for the series at the maximum time range.
    def getFullOutput(self):
    
        print("Assembling full output for " + self.id + ".")
    
        # Attempt to retrieve the full downsample output
        downsampleFullOutput = self.dss.getFullOutput()
        
        # Set data either to the retrieved downsample or to the raw data
        if downsampleFullOutput is not None:
            
            print("(downsampled output)")
            
            data = downsampleFullOutput.tolist()
            output_type = 'downsample'
            
        else:
            
            print("(raw data output)")

            # Get reference to the series datastream from the HDF5 file
            dataset = self.fileparent.f.get('/'.join(self.h5path))[()]
            nones = [None] * self.rd.len
            data = [list(i) for i in zip(dataset['time'], nones, nones, dataset['value'].astype(np.float64))]
            output_type = 'real'

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

        # Get the appropriate downsample for this time range
        ds = self.dss.getRangedOutput(starttime, stoptime)

        if isinstance(ds, np.ndarray):
            print("(downsampled output)")
            data = ds.tolist()
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
        self.removeRawDataFromMemory()

        print("MEM AFT-REMVD: " + str(p.memory_full_info().uss / 1024 / 1024) + " MB")

        end = time.time()
        print("Completed processing & storing all downsamples for the series " + self.id + ". Took " + str(round((end - start) / 60, 3)) + " minutes.")

    # Pulls the raw data for the series from the file into memory (self.rawTimeOffsets
    # and self.rawValues).
    def pullRawDataIntoMemory(self):

        print("Reading raw series data into memory for " + self.id + ".")
        start = time.time()

        # Get reference to the series datastream from the HDF5 file
        dataset = self.fileparent.f.get('/'.join(self.h5path))[()]

        self.rawTimeOffsets = dataset['time']
        self.rawValues = dataset['value'].astype(np.float64)

        end = time.time()
        print("Finished reading raw series data into memory for " + self.id + " (" + str(self.rawTimeOffsets.shape[0]) + " points). Took " + str(round(end - start, 5)) + "s.")
        
    def removeRawDataFromMemory(self):
    
        # Initialize raw data to None
        self.rawTimeOffsets = None
        self.rawValues = None
