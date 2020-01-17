import numpy as np
from cylib import getSliceParam

# Represents raw data for a single time series
class RawData:
    
    # RawData may operate in file-mode or data-mode. If seriesparent.h5path`
    def __init__(self, seriesparent):
        
        # Set the series parent
        self.seriesparent = seriesparent
        
        # Grab a reference to the dataset
        dataset = self.getDatasetReference()
        
        # Holds the number of data points in the raw data series
        self.len = dataset.len()
        
        # Holds the timespan of the time series
        self.timespan = dataset[-1]['time'] - dataset[0]['time']

    # Returns a slice of the appropriate downsample for the given time range, or
    # nothing if there is no appropriate downsample available (in this case, raw
    # data should be used). Expects starttime & stoptime to be time offsets
    # floats in seconds.
    def getRangedOutput(self, starttime, stoptime):
        
        # Grab a reference to the dataset
        ds = self.getDatasetReference()
        
        # Find the start & stop indices based on the start & stop times.
        # startIndex = np.searchsorted(self.rawTimeOffsets, starttime)
        # stopIndex = np.searchsorted(self.rawTimeOffsets, stoptime, side='right')
        startIndex = getSliceParam(ds, 0, starttime)
        stopIndex = getSliceParam(ds, 1, stoptime)
        
        # Assemble the output data
        nones = [None] * (stopIndex - startIndex)
        # data = [list(i) for i in zip(self.rawTimeOffsets[startIndex:stopIndex], nones, nones, self.rawValues[startIndex:stopIndex])]
        return [list(i) for i in zip(ds[startIndex:stopIndex]['time'], nones, nones, ds[startIndex:stopIndex]['value'].astype(np.float64))]
        
    def getDatasetReference(self):
        
        return self.seriesparent.fileparent.f.get('/'.join(self.seriesparent.h5path))