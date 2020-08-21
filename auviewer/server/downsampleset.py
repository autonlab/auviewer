import logging
import psutil
import time

from .config import config
from .cylib import buildDownsampleFromRaw, buildNextDownsampleUp, getSliceParam, numDownsamplesToBuild

# Represents a set of downsamples for a series of data.
class DownsampleSet:

    def __init__(self, seriesparent):

        # Set the series parent
        self.seriesparent = seriesparent

        # Holds the number of downsamples available for the series
        self.numDownsamples = self.getNumDownsamplesFromFile()

    # Returns the full series output at the highest downsample level, or None
    # if no downsample exists for the series.
    def getFullOutput(self):

        if self.numDownsamples < 1:
            return None

        return self.seriesparent.fileparent.pf['/'.join(self.seriesparent.h5pathDownsample) + '/' + '0'][:]

    # Returns the number of downsamples available for this series in the
    # processed data file.
    def getNumDownsamplesFromFile(self):

        # If no processed file is available, return 0
        if not hasattr(self.seriesparent.fileparent, 'pf'):
            return 0

        # Get reference to the group containing the downsamples
        grp = self.seriesparent.fileparent.pf['/'.join(self.seriesparent.h5pathDownsample)]

        # If no downsamples are available, return 0
        if grp is None:
            return 0

        # Get the keys present in the group (they should all be strings of
        # integers 0..n where n+1 is the count of downsamples.
        keys = grp.list()['datasets']

        # We start with -1
        maxDownsampleIndex = -1

        # Crawl up the downsample indicates, confirming that each is present.
        # There's obviously an easier way to do this, but we're doing some
        # verification of integrity here.
        while str(maxDownsampleIndex + 1) in keys:
            maxDownsampleIndex = maxDownsampleIndex + 1

        # We have the real max downsample index, so that plus one is the count.
        return maxDownsampleIndex + 1

    # Returns the number of intervals for the downsample at index i.
    def getNumIntervalsByIndex(self, i, nds=-1):

        if nds == -1:
            nds = self.numDownsamples

        # Handle negative index
        if i < 0:
            i = nds + i

        return config['M'] * (config['stepMultiplier'] ** i)

    # Returns a slice of the appropriate downsample for the given time range, or
    # nothing if there is no appropriate downsample available (in this case, raw
    # data should be used). Expects starttime & stoptime to be time offsets
    # floats in seconds.
    def getRangedOutput(self, starttime, stoptime):

        # If there are no downsamples available, we cannot provide one
        if self.numDownsamples < 1:
            return None

        # Calculate the timespan of the view window, in seconds
        timespan = stoptime - starttime

        # Get index of the appropriate downsample to use
        dsi = self.whichDownsampleIndexForTimespan(timespan)

        # If we should be using raw data, return nothing
        if dsi == -1:
            return None

        # Get reference to the downsample dataset in the processed file
        ds = self.seriesparent.fileparent.pf['/'.join(self.seriesparent.h5pathDownsample) + '/' + str(dsi)]

        # Find the start & stop indices based on the start & stop times.
        startIndex = getSliceParam(ds, '0', 0, starttime)
        stopIndex = getSliceParam(ds, '0', 1, stoptime)

        # Return the downsample slice
        return ds[startIndex:stopIndex]

    # Returns the time-per-interval for the downsample at index i.
    def getTimePerIntervalByIndex(self, i, nds=-1):

        if nds == -1:
            nds = self.numDownsamples

        # Handle negative index
        if i < 0:
            i = nds + i

        return self.seriesparent.rd.timespan / self.getNumIntervalsByIndex(i, nds)

    # Build all necessary downsamples, and store in the processed file.
    def processAndStore(self):

        p = psutil.Process()

        # We assume:
        #   - Datagroup has two non-empty datasets, "datetime" and "value";
        #   - The two datasets are of equal length;
        #   - There exists a file for storing processed data.
        if (len(self.seriesparent.rawTimes) < 1 or len(self.seriesparent.rawValues) < 1) or len(self.seriesparent.rawTimes) != len(self.seriesparent.rawValues) or not hasattr(self.seriesparent.fileparent, 'pf'):
            return

        # Get an array of the downsamples to build (each element of the array
        # is a number of intervals to divide the data set into).
        ndtb = numDownsamplesToBuild(self.seriesparent.rawTimes, config['M'], config['stepMultiplier'])

        # If we do not need to build any downsamples, return now.
        if ndtb < 1:
            return

        # Begin by building the last downsample from the raw data first. Then
        # proceed by building the next downsample up from the previously-built
        # downsample until all downsamples have been created.
        logging.info(f"MEM PRE-DSBLD: {p.memory_full_info().uss / 1024 / 1024} MB")
        for i in range(-1, -ndtb - 1, -1):

            logging.info(f"Creating downsample ({self.getNumIntervalsByIndex(i, ndtb)} intervals possible).")
            start = time.time()

            # Build the downsample
            if i == -1:
                logging.info("This pass from raw.")
                downsample = buildDownsampleFromRaw(self.seriesparent.rawTimes, self.seriesparent.rawValues, self.getNumIntervalsByIndex(i, ndtb))
            else:
                downsample = buildNextDownsampleUp(previousDownsample, self.getTimePerIntervalByIndex(i + 1, ndtb), config['stepMultiplier'])

            logging.info(f"MEM AFT-DSBLD: {p.memory_full_info().uss / 1024 / 1024} MB")

            # Save the just-computed downsample for use on the next loop iteration
            previousDownsample = downsample

            logging.info(f"MEM AFT-REPLP: {p.memory_full_info().uss / 1024 / 1024} MB")

            end = time.time()
            logging.info(f"Done creating downsample. Yielded {downsample.shape[0]} actual intervals. Took {round(end - start, 5)}s.")

            logging.info("Storing the downsample to the processed file.")
            start = time.time()

            try:

                # Store the downsample
                dds_name = '{}/{}'.format('/'.join(self.seriesparent.h5pathDownsample), i % ndtb)
                self.seriesparent.fileparent.pf[dds_name] = downsample
                logging.info(f"MEM AFT-STRFL: {p.memory_full_info().uss / 1024 / 1024} MB")

            except:

                logging.info(f"There was an exception while creating the dataset in the processed data file at the path: {'/'.join(self.seriesparent.h5pathDownsample)}/{i%ndtb}.")
                raise

            end = time.time()
            logging.info(f"Done storing to file. Took {round(end - start, 5)}s.")

        # Update the self.numDownsamples count.
        self.numDownsamples = self.getNumDownsamplesFromFile()

    # Returns the index of the appropriate downsample which should be used for
    # the given timespan, or -1 if raw data should be used instead.
    def whichDownsampleIndexForTimespan(self, timespan):

        # Calculate the largest interval size to deliver <= M intervals, in seconds
        maxTimePerInterval = timespan / config['M']

        # Determine which downsample to use. To do this, find the first
        # downsample, going from the largest interval downwards, which is too
        # small and then select the previous one.
        i = 0
        while i < self.numDownsamples and self.getTimePerIntervalByIndex(i) >= maxTimePerInterval:
            i = i + 1
        dsi = i - 1

        # We do not expect this, but in case even the largest interval size was
        # too small, return the largest one we have.
        if dsi < 0:
            dsi = 0

        # If we reached the lowest downsample level, check whether we should be
        # using real data points. If so, return -1.
        if (dsi == self.numDownsamples - 1) and maxTimePerInterval <= self.getTimePerIntervalByIndex(dsi) / 2:
            return -1

        return dsi
