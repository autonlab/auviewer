#!python
#cython: boundscheck=False
#cython: wraparound=False

import numpy as np
cimport numpy as np

# Given a series of raw values and a time-per-interval parameter, produces and
# returns a two-dimension NumPy array of downsample intervals
def buildDownsample(np.ndarray[np.float64_t, ndim=1] rawOffsets, np.ndarray[np.float64_t, ndim=1] rawValues, double timePerInterval):

    # Calculate the maximum number of intervals needed
    cdef int numIntervals = <int>((rawOffsets[rawOffsets.shape[0]-1] - rawOffsets[0]) / timePerInterval + 2)

    # Allocate the maximum number of intervals needed (excess will be sliced off
    # at the end). The two-dimensional array will have 3 columns and numIntervals
    # rows. The columns, in order, will be: Time Offset, Min, Max, # Points.
    cdef np.ndarray[np.float64_t, ndim=2] intervals = np.zeros((numIntervals, 4))

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

            # Add 1 to the number of data points represented by this interval.
            intervals[cii][3] = intervals[cii][3] + 1

            # Increment cdpi to progress to the next data point
            cdpi = cdpi + 1

    # Slice off the unused intervals
    intervals = intervals[:cii+1]

    # Return the downsampled intervals
    return intervals

# Determines whether a downsample has reached the threshold where it should be
# kept, or, more specifically, where any window of M consecutive intervals in
# the downsample represents at least 2*M data points.
def wasThresholdReached(np.ndarray[np.float64_t, ndim=2] intervals, double timePerInterval, int N, int M):

    # We begin with heuristic that will let us avoid the expensive computation
    # of a full threshold check for the earlier downsamples. The heuristic is
    # follows.
    #
    # Terms:
    #
    # M =        Max number of data points we wish to transmit. For downsamples,
    #            each interval counts as two data points since min & max are
    #            transmitted.
    # N =        Number of raw values in the data set.
    # I =        Number of intervals kept in the downsample, or, in other words,
    #            the number of non-empty intervals in a downsample.
    # DDW =      Densest data window, or the densest number of data points
    #            represented in any window of M intervals within an entire
    #            downsample.
    # DDW(min) = The minimum value of DDW for a given downsample, computed by
    #            our heuristic.
    #
    # Assertion: DDW(min) = N/I*M
    #
    # Heuristic: If DDW(min) >= 2M, then we do not need to perform the full
    #            trailing summary threshold test because we have already proven
    #            the threshold has been met (DDW >= 2M).
    #
    # Reasoning: The reason the assertion is valid is the following. We know
    #            that each interval represents some number of raw data points,
    #            and we know that an entire set of downsample intervals I will
    #            represent all N data points. So, for a given downsample, the
    #            minimum DDW would be in the case that the data points are
    #            represnted evenly across the set of intervals (or, in other
    #            words, where each interval represents N/I data points). This
    #            leads us to establish our assertion that DDW(min) = N/I*M.
    #
    # Credit:    Credit to Jim Leonard for first suggesting the heuristic.

    # Calculate DDW(min) for our heuristic
    cdef int ddwMin = N/intervals.shape[0]*M

    # Check if the heuristic shows DDW(min) >= 2M, and if so we can return now.
    if ddwMin >= 2*M:
        return True

    # If the heuristic did not prove true, we must calculate the maximum
    # trailing summary of M * timePerInterval seconds.

    # Let's begin by calculating our sliding time window
    cdef double timeWindow = M * timePerInterval

    # Let's establish two index pointers, one to the first element and one to
    # last element in the sliding window. We start both pointers at index 0.
    cdef int firstIntervalInWindow = 0
    cdef int lastIntervalInWindow = 0

    # Grab the size of the intervals array
    cdef int numIntervals = intervals.shape[0]

    # Will hold the number of data points represented by a given sliding window
    cdef int numPointsRepresented = 0

    # Calculate twice M so we don't need to calculate each time within the loop.
    cdef int twoM = 2*M

    # Here begins our sliding window test, where each iteration tests one window.
    while lastIntervalInWindow < numIntervals:

        # First, see if we need to move up the first interval in the window
        while intervals[lastIntervalInWindow][0] - intervals[firstIntervalInWindow][0] > timeWindow:

            # Remove the interval's points represented
            numPointsRepresented = numPointsRepresented - intervals[firstIntervalInWindow][3]

            # Increment the first interval index
            firstIntervalInWindow = firstIntervalInWindow + 1

        # Add the data points represented by the new interval
        numPointsRepresented = numPointsRepresented + intervals[lastIntervalInWindow][3]

        # If we reach the threshold, return true
        if numPointsRepresented >= twoM:
            return True

        # Increment the last interval index pointer to proceed to the next window.
        lastIntervalInWindow = lastIntervalInWindow + 1

    # Having reached this point, we did not reach the threshold, so return false.
    return False

def whatDownsamplesToBuild(np.ndarray[np.float64_t, ndim=1] rawOffsets, int M):

    # Grab the rawOffsets length
    cdef int numDataPoints = rawOffsets.shape[0]

    # Calculate the timespan of the entire dataset
    cdef double timespan = rawOffsets[rawOffsets.shape[0]-1] - rawOffsets[0]

    # Will hold the return array of downsample levels to build (each element
    # is the number of intervals which the timespan should be divided into).
    cdef np.ndarray[np.int64_t, ndim=1] downsampleLevelsToBuild = np.empty((0), dtype=np.int64)

    # If we have fewer than 2M data points, no downsamples need to be built and
    # we can return immediately.
    if numDataPoints < 2*M:
        return downsampleLevelsToBuild

    # The first & last variables track the sliding window of 2M data points.
    cdef int first = 0
    cdef int last = 2*M-1

    # The currentTimeWindow variable will track the time window of the current
    # sliding window of 2M data points. The smallestTimeWindow will, after
    # the while loop completes, hold the smallest time window of any consecutive
    # 2M data points in the data set, and it is primed with the first window.
    cdef double currentTimeWindow
    cdef double smallestTimeWindow = rawOffsets[last] - rawOffsets[first]

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

    # Starting with the outermost zoom level at M points, iterate through and
    # build the array of downsample levels that should be built. The
    # timespan/currentNumDownsamples represents the time-per-interval for the
    # current number of downsamples, so we stop once that reaches at or below
    # floorTimePerInterval.
    cdef int currentNumDownsamples = M
    cdef double currentTimePerInterval
    while timespan/currentNumDownsamples > floorTimePerInterval:
        downsampleLevelsToBuild = np.append(downsampleLevelsToBuild, currentNumDownsamples)
        currentNumDownsamples = currentNumDownsamples * 2

    # Return the downsample levels to build.
    return downsampleLevelsToBuild