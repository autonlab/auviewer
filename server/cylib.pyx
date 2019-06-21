#!python
#cython: boundscheck=False
#cython: wraparound=False

import numpy as np
cimport numpy as np

def buildNextDownsampleUp(np.ndarray[np.float64_t, ndim=2] intervals, int stepMultiplier):

    # Get the number of intervals in the original downsample.
    cdef int numIntervalsOriginal = intervals.shape[0]

    # Do a sanity check
    if numIntervalsOriginal < 2:
        return

    # The new downsample will hold original/stepMultiplier number of intervals
    # (we're building the next level up, so we're consolidating intervals).
    # NOTE: We can assume even divisibility.
    cdef int numIntervalsNew = numIntervalsOriginal/stepMultiplier

    # Will hold our new downsample. We allocate the worst-case number of
    # intervals needed for the new downsample, which would be equal to the
    # original downsample (for example, if each interval of the original
    # downsample were separated from the other by at least
    # timePerIntervalOriginal * stepMultiplier.
    cdef np.ndarray[np.float64_t, ndim=2] intervalsNew = np.zeros((numIntervalsNew, 3))

    # Determine the original time-per-interval
    cdef double timePerIntervalOriginal = intervals[1][0] - intervals[0][0]

    # Hold the half time-per-interval so we can save some computation in the loop.
    cdef double halfTimePerIntervalOriginal = timePerIntervalOriginal / 2

    # Will track the stepwise left & right boundary of the new intervals
    cdef double leftboundaryNew = intervals[0][0]-halfTimePerIntervalOriginal
    cdef double rightboundaryNew = leftboundary + timePerIntervalOriginal*stepMultiplier
    
    # These index pointers will track our position along the original & new
    # interval sets.
    cdef int cio = 0
    cdef int cin = 0
    
    # Temporary-use iterator to be used below
    cdef int i

    # Build the new downsample intervals
    while cin < numIntervalsNew:
        
        # Prime the min & max of the new interval to the first original interval
        intervalsNew[cin][1] = intervals[cio][1]
        intervalsNew[cin][2] = intervals[cio][2]

        # Go through the next stepMultiplier intervals of the original, and
        # consolidate the statistics for the new set.
        i = 0
        while i < stepMultiplier and cio < numIntervalsOriginal:

            # Update min & max
            if intervals[cio][1] < intervalsNew[cin][1]:
                intervalsNew[cin][1] = intervals[cio][1]
            if intervals[cio][2] > intervalsNew[cin][2]:
                intervalsNew[cin][2] = intervals[cio][2]

            # Add the time offset (it will be divided by stepMultiplier at the
            # end to yield the average time offset for the new interval
            intervalsNew[cin][0] = intervalsNew[cin][0] + intervals[cio][0]

            # Increment to proceed to the next original interval
            cio = cio + 1

            # Increment our counter
            i = i + 1

        # Divide the time offset for the new interval by stepMultiplier to
        # yield the average time offset of the original intervals represented.
        intervalsNew[cin][0] = intervalsNew[cin][0] / stepMultiplier

        # Increment to proceed to the next new interval
        cin = cin + 1

    # Return the new downsample intervals
    return intervalsNew

# Given a series of raw values and a time-per-interval parameter, produces and
# returns a two-dimension NumPy array of downsample intervals
def buildDownsampleFromRaw(np.ndarray[np.float64_t, ndim=1] rawOffsets, np.ndarray[np.float64_t, ndim=1] rawValues, int numIntervals):

    # Calculate the timespan of the entire dataset
    cdef double timespan = rawOffsets[rawOffsets.shape[0]-1] - rawOffsets[0]

    # Calculate the interval size in seconds
    cdef double timePerInterval = timespan / numIntervals

    # Allocate the maximum number of intervals needed (excess will be sliced off
    # at the end). The two-dimensional array will have 3 columns and numIntervals
    # rows. The columns, in order, will be: Time Offset, Min, Max, # Points.
    cdef np.ndarray[np.float64_t, ndim=2] intervals = np.zeros((numIntervals, 3))

    # Establish our initial boundaries for the first interval
    cdef double leftboundary = rawOffsets[0]
    cdef double rightboundary = leftboundary + timePerInterval

    # Grab data points length so we don't have to look it up every time.
    cdef int numDataPoints = rawOffsets.shape[0]

    # Holds the index of the current data point we're working on
    cdef int cdpi = 0
    
    # Holds the index of the current interval we're working on. We start at -1
    # because the loop will increment the index the first time it runs in order
    # to point to the "first" interval.
    cdef int cii = -1

    # For all data points
    while cdpi < numDataPoints:

        # While the next data point does not belong to the current interval,
        # progress to the next interval.
        while rawOffsets[cdpi] >= rightboundary:

            # Update left & right boundaries to the next interval
            leftboundary = rightboundary
            rightboundary = leftboundary + timePerInterval

            # NOTE: We do not progress cii because we have simply skipped an
            # empty interval, and we do not store/represent empty intervals.

        # Having escaped the while loop, we have reached a new interval to
        # which the next data point belongs, so we increment the current index
        # pointer to point to the next available interval.
        cii = cii + 1

        # Do a sanity check. We don't expect to ever need more than numIntervals
        # intervals. However, double check that we have not gone out of bounds.
        if cii >= numIntervals:
            raise RuntimeError("Unexpectedly required more than numIntervals intervals during downsample buiding.")

        # Set the time for the interval
        intervals[cii][0] = leftboundary + (timePerInterval / 2)

        # Prime this interval's min & max with the first data point
        intervals[cii][1] = rawValues[cdpi]
        intervals[cii][2] = rawValues[cdpi]

        # While the next data point occurs within the current interval, add
        # it to the interval's statistics.
        while cdpi < numDataPoints and rawOffsets[cdpi] < rightboundary:

            # Update interval's min & max based on the new data point
            if intervals[cii][1] > rawOffsets[cdpi]:
                intervals[cii][1] = rawOffsets[cdpi]
            if intervals[cii][2] < rawOffsets[cdpi]:
                intervals[cii][2] = rawOffsets[cdpi]

            # Increment cdpi to progress to the next data point
            cdpi = cdpi + 1

    # Slice off the unused intervals
    intervals = intervals[:cii+1]

    # Return the downsampled intervals
    return intervals

def numDownsamplesToBuild(np.ndarray[np.float64_t, ndim=1] rawOffsets, int M, int stepMultiplier):

    # Grab the rawOffsets length
    cdef int numDataPoints = rawOffsets.shape[0]

    # Calculate the timespan of the entire dataset
    cdef double timespan = rawOffsets[rawOffsets.shape[0]-1] - rawOffsets[0]

    # If we have fewer than or equal to 2M data points, no downsamples need to
    # be built and we can return immediately.
    if numDataPoints <= 2*M:
        return 0

    # The first & last variables track the sliding window of 2M data points.
    cdef int first = 0
    cdef int last = 2*M-1

    # The currentTimeWindow variable will track the time window of the current
    # sliding window of 2M data points. The smallestTimeWindow will, after
    # the while loop completes, hold the smallest time window of any consecutive
    # 2M data points in the data set, and it is primed with the first window.
    cdef double currentTimeWindow
    cdef double smallestTimeWindow = rawOffsets[last] - rawOffsets[first]

    # Determine the smallest time window of 2M data points
    while last < numDataPoints:

        # Calculate the time window of the current window of 2M data points
        currentTimeWindow = rawOffsets[last] - rawOffsets[first]

        # Update smallest time window if applicable
        if currentTimeWindow < smallestTimeWindow:
            smallestTimeWindow = currentTimeWindow

        # Increment first & last pointers
        first = first + 1
        last = last + 1

    # Calculate the time-per-interval for a downsample to represeent the
    # smallest time window in the data set. This will represent the floor
    # time-per-interval that the downsample reach (by floor is meant it should
    # not actually reach it).
    cdef double floorTimePerInterval = smallestTimeWindow / M

    # Holds our return value, the number of downsamples to build
    cdef int numDownsamplesToBuild = 0

    # Starting with the outermost zoom level at M points, iterate through and
    # add to the number downsample levels that should be built. The
    # timespan/currentNumDownsamples represents the time-per-interval for the
    # current number of downsamples, so we stop once that reaches at or below
    # floorTimePerInterval.
    cdef int currentNumDownsamples = M
    while timespan/currentNumDownsamples > floorTimePerInterval:
        numDownsamplesToBuild = numDownsamplesToBuild + 1
        currentNumDownsamples = currentNumDownsamples * stepMultiplier

    # Return the downsample levels to build.
    return numDownsamplesToBuild