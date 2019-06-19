import bisect
import config
# import datetime as dt
from collections import deque

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

        # Will hold the downsample intervals
        self.intervals = []

        # We assume datagroup has two non-empty datasets, "datetime" and "value".
        if len(self.dssparent.seriesparent.rawTimeOffsets) < 1 or len(self.dssparent.seriesparent.rawValues) < 1:
            return

        # We assume the two datasets are of equal length
        if len(self.dssparent.seriesparent.rawTimeOffsets) != len(self.dssparent.seriesparent.rawValues):
            return

        # Grab the first & last time offsets for this series
        firsttime = self.dssparent.seriesparent.rawTimeOffsets[0]
        lasttime = self.dssparent.seriesparent.rawTimeOffsets[len(self.dssparent.seriesparent.rawTimeOffsets) - 1]

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

        # Establish our initial boundaries for the first interval
        leftboundary = firsttime
        rightboundary = leftboundary + self.timePerInterval

        # Tracks the trailing data point counts of up to the last M intervals
        trailingSummary = TrailingSummary()

        # Prime the trailing summary with an initial interval since we're
        # starting from the first interval (e.g. if the first data point belongs
        # to the first interval, the first inner while loop would be skipped).
        trailingSummary.addInterval()

        # Grab data points length so we don't have to look it up every time.
        dataPointsLength = len(self.dssparent.seriesparent.rawTimeOffsets)

        # Holds the index of the current data point we're working on
        i = 0

        # For all data points
        while i < dataPointsLength:

            print(type(self.dssparent.seriesparent.rawTimeOffsets))
            quit()

            # While the next data point does not belong to the current interval,
            # progress to the next interval.
            while self.dssparent.seriesparent.rawTimeOffsets[i] >= rightboundary:

                # Update left & right boundaries to the next interval
                leftboundary = rightboundary
                rightboundary = leftboundary + self.timePerInterval

                # Add an interval to the trailing summary
                trailingSummary.addInterval()

            # Having escaped the while loop, we have reached a new interval to
            # which the next data point belongs, so we create a new interval.
            self.intervals.append(Interval(self.dssparent.seriesparent.rawValues[i], leftboundary + (self.timePerInterval / 2)))

            # While the next data point occurs within the current interval, add
            # it to the interval's statistics.
            while i < dataPointsLength and self.dssparent.seriesparent.rawTimeOffsets[i] < rightboundary:

                # Add the data point to the interval
                self.intervals[len(self.intervals) - 1].addDataPoint(self.dssparent.seriesparent.rawValues[i])

                # Increment i to progress to the next data point
                i = i + 1

            # Finalize the interval count in the trailing summary
            trailingSummary.finalizeInterval(self.intervals[len(self.intervals) - 1])

        # Attach a flag of whether the threshold was reached to this downsample.
        self.thresholdReached = trailingSummary.thresholdReached

        if self.thresholdReached:
            print("Threshold reached at " + str(numIntervals))
        else:
            print("Threshold not reached at " + str(numIntervals))

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

# Interval defines a data summary interval for downsampling
class Interval:

    # Expected member variables:
    #   min: minimum value for the interval
    #   max: maximum value for the interval
    #   count: number of data points the interval represents
    #   time: datetime of the middle of the interval

    # Constructor accepts one parameter, firstvalue, which should be the value
    # from the first data point and will be assigned to min & max initially.
    def __init__(self, firstvalue, time):

        # Prime min & max with the first data point value
        self.min = firstvalue
        self.max = firstvalue

        # Set time
        self.time = time

        # We've primed the interval with the first data point, so the count
        # starts at 1
        self.count = 1

    def __eq__(self, other):
        return self.time == other.time if isinstance(other, Interval) else self.time == other

    def __ne__(self, other):
        return self.time != other.time if isinstance(other, Interval) else self.time != other

    def __lt__(self, other):
        return self.time < other.time if isinstance(other, Interval) else self.time < other

    def __le__(self, other):
        return self.time <= other.time if isinstance(other, Interval) else self.time <= other

    def __gt__(self, other):
        return self.time > other.time if isinstance(other, Interval) else self.time > other

    def __ge__(self, other):
        return self.time >= other.time if isinstance(other, Interval) else self.time >= other

    # Adds the provided data point value to the interval
    def addDataPoint(self, dp):

        # Update max
        if dp > self.max:
            self.max = dp

        # Update min
        if dp < self.min:
            self.min = dp

        # Update count
        self.count = self.count + 1

# TrailingSummary maintains a trailing summary of counts for the last M
# intervals and determines whether the threshold is reached for the downsample
# being necessary.
class TrailingSummary:

    def __init__(self):

        # Holds the queue of the last M intervals, where each queue element
        # is the integer count of data points in the interval.
        self.lastMIntervals = deque()

        # This is a boolean that tracks whether we've reached the threshold
        # where some sequence of M intervals contains > M*2 points.
        self.thresholdReached = False
        
        # Holds the current summary of data point counts for all intervals
        # currently in the queue.
        self.currentTrailingSummary = 0

    # Adds an interval (initially with 0 count) to the queue of last M intervals.
    # A finalizeInterval call may happen after addInterval, but it is not
    # necessary (in this case, the count for the interval would remain at 0).
    def addInterval(self):

        # Add a count representation for the interval to the queue
        self.lastMIntervals.append(0)

        # Pop out from lastMIntervals if we've reached M intervals. At any given
        # time, we want to have no more than M intervals.
        if len(self.lastMIntervals) > config.M:
            
            # Pop out the oldest interval in the queue
            poppedInterval = self.lastMIntervals.popleft()
            
            # Update the current summary to reflect removal of the popped interval
            self.currentTrailingSummary = self.currentTrailingSummary - poppedInterval
            
    # Updates the final count for the interval. Should be called after an
    # addInterval call, once interval has been finalized.
    def finalizeInterval(self, interval):

        # Verify that we have at least one element in the queue
        if len(self.lastMIntervals) < 1:
            return

        # Set the final interval count in the trailing summary representation
        self.lastMIntervals[len(self.lastMIntervals)-1] = interval.count
        
        # Update the current trailing summary
        self.currentTrailingSummary = self.currentTrailingSummary + interval.count

        # Check if the threshold has been reached. The M*2 threshold is used
        # because, for min/max, 2 "y" values are transmitted, whereas only 1 is
        # transmitted for raw data points.
        if self.currentTrailingSummary > config.M * 2:
            self.thresholdReached = True
