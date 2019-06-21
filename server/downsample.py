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
