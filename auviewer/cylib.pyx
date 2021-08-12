#!python
#cython: boundscheck=False
#cython: wraparound=False
#cython: cdivision=True

import logging
import numpy as np
cimport numpy as np
from libc.math cimport floor

# Given an already-built downsample, this function builds the next downsample up.
# It bases the "next downsample up" on the time-per-interval of the original
# downsample and the step multiplier provided. For example, if the original
# time-per-interval is 5s and the step multiplier is 3, the new downsample will
# have a time-per-interval of 5*3=15s.
def buildNextDownsampleUp(np.ndarray[np.float64_t, ndim=2] intervalsOrig, double timePerIntervalOrig, int stepMultiplier):

    # Get the number of intervals in the original downsample.
    cdef int numIntervalsOrig = intervalsOrig.shape[0]

    # Do a sanity check
    if numIntervalsOrig < stepMultiplier:
        return

    # Will hold our new downsample. We allocate the worst-case number of
    # intervals needed for the new downsample, which would be equal to the
    # original downsample (for example, if each interval of the original
    # downsample were separated from the other by at least
    # timePerIntervalOrig * stepMultiplier.
    cdef np.ndarray[np.float64_t, ndim=2] intervalsNew = np.zeros((numIntervalsOrig, 3))

    # Determine the new time-per-interval
    cdef double timePerIntervalNew = timePerIntervalOrig*stepMultiplier

    # This is the base offset, or essentially the time offset of the original
    # first raw data point in the series.
    cdef double baseOffset = intervalsOrig[0,0] - (timePerIntervalOrig / 2)

    # Will track the stepwise left & right boundary of the new intervals
    cdef double leftboundaryNew = baseOffset
    cdef double rightboundaryNew = leftboundaryNew + timePerIntervalNew

    # Holds the index of the current original interval we're working on.
    cdef int cio = 0

    # Holds the index of the current new interval we're working on. We start at
    # -1 because the loop will increment the index the first time it runs in
    # order to point to the "first" interval.
    cdef int cin = -1

    # Temporary-use iterator to be used below
    cdef int i

    while cio < numIntervalsOrig:

        # If this original interval does not belong to the current new interval
        # boundaries, compute the subsequent new interval boundaries to which
        # it belongs.
        if intervalsOrig[cio,0] >= rightboundaryNew:

            leftboundaryNew = floor( (intervalsOrig[cio,0]-baseOffset) / timePerIntervalNew) * timePerIntervalNew + baseOffset
            rightboundaryNew = leftboundaryNew + timePerIntervalNew

            # NOTE: We do not progress cin because we have simply skipped an
            # empty interval, and we do not store/represent empty intervals.

        # The above code block (if statement) calculates precisely which
        # interval window the data point is a member of. However, in the case of
        # very small intervals (e.g. if a data series has dense data and
        # requires downsampling using high floating point precision), there may
        # be floating point rounding which mucks things up and the data point
        # actually belongs to an adjacent interval. This is a heuristic to
        # account for such a possibility. The while loop criterion matches what
        # is used in the while loop below, so we avoid an infinite loop
        # situation in case there is a rounding error as described.
        #
        # NOTE: For some reason, the while loop (C addition) will use 15 places
        # past the decimal for the exponent, but the computation in the if
        # statement above only uses 12. In testing, the below while loop is used
        # not infrequently for dense data sets (e.g. waveforms at 500 Hz). It
        # has been observed to be used frequently for the downsample with the
        # smallest interval and for 4-5 data points in waveform data sets in the
        # 270-330MM data points range.
        while intervalsOrig[cio,0] >= rightboundaryNew:

            logging.info("Using the while heuristic for data point " + str(intervalsOrig[cio,0]))

            # Update left & right boundaries to the next interval
            leftboundaryNew = rightboundaryNew
            rightboundaryNew = leftboundaryNew + timePerIntervalNew

        # Increment the current index pointer to the next available interval.
        cin = cin + 1

        # Do a sanity check and double check that we have not gone out of bounds.
        if cin >= numIntervalsOrig:
            raise RuntimeError("Unexpectedly require more than numIntervalsOrig during downsample building from downsample.")

        # Prime the min & max of the new interval to the first original interval
        intervalsNew[cin,1] = intervalsOrig[cio,1]
        intervalsNew[cin,2] = intervalsOrig[cio,2]

        i = 0
        while cio < numIntervalsOrig and i < stepMultiplier and intervalsOrig[cio,0] < rightboundaryNew:

            # Update min & max
            if intervalsOrig[cio,1] < intervalsNew[cin,1]:
                intervalsNew[cin,1] = intervalsOrig[cio,1]
            if intervalsOrig[cio,2] > intervalsNew[cin,2]:
                intervalsNew[cin,2] = intervalsOrig[cio,2]

            # Add the time offset (it will be divided by i at the
            # end to yield the average time offset for the new interval
            intervalsNew[cin,0] = intervalsNew[cin,0] + intervalsOrig[cio,0]

            cio = cio + 1
            i = i + 1

        # Divide the time offset for the new interval by i to yield the
        # average time offset of the original intervals represented.
        intervalsNew[cin,0] = intervalsNew[cin,0] / i

    # Slice off the unused intervals
    intervalsNew = intervalsNew[:cin+1]

    # Return the new downsample intervals
    return intervalsNew

# Given a series of raw values and a time-per-interval parameter, produces and
# returns a two-dimension NumPy array of downsample intervals
def buildDownsampleFromRaw(np.ndarray[np.float64_t, ndim=1] rawOffsets, np.ndarray[np.float64_t, ndim=1] rawValues, int numIntervals):

    # Calculate the timespan of the entire dataset
    cdef double timespan = rawOffsets[rawOffsets.shape[0]-1] - rawOffsets[0]

    # Calculate the interval size in seconds
    cdef double timePerInterval = timespan / numIntervals

    # TODO(gus): FIX THIS BS!
    origNumIntervals = numIntervals
    numIntervals = numIntervals + 1

    # Allocate the maximum number of intervals needed (excess will be sliced off
    # at the end). The two-dimensional array will have 3 columns and numIntervals
    # rows. The columns, in order, will be: Time Offset, Min, Max, # Points.
    cdef np.ndarray[np.float64_t, ndim=2] intervals = np.zeros((numIntervals, 3))

    # This is the base offset, or the time offset of the first data point.
    cdef double baseOffset = rawOffsets[0]

    # Establish our initial boundaries for the first interval
    cdef double leftboundary = baseOffset
    cdef double rightboundary = leftboundary + timePerInterval

    # Grab data points length so we don't have to look it up every time.
    cdef int numDataPoints = rawOffsets.shape[0]

    # Holds the index of the current data point we're working on.
    cdef int cdpi = 0

    # Holds the index of the current interval we're working on. We start at -1
    # because the loop will increment the index the first time it runs in order
    # to point to the "first" interval.
    cdef int cii = -1

    cdef double leftboundaryORIG, rightboundaryORIG, leftboundaryIF, rightboundaryIF, leftboundaryWHILE, rightboundaryWHILE

    # For all data points
    while cdpi < numDataPoints:

        # If the next data point does not belong to the current interval
        # boundaries, compute the next interval boundaries to which it belongs.
        if rawOffsets[cdpi] >= rightboundary:

            # Compute the left & right boundaries for the new interval.
            leftboundary = floor( (rawOffsets[cdpi]-baseOffset) / timePerInterval) * timePerInterval + baseOffset
            rightboundary = leftboundary + timePerInterval

            # NOTE: We do not progress cii because we have simply skipped an
            # empty interval, and we do not store/represent empty intervals.

        # The above code block (if statement) calculates precisely which
        # interval window the data point is a member of. However, in the case of
        # very small intervals (e.g. if a data series has dense data and
        # requires downsampling using high floating point precision), there may
        # be floating point rounding which mucks things up and the data point
        # actually belongs to an adjacent interval. This is a heuristic to
        # account for such a possibility. The while loop criterion matches what
        # is used in the while loop below, so we avoid an infinite loop
        # situation in case there is a rounding error as described.
        #
        # NOTE: For some reason, the while loop (C addition) will use 15 places
        # past the decimal for the exponent, but the computation in the if
        # statement above only uses 12. In testing, the below while loop is used
        # not infrequently for dense data sets (e.g. waveforms at 500 Hz). It
        # has been observed to be used frequently for the downsample with the
        # smallest interval and for 4-5 data points in waveform data sets in the
        # 270-330MM data points range.
        while rawOffsets[cdpi] >= rightboundary:

            #print("Using the while heuristic for data point " + str(rawOffsets[cdpi]))

            # Update left & right boundaries to the next interval
            leftboundary = rightboundary
            rightboundary = leftboundary + timePerInterval

        # Increment the current index pointer to the next available interval.
        cii = cii + 1

        # Do a sanity check. We don't expect to ever need more than numIntervals
        # intervals. However, double check that we have not gone out of bounds.
        if cii >= numIntervals:
            raise RuntimeError("Unexpectedly required more than numIntervals intervals during downsample building from raw. numIntervals: "+str(numIntervals)+", cii: "+str(cii)+", leftboundary: "+str(leftboundary)+", rightboundary: "+str(rightboundary)+", cdpi: "+str(cdpi)+", numDataPoints: "+str(numDataPoints)+", rawOffsets[cdpi]: "+str(rawOffsets[cdpi])+", rawValues[cdpi]: "+str(rawValues[cdpi]))

        # Set the time for the interval
        intervals[cii,0] = leftboundary + (timePerInterval / 2)

        # Prime this interval's min & max with the first data point
        intervals[cii,1] = rawValues[cdpi]
        intervals[cii,2] = rawValues[cdpi]

        # While the next data point occurs within the current interval, add
        # it to the interval's statistics.
        while cdpi < numDataPoints and rawOffsets[cdpi] < rightboundary:

            # Update interval's min & max based on the new data point
            if intervals[cii,1] > rawValues[cdpi]:
                intervals[cii,1] = rawValues[cdpi]
            if intervals[cii,2] < rawValues[cdpi]:
                intervals[cii,2] = rawValues[cdpi]

            # Increment cdpi to progress to the next data point
            cdpi = cdpi + 1

    # TODO(gus): TEMP
    if cii >= origNumIntervals:
        # TODO(gus): I've made this an error because it's not relevant for users,
        # but this should be watched when next working on downsampling.
        logging.info("Exceeded numIntervals! origNumIntervals: "+str(origNumIntervals)+", numIntervals: "+str(numIntervals)+", timePerInterval: "+str(timePerInterval)+", cii: "+str(cii)+", leftboundary: "+str(leftboundary)+", rightboundary: "+str(rightboundary)+", cdpi: "+str(cdpi)+", numDataPoints: "+str(numDataPoints)+", rawOffsets[cdpi]: "+str(rawOffsets[cdpi])+", rawValues[cdpi]: "+str(rawValues[cdpi]))

    # Slice off the unused intervals
    intervals = intervals[:cii+1]

    # Return the downsampled intervals
    return intervals

# Generates a two-dimensional Nx2 alerts array, with N alerts in the first
# dimension and each alert having a start time in the first array element and a
# stop time in the second. A low threshold, a high threshold, or both may be
# provided for alert generation. The mode parameter specifies which of these is
# provided, with 0 indicating low threshold, 1 indicating high threshold, and 2
# indicating both being provided. This may not be inferred from the threshold
# parameter values themselves because no real number is out-of-bounds. The
# duration is in the same units as the start times (e.g. if start time is in
# seconds, duration is in seconds). The min_sample_count, if greater than 0, is
# used to filter out alerts which have fewer than min_sample_count values within
# the duration timespan.
def generateThresholdAlerts(np.ndarray[np.float64_t, ndim=1] rawOffsets, np.ndarray[np.float64_t, ndim=1] rawValues, double thresholdlow, double thresholdhigh, int mode, double duration, double persistence, double maxgap, int min_sample_count):

    # Holds the indices of all raw values which surpass the threshold(s)
    cdef np.ndarray[long, ndim=1] pastThresholdIndices

    # Pull the indices of all data points that exceed the threshold.
    # TODO(gus): Is there a more efficient way to do this?
    if mode == 0:
        pastThresholdIndices = np.nonzero((rawValues < thresholdlow))[0]
    elif mode == 1:
        pastThresholdIndices = np.nonzero((rawValues > thresholdhigh))[0]
    elif mode == 2:
        pastThresholdIndices = np.nonzero((rawValues < thresholdlow) | (rawValues > thresholdhigh))[0]
    else:
        logging.error("Invalid mode parameter provided to generateThresholdAlerts.")
        return np.array([])

    # Holds generated alerts (start & stop time offsets). We assume there can be
    # a max of len(pastThresholdIndices) alerts and slice it shorter at the end.
    cdef np.ndarray[np.float64_t, ndim=2] alerts = np.zeros((pastThresholdIndices.shape[0], 2))

    # Holds the index of the current data point we're working on
    cdef long cdpi = 0

    # Holds the index of the next available unwritten alert
    cdef long nuai = 0

    # Tracks the left & right boundaries of the current alert sample
    cdef double leftboundary, rightboundary

    # Tracks the number of points that exceed the threshold and the total number
    # of sample points for calculation of the sample persistence.
    cdef long numexceed, numtotal

    # Holds the sample persistence once calculated
    cdef double sampleduty

    for alertSampleBeginIndex in pastThresholdIndices:

        cdpi = alertSampleBeginIndex
        leftboundary = rawOffsets[cdpi]
        rightboundary = leftboundary + duration

        # Reset sample persistence statistics
        numexceed = 0
        numtotal = 0

        # Iterate through raw data indices until we hit the raw data bound or
        # hit the right time boundary for this current alert.
        while cdpi < rawOffsets.shape[0] and rawOffsets[cdpi] < rightboundary:

            # Increment the number of total data points
            numtotal = numtotal + 1

            # If this data point exceeds the threshold, increment the number of
            # threshold-exceed data points.
            if (mode == 0 and rawValues[cdpi] < thresholdlow) or \
                (mode == 1 and rawValues[cdpi] > thresholdhigh) or \
                (mode == 2 and (rawValues[cdpi] < thresholdlow or rawValues[cdpi] > thresholdhigh)):
                numexceed = numexceed + 1

            # Increment to the next data point
            cdpi = cdpi + 1

        # Calculate the sample persistence
        sampleduty = <double>numexceed / <double>numtotal

        # If the persistence of the sample exceeds the minimum to qualify for an
        # alert, add this to our alerts.
        if sampleduty >= persistence and (cdpi-alertSampleBeginIndex) >= min_sample_count:

            alerts[nuai,0] = leftboundary
            alerts[nuai,1] = rawOffsets[cdpi-1]

            # Increment to the next available unwritten alert
            nuai = nuai + 1

    # Slice off unused alerts
    alerts = alerts[0:nuai]

    # Holds the final, consolidated alerts to be returned
    cdef np.ndarray[np.float64_t, ndim=2] finalalerts = np.zeros((alerts.shape[0], 2))

    # Holds the index of the current raw alert
    cdef long crai = 0

    # Holds the index of the current final alert
    cdef long cfai = 0

    # Holds start & stop times for a candidate final alert
    cdef double candalertbegin, candalertend

    # Handle the special case that there is only zero or one alert
    if len(alerts) <= 1:
        return alerts

    # Prime the while loop with the first alert as candidate alert
    candalertbegin = alerts[crai,0]
    candalertend = alerts[crai,1]
    crai = crai + 1

    while crai < len(alerts):

        # For each iteration, we either extend the candidate time and move on,
        # or write out the final alert and start a new candidate.

        # If the next alert is less than maxgap from the previous alert, extend
        # the alert window and move on
        if alerts[crai][0] <= candalertend + maxgap:
            candalertend = alerts[crai][1]

        # Otherwise, add the current candidate as a final alert and start a
        # new candidate.
        else:

            # Write the  candidate alert as a final alert
            finalalerts[cfai,0] = candalertbegin
            finalalerts[cfai,1] = candalertend
            cfai = cfai + 1

            # Start a new candidate
            candalertbegin = alerts[crai,0]
            candalertend = alerts[crai,1]

        # Increment to the next alert
        crai = crai + 1

    # Write the final unwritten candidate as a final alert.
    finalalerts[cfai,0] = candalertbegin
    finalalerts[cfai,1] = candalertend
    cfai = cfai + 1

    # Slice off the unused final alerts array elements
    finalalerts = finalalerts[0:cfai]

    return finalalerts

# Returns the index where a provided target value should be inserted in a
# downsample or raw data series. The side parameter indicates whether to
# approach from the left or right, where 0 indicates left and non-zero is right.
def getSliceParam(ds, timecol, unsigned short side, double target):

    cdef long numDataPoints = ds.nrow

    cdef int low = 0
    cdef int high = numDataPoints - 1

    # Will hold the midpoint index
    cdef int mid

    # Will be used later for iteration
    cdef int i

    while low <= high:

        mid = (low + high) / 2

        if target > ds[mid][timecol][0]:
            low = mid + 1
        elif target < ds[mid][timecol][0]:
            high = mid - 1
        else:

            i = mid

            # For left slice param, we want leftmost equal value index
            if side == 0:
                while i > 0 and ds[i][timecol][0] == target:
                    i = i - 1
                return i + 1

            # For right slice param, we want 1 + rightmost equal value index
            else:
                while i < numDataPoints and ds[i][timecol][0] == target:
                    i = i + 1
                return i

    return low

# This function calculates the number of downsample levels to build based on the
# value of M and stepMultiplier (see the config file for details on those). It
# calculates this by finding the smallest timespan of any consecutive 2M points
# in the data series (the densest window of 2M points) and determining the
# number of downsample levels that approach but do not exceed that threshold.
#
# To illustrate how the function response may be used, take the example of
# M=3000 and stepMultiplier=2, and assume the return value is 7. In this case,
# the following downsamples should be built: 3000, 6000, 12000, 24000, 48000,
# 96000, 192000.
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

    # If all values are at the same point in time and, having passed the if statement above, there are > 2*M data points,
    # we cannot downsample the file.
    if smallestTimeWindow == 0:
        raise Exception('All values are at the same point in time. Cannot downsample.')
    elif smallestTimeWindow < 0:
        raise Exception('Series violates assumption of monotonically increasing time values (i.e. series should be ordered in time).')

    # Determine the smallest time window of 2M data points
    while last < numDataPoints:

        # Calculate the time window of the current window of 2M data points
        currentTimeWindow = rawOffsets[last] - rawOffsets[first]

        # Update smallest time window if applicable
        if currentTimeWindow < smallestTimeWindow and currentTimeWindow > 0:
            smallestTimeWindow = currentTimeWindow

        if currentTimeWindow < 0:
            raise Exception('Series violates assumption of monotonically increasing time values (i.e. series should be ordered in time).')

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
