import multiprocessing
import numpy as np
import datetime as dt
import h5py

from .cylib import getSliceParam
# from .project import ds

# Represents raw data for a single time series
class RawData:

    # RawData may operate in file-mode or data-mode. If seriesparent.h5path`
    def __init__(self, seriesparent, loading=True):

        # Set the series parent
        self.seriesparent = seriesparent

        # Grab a reference to the dataset
        dataset = self.getDatasetReference(loading)

        # Holds the number of data points in the raw data series
        self.len = dataset.nrow

        # Holds the timespan of the time series
        if self.len < 2:
            self.timespan = 0
        else:
            # self.timespan = np.abs(np.diff(dataset[[-1, 0]][self.seriesparent.timecol].values.astype(np.float64))[0])
            self.timespan = dataset[[0, -1]]
            self.timespan = self.timespan[self.seriesparent.timecol]
            self.timespan = self.timespan.values.astype(np.float64)
            self.timespan = np.abs(np.diff(self.timespan)[0])
    # def getRangedOutputParallel(series, starttimes, stoptimes):
    #     dss = [s.getDatasetReference for s in series]

    #     args = list()
    #     args2 = list()
    #     for i in range(len(series)):
    #         args.append(dss[i], series[i].seriesparent.timecol, 0, starttimes[i])
    #         args2.append(dss[i], series[i].seriesparent.timecol, 1, stoptimes[i])
    #     pool = multiprocessing.Pool(8)
    #     startresults = zip(*pool.map(getSliceParam, args))
    #     stopresults = zip(*pool.map(getSliceParam, args2))

    #     startlist = list(startresults)
    #     stoplist = list(stopresults)

    #     noness = list()
    #     ds_slices = list()
    #     for i in range(len(startlist)):
    #         noness.append([None]*(stoplist[i]-startlist[i]))
    #         ds = dss[i]
    #         ds_slices.append(ds[startlist[i]:stoplist[i]])
    #     results = []
    #     for i in range(len(ds_slices)):
    #         ds_slice = ds_slices[i]
    #         sel = series[i]
    #         results.append ([list(j) for j in zip(ds_slice[sel.seriesparent.timecol].values.astype(np.float64), noness[i], noness[i], ds_slice[sel.seriesparent.valcol].values.astype(np.float64))])
        
    #     return results


    # Returns a slice of the appropriate downsample for the given time range, or
    # nothing if there is no appropriate downsample available (in this case, raw
    # data should be used). Expects starttime & stoptime to be time offsets
    # floats in seconds.
    def getRangedOutput(self, starttime, stoptime):

        # Grab a reference to the dataset
        ds = self.getDatasetReference()

        # print("time per interval:", timePerInterval)
        

        # Find the start & stop indices based on the start & stop times.
        # startIndex = np.searchsorted(self.rawTimeOffsets, starttime)
        # stopIndex = np.searchsorted(self.rawTimeOffsets, stoptime, side='right')
        # startIndex = getSliceParam(ds, self.seriesparent.timecol, 0, starttime)
        # stopIndex = getSliceParam(ds, self.seriesparent.timecol, 1, stoptime)

        startIndex = getSliceParam(ds, self.seriesparent.timecol, 0, starttime)
        stopIndex = getSliceParam(ds, self.seriesparent.timecol, 1, stoptime)


        # Assemble the output data
        nones = [None] * (stopIndex - startIndex)
        # data = [list(i) for i in zip(self.rawTimeOffsets[startIndex:stopIndex], nones, nones, self.rawValues[startIndex:stopIndex])]
        ds_slice = ds[startIndex:stopIndex]
        return [list(i) for i in zip(ds_slice[self.seriesparent.timecol].values.astype(np.float64), nones, nones, ds_slice[self.seriesparent.valcol].values.astype(np.float64))]

    def getRangedOutputWithDS(self, ds, starttime, stoptime):

        # Grab a reference to the dataset
        # ds = self.getDatasetReference()

        # Find the start & stop indices based on the start & stop times.
        # startIndex = np.searchsorted(self.rawTimeOffsets, starttime)
        # stopIndex = np.searchsorted(self.rawTimeOffsets, stoptime, side='right')
        startIndex = getSliceParam(ds, self.seriesparent.timecol, 0, starttime)
        stopIndex = getSliceParam(ds, self.seriesparent.timecol, 1, stoptime)


        # Assemble the output data
        nones = [None] * (stopIndex - startIndex)
        # data = [list(i) for i in zip(self.rawTimeOffsets[startIndex:stopIndex], nones, nones, self.rawValues[startIndex:stopIndex])]
        ds_slice = ds[startIndex:stopIndex]
        return [list(i) for i in zip(ds_slice[self.seriesparent.timecol].values.astype(np.float64), nones, nones, ds_slice[self.seriesparent.valcol].values.astype(np.float64))]

    def getDatasetReference(self, loading=False):

        
        return self.seriesparent.fileparent.f['/'.join(self.seriesparent.h5path)]
