import datetime as dt
import h5py

# Max number of data points to transmit for a given view
M = 1000

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

        # We've primted the interval with the first data point, so the count
        # starts at 1
        self.count = 1

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

def downsample(datagroup):

    # We assume datagroup has two non-empty datasets, "datetime" and "value".
    if len(datagroup['datetime']) < 1 or len(datagroup['value']) < 1:
        return

    # We assume the two datasets are of equal length
    if len(datagroup['datetime']) != len(datagroup['value']):
        return

    # The datetime values are offsets, in seconds, from a baseline datetime.
    # This is set as a global variable for now but should be changed later.
    global baseline
    baseline = dt.datetime.strptime(datagroup['datetime'].attrs['time_reference'], '%Y-%m-%d %H:%M:%S.%f %z')

    # Grab the first and last timestamps as datetime types
    startTime = baseline + dt.timedelta(0, datagroup['datetime'][0])
    stopTime = baseline + dt.timedelta(0, datagroup['datetime'][len(datagroup['datetime'])-1])

    # Calculate the time difference
    timespan = stopTime - startTime

    # Calculate the interval size
    timePerInterval = timespan / M

    # Holds the downsampled intervals to be returned
    intervals = []

    # Establish our initial boundaries for the first interval
    leftBoundary = startTime
    rightBoundary = startTime + timePerInterval

    # Holds count of how many intervals we've created or bypassed. Used to track
    # when we've hit n==M intervals.
    n = 0

    # Holds the current index we're pointing to in the data arrays
    i = 0

    # Holds the array length we're iterating to
    arrlen = len(datagroup['datetime'])

    # For all data points
    while i < arrlen:

        # While the next data point does not belong to the current interval,
        # progress to the next interval. If we reach the n==M'th interval,
        # we've completed our work, so return the function.
        while (baseline + dt.timedelta(0, datagroup['datetime'][i])) >= rightBoundary:

            # Update left & right boundaries to the next interval
            leftBoundary = rightBoundary
            rightBoundary = leftBoundary + timePerInterval

            # We've passed into the next interval, so increment n
            n = n+1

            # By the time we've reached n==M, we've already created M intervals,
            # and the work is almost complete.
            #
            # We expect to reach n==M intervals with one data point left
            # unaccounted for (i==arrlen-1). The reason for this is that the
            # right interval boundary is non-inclusive, and yet we predetermined
            # that the right boundary of the last interval (stopTime) would
            # equal time of the last data point. For this reason, we must add
            # the last data point to our last interval before returning.
            if n >= M:

                # Validate our expected conditions
                if n == M and i == arrlen-1:

                    # Add the final data point to the last interval (see above)
                    intervals[len(intervals)-1].addDataPoint(datagroup['value'][i])

                else:

                    # Print an error
                    print("There has been an error. Expected n==M and i==arrlen-1, but got n="+str(n)+" and i="+str(i)+" with arrlen="+str(arrlen))

                #Return the prepared intervals
                return intervals

        # Having reached this point, we have reached an interval to which the
        # next data point belongs but have not reached n==M, so we should create
        # a new interval.
        intervals.append(Interval(datagroup['value'][i], leftBoundary + (timePerInterval/2)))

        # While the next data point occurs within the current interval, add it
        # to the interval's statistics.
        while (baseline + dt.timedelta(0, datagroup['datetime'][i])) < rightBoundary and i < arrlen:

            # Add the data point to the interval
            intervals[len(intervals)-1].addDataPoint(datagroup['value'][i])

            # Increment i to process the next data point
            i = i+1

    # We don't expect to reach this point; we expect the function to return
    # within the while loop. So if we reach this point, output an error.
    print("There has been an error. Exited the data processing loop without returning.")
