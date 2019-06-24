import bisect
import config
import time
from cylib import buildDownsampleFromRaw, buildNextDownsampleUp, numDownsamplesToBuild

# Represents a set of downsamples for a series of data.
class Downsamples:

    # Expected member variables:
    #   downsamples: array of downsamples at various resolutions

    def __init__(self, seriesparent):

        outerStart = time.time()

        # Set the series parent
        self.seriesparent = seriesparent

        # We assume datagroup has two non-empty datasets, "datetime" and "value".
        if len(self.seriesparent.rawTimeOffsets) < 1 or len(self.seriesparent.rawValues) < 1:
            return

        # We assume the two datasets are of equal length
        if len(self.seriesparent.rawTimeOffsets) != len(self.seriesparent.rawValues):
            return

        # Get an array of the downsamples to build (each element of the array
        # is a number of intervals to divide the data set into).
        numDownsamples = numDownsamplesToBuild(self.seriesparent.rawTimeOffsets, config.M, config.stepMultiplier)

        # Holds the downsample sets (each element is a NumPy array which holds
        # the intervals for that downsample level
        self.downsamples = [None] * numDownsamples

        # If we do not need to build any downsamples, return now.
        if numDownsamples < 1:
            return

        # Begin by building the last downsample from the raw data first.
        # NOTE: We will build the self.downsamples list in reverse order
        # initially and then reverse its order at the end so that we end
        # up with the downsamples in order from smallest number of
        # intervals to largest.
        lastDownsampleNumIntervals = config.M*(config.stepMultiplier**(numDownsamples-1))
        print("Creating " + str(lastDownsampleNumIntervals) + " intervals.")
        start = time.time()
        self.downsamples[-1] = buildDownsampleFromRaw(self.seriesparent.rawTimeOffsets, self.seriesparent.rawValues, lastDownsampleNumIntervals)
        end = time.time()
        print("Done. Yielded " + str(self.downsamples[-1].shape[0]) + " intervals. Took " + str(round(end - start, 5)) + "s.")
        
        # Build the next numDownsamples-1 downsamples (because we've already
        # built the first one).
        for i in range(-2, -numDownsamples-1, -1):
            print("Creating " + str(self.getNumIntervalsByIndex(i)) + " intervals.")
            start = time.time()
            self.downsamples[i] = buildNextDownsampleUp(self.downsamples[i+1], self.getTimePerIntervalByIndex(i+1), config.stepMultiplier)
            end = time.time()
            print("Done. Yielded " + str(self.downsamples[i].shape[0]) + " intervals. Took " + str(round(end - start, 5)) + "s.")

        print("Completed build of all downsamples for this series.")

        outerEnd = time.time()
        print("Downsample Set: " + str(round(outerEnd - outerStart, 5)) + "s")

        print(self)

    ################ FROM DOWNSAMPLE -- NEEDS ADAPTATION
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

        return self.intervals[startIntervalIndex:(stopIntervalIndex + 1)]

    # Returns a reference to the appropriate downsample for the given time range.
    # Expects starttime & stoptime to be time offsets floats in seconds.
    def getDownsample(self, starttime, stoptime):

        # If there are no downsamples available, we cannot provide one
        if len(self.downsamples) < 1:
            return

        # Calculate the timespan of the view window, in seconds
        timespan = stoptime - starttime

        # Calculate the largest interval size to deliver <= M intervals, in seconds
        maxTimePerInterval = timespan / config.M

        # Determine which downsample to use. To do this, find the first
        # downsample, going from the largest interval downwards, which is too
        # small and then select the previous one.
        i = 0
        while i < len(self.downsamples) and self.downsamples[i].timePerInterval >= maxTimePerInterval:
            i = i + 1
        chosenDownsampleIndex = i - 1

        # We do not expect this, but in case even the largest interval size was
        # too small, return the largest one we have.
        if chosenDownsampleIndex < 0:
            chosenDownsampleIndex = 0

        # If we reached the lowest downsample level, check whether we should be
        # using real data points. If so, return nothing.
        if (chosenDownsampleIndex == len(self.downsamples) - 1) and maxTimePerInterval <= self.downsamples[chosenDownsampleIndex].timePerInterval / 2:
            return

        return self.downsamples[chosenDownsampleIndex]

    # Returns the number of intervals for the downsample at index i.
    def getNumIntervalsByIndex(self, i):

        # Handle negative index
        if i < 0:
            i = len(self.downsamples) + i

        return config.M * (config.stepMultiplier ** i)

    # Returns the time-per-interval for the downsample at index i.
    def getTimePerIntervalByIndex(self, i):

        # Handle negative index
        if i < 0:
            i = len(self.downsamples) + i

        return self.getTimespan() / self.getNumIntervalsByIndex(i)

    # Returns the timespan of the data series.
    def getTimespan(self):
        return self.seriesparent.rawTimeOffsets[-1] - self.seriesparent.rawTimeOffsets[0]

    def __str__(self):
        s = ""
        for i in range(len(self.downsamples)):

            s = s + "Downsample #" + str(i + 1) + " - Official Intervals " + str(self.getNumIntervalsByIndex(i)) + " - Actual Intervals " + str(self.downsamples[i].shape[0]) + " - Time Per Interval " + str(self.getTimePerIntervalByIndex(i)) + "s" + "\n"

            s = s + "First 5:" + "\n"
            j = 0
            while j < 5:
                s = s + str(self.downsamples[i][j]) + "\n"
                j = j + 1

            s = s + "Last 5:" + "\n"
            j = 6
            while j > 0:
                s = s + str(self.downsamples[i][-j]) + "\n"
                j = j - 1

            s = s + "\n"

        return s