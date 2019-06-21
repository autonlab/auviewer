import bisect
import config
# import datetime as dt
from collections import deque
from cylib import buildDownsample, wasThresholdReached, whatDownsamplesToBuild
import time

# Downsample represents a single downsample level for a series at a specific
# interval size.
class Downsample:

    # Build builds a downsampled set of datagroup with numIntervals number of
    # points. Build will determine if the threshold of necessity for this
    # downsample has been reached. It will return True if the downsample is
    # necessary, and it will return False if the downsample is not necessary.
    # In either case, the downsample will be built.
    def __init__(self, dssparent, numIntervals):

        # Set the downsample series parent
        self.dssparent = dssparent

        # We assume datagroup has two non-empty datasets, "datetime" and "value".
        if len(self.dssparent.seriesparent.rawTimeOffsets) < 1 or len(self.dssparent.seriesparent.rawValues) < 1:
            return

        # We assume the two datasets are of equal length
        if len(self.dssparent.seriesparent.rawTimeOffsets) != len(self.dssparent.seriesparent.rawValues):
            return

        start = time.time()
        downsamplesToBuild = whatDownsamplesToBuild(self.dssparent.seriesparent.rawTimeOffsets, config.M)
        end = time.time()
        print("Took "+str(end-start)+"s.")
        print(downsamplesToBuild)

        quit()














        # Grab the first & last time offsets for this series
        firsttime = self.dssparent.seriesparent.rawTimeOffsets[0]
        lasttime = self.dssparent.seriesparent.rawTimeOffsets[-1]

        # Get the timespan, in seconds, as the difference between the first
        # and last data point offsets.
        timespan = lasttime - firsttime

        # Calculate the interval size in seconds
        self.timePerInterval = timespan / numIntervals

        # Our goal is to ensure that numIntervals intervals of timePerInterval
        # time encompass the data set, including the last point. Our intervals
        # are defined to be inclusive at the left boundary and non-inclusive at
        # the right boundary. In other words, an interval that starts at time
        # 1:00.000000 and ends at 2:00.000000 will include a point at
        # 1:00.000000 but will not include a point at 2:00.000000.
        #
        # Furthermore, there is the possibility of rounding in the division to
        # calculate timePerInterval.
        #
        # For both reasons above, we must evaluate whether to add 1 microsecond
        # to the timePerInterval.
        #
        # There are three cases to account for:
        # 1. Timespan was evenly divided into numIntervals intervals (timespan % numIntervals == 0).
        # 2. Timespan was not evenly divided (timespan % numIntervals != 0), and timePerInterval was rounded down.
        # 3. Timespan was not evenly divided (timespan % numIntervals != 0), and timePerInterval was rounded up.
        # ( Side note: Python 3 uses round-half-to-even rounding. )
        #
        # For cases 1 & 2, we must add 1 microsecond to the timePerInterval in
        # order to achieve the goal of numIntervals intervals including all data
        # points in the plot. For case 3, no action is needed.
        #
        # NOTE: We add firsttime here because we will start the interval windows
        # at firsttime.
        if firsttime + self.timePerInterval * numIntervals <= lasttime:

            # Add 1 microsecond. This covers cases 1 & 2.
            self.timePerInterval += .001

            # We expect the above action to achieve the "encompass all points"
            # goal. If it does not, raise an exception
            # as this is an unexpected condition.
            if firsttime + self.timePerInterval * numIntervals <= lasttime:
                raise RuntimeError('Algorithm for setting timespan to encompass all points failed unexpectedly.')

        # Build the downsampled intervals, and attach them to the class instance.
        start = time.time()
        self.intervals = buildDownsample(self.dssparent.seriesparent.rawTimeOffsets, self.dssparent.seriesparent.rawValues, self.timePerInterval)
        end = time.time()
        print("Downsample: "+str(round(end-start, 5))+"s.")
        # print("First 10:")
        # i = 0
        # while i < 10:
        #     print(self.intervals[i])
        #     i = i + 1
        #
        # print("Last 10:")
        # i = 1
        # while i < 11:
        #     print(self.intervals[-i])
        #     i = i + 1

        # Check whether threshold was reached, and set flag accordingly
        start = time.time()
        self.thresholdReached = wasThresholdReached(self.intervals, self.timePerInterval, self.dssparent.seriesparent.rawTimeOffsets.shape[0], config.M)
        end = time.time()
        print("Threshold: "+str(round(end-start, 5))+"s.")

        # print(len(self.intervals))
        #
        # print("FINISHED")
        #
        # quit()

    # Returns a list of the intervals in the range of starttime to stoptime.
    def getIntervals(self, starttime, stoptime):

        # Determine the index of the first interval to transmit for the view. To
        # do this, find the first interval which occurs after the starttime and
        # take the index prior to that as the starting interval.
        startIntervalIndex = bisect.bisect(self.intervals, starttime) - 1
        if startIntervalIndex < 0:
            startIntervalIndex = 0

        # Determine the index of the last interval to transmit for the view. To
        # do this, find the first interval which occurs after the stoptime and
        # take the index prior to that as the starting interval.
        stopIntervalIndex = bisect.bisect(self.intervals, stoptime) - 1
        if stopIntervalIndex < 0:
            stopIntervalIndex = 0

        return self.intervals[startIntervalIndex:(stopIntervalIndex+1)]
