import config
from downsample import Downsample

# Represents a set of downsamples for a series of data.
class DownsampleSet:

    # Expected member variables:
    #   downsamples: array of downsamples at various resolutions

    def __init__(self, seriesparent):

        # Holds the downsample sets
        self.downsamples = []

        # Set the series parent
        self.seriesparent = seriesparent

    # Builds all necessary downsamples for the series.
    def build(self):

        # Tracks the next number of intervals for which to create a downsample.
        numIntervals = config.M

        while True:

            print("Creating " + str(numIntervals) + " intervals.")

            # Create a Downsample instance, and build the downsample
            ds = Downsample(self, numIntervals)

            # If the downsample proved necessary, add it to the downsamples list.
            # If not, break out of the loop.
            if ds.thresholdReached:
                self.downsamples.append(ds)
            else:
                break

            print("Created " + str(numIntervals) + " intervals.")

            # Increment the number of intervals for next round by 100%
            numIntervals = numIntervals * 2

        print("Broke out of downsample creation loop.")

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