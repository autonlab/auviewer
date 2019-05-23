import datetime as dt
import h5py

# Max number of data points to transmit for a given view
M = 1000

# Interval defines a data summary interval for downsampling
class Interval:
    min = 0
    max = 0
    count = 0
    # time

    # Constructor accepts one parameter, firstvalue, which will be assigned
    # to min & max initially.
    def __init__(self, firstvalue, time):
        self.min = firstvalue
        self.max = firstvalue
        self.time = time

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

    while i < arrlen:

        # While the next data point does not belong to the current interval,
        # proceed to the next interval. If we reach n==M, we've completed our
        # work, so return the function.
        while (baseline + dt.timedelta(0, datagroup['datetime'][i])) >= rightBoundary:

            # Update left & right boundaries to the next interval
            leftBoundary = rightBoundary
            rightBoundary = leftBoundary + timePerInterval

            # We've passed into the next interval, so increment n
            n = n+1

            # By the time we've reached n==M, we've already created M interval,
            # and the work is complete. So return the intervals array.
            if n >= M:
                print("Hmm, interesting... we reached n==M before processing all data points.")
                print("Data points left (arrlen-i): ("+arrlen+"-"+i+"): "+(arrlen-i))
                print("Increments left (M-n): ("+M+"-"+n+"): "+(M-n))
                return intervals

        # Having reached this point, we have reached an interval to which the
        # next data point belongs but have not reached n==M, so we should create
        # a new interval.
        intervals.append(Interval(datagroup['value'][i], baseline + dt.timedelta(0, datagroup['datetime'][i])))

        # While the next data point occurs within the current interval, add it
        # to the interval's statistics.
        while (baseline + dt.timedelta(0, datagroup['datetime'][i])) < rightBoundary and i < arrlen:

            if datagroup['value'][i] > intervals[len(intervals)-1].max:
                intervals[len(intervals)-1].max = datagroup['value'][i]

            if datagroup['value'][i] < intervals[len(intervals)-1].min:
                intervals[len(intervals)-1].min = datagroup['value'][i]

            intervals[len(intervals)-1].count = intervals[len(intervals)-1].count + 1

            i = i+1

    # Having reached this point, we've processed all data points, so return.
    print("Returning normally.")
    print("Data points left (arrlen-i): ("+arrlen+"-"+i+"): "+(arrlen-i))
    print("Increments left (M-n): ("+M+"-"+n+"): "+(M-n))
    return intervals
