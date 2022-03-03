import numpy as np
import datetime as dt

from .cylib import getSliceParam

# Represents raw data for a single time series
class RawData:

    # RawData may operate in file-mode or data-mode. If seriesparent.h5path`
    def __init__(self, seriesparent):

        # Set the series parent
        self.seriesparent = seriesparent

        # Grab a reference to the dataset
        dataset = self.getDatasetReference()

        # Holds the number of data points in the raw data series
        self.len = dataset.nrow

        # Holds the timespan of the time series
        if self.len < 2:
            self.timespan = 0
        else:
            # self.timespan = np.abs(np.diff(dataset[[-1, 0]][self.seriesparent.timecol].values.astype(np.float64))[0])
            self.timespan = dataset[[-1, 0]]
            self.timespan = self.timespan[self.seriesparent.timecol]
            self.timespan = self.timespan.values.astype(np.float64)
            self.timespan = np.abs(np.diff(self.timespan)[0])

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
        startIndex = getSliceParam(ds, self.seriesparent.timecol, 0, starttime)
        stopIndex = getSliceParam(ds, self.seriesparent.timecol, 1, stoptime)

        # Slice the output data the output data
        ds_slice = ds[startIndex:stopIndex]

        # Pull the raw times & values
        rawTimes = ds_slice[self.seriesparent.timecol].values.astype(np.float64)
        rawValues = ds_slice[self.seriesparent.valcol].values.astype(np.float64)

        # Drop nan values
        mask = ~np.isnan(rawValues)
        rawTimes = rawTimes[mask]
        rawValues = rawValues[mask]

        nones = [None] * len(rawTimes)

        return [list(i) for i in zip(rawTimes, nones, nones, rawValues)]

    def getDatasetReference(self):
        
        return self.seriesparent.fileparent.f['/'.join(self.seriesparent.h5path)]
