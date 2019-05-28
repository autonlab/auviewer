import bisect
import datetime as dt
import downsample
import h5py
import pickle

# Simplejson package is required in order to "ignore" NaN values and implicitly convert them into null values.
# RFC JSON spec left out NaN values, even though ES5 supports them (https://www.ecma-international.org/ecma-262/5.1/#sec-4.3.23).
# By default, Python "json" module will allow & json-encode NaN values, but the Chrome JS engine will throw an error when trying to parse them.
# Simplejson package, with ignore_nan=True, will implicitly convert NaN values into null values.
# Find "ignore_nan" here: https://simplejson.readthedocs.io/en/latest/
import simplejson as json

class File:

    # Version is used to make upgrades to pickled class instances when necessary.
    # See: http://code.activestate.com/recipes/521901-upgradable-pickles/
    version = 0.1

    def __init__(self, filename):

        # Holds the filename
        self.filename = filename

        # Will hold the numeric series from the file
        self.numericSeries = []

        # Will hold the waveform series from the file
        self.waveformSeries = []

        # Load the file
        self.loadFile()

    def getRangedOutput(self, start, stop):

        outputObject = {}

        for s in self.numericSeries:

            outputObject[s.name] = s.getRangedOutput(start, stop)

        return json.dumps(outputObject, ignore_nan = True)

    # Returns full JSON output for all series in the file.
    def getFullOutput(self):

        outputObject = {}

        for s in self.numericSeries:

            outputObject[s.name] = s.getFullOutput()

        return json.dumps(outputObject, ignore_nan = True)

    # Loads the HDF5 file
    def loadFile(self):

        # Open the HDF5 file
        self.f = h5py.File(self.filename, 'r')

    # Pickles the class instance to a file named [filename].pkl. To pickle
    # itself, an instance will remove its self.f file reference because the
    # the h5py file objects cannot be pickled/unpickled.
    def pickle(self):

        # Remove the file reference
        self.f = None

        # Pickle this object
        with open(self.filename+'.pkl', 'wb') as f:
            pickle.dump(self, f)

    # Reads a series into memory and processes downsampling. Type is either
    # 'numeric' or 'waveform'.
    def prepareSeries(self, type, name):

        print('Preparing series ' + name + '.')

        # Check if the series already exists
        if type == 'numeric':
            for s in self.numericSeries:
                if s.name == name:
                    print('Aborting series preparation because series already exists.')
                    return
        elif type == 'waveform':
            for s in self.waveformSeries:
                if s.name == name:
                    print('Aborting series preparation because series already exists.')
                    return

        # We expect type to be one of two values
        if type != 'numeric' and type != 'waveform':
            raise RuntimeError('Invalid type was provided to File.prepareSeries(): ' + str(type))

        # Prepare the series
        series = Series(type, name, self)

        # Add the series to the appropriate list
        if type == 'numeric':
            self.numericSeries.append(series)
        elif type == 'waveform':
            self.waveformSeries.append(series)

    def prepareAllNumericSeries(self):

        print("Preparing all numeric series for file.")

        for s in self.f['numeric']:
            self.prepareSeries('numeric', s)

    def prepareAllWaveformSeries(self):

        print("Preparing all waveform series for file.")

        for s in self.f['waveform']:
            self.prepareSeries('waveform', s)

    # Attempts to unpickle the pickle file for filename, and returns the
    # unpickled object if successful.
    @staticmethod
    def unpickle(filename):

        try:

            # Unpickle this object
            with open(filename+'.pkl', 'rb') as f:
                obj = pickle.load(f)

            # Reopen the HDF5 file
            obj.loadFile()

            # Return the object
            return obj

        except:

            return


class Series:

    # Reads a series into memory and builds the downsampling. Type is either
    # 'numeric' or 'waveform'. Fileparent is a reference to the File class
    # instance which contains the Series.
    def __init__(self, type, name, fileparent):

        # Holds the type
        self.type = type

        # Holds the series name
        self.name = name

        # Holds a reference to the file parent which contains the series
        self.fileparent = fileparent

        # Parse the basetime datetime, with timezone removed
        self.basetime = dt.datetime.strptime(self.getData()['datetime'].attrs['time_reference'], '%Y-%m-%d %H:%M:%S.%f %z').replace(tzinfo=None)

        # Holds the downsample set
        self.downsampleSet = downsample.DownsampleSet(self)

        # Pull raw data into memory
        self.pullRawData()

        # Build the downsample set
        self.downsampleSet.build()

    # Returns this series' dataset.
    def getData(self):

        return self.fileparent.f[self.type][self.name]['data']

    def getRangedOutput(self, starttime, stoptime):

        # Get the appropriate downsample for this time range
        ds = self.downsampleSet.getDownsample(starttime, stoptime)

        if ds:

            print("Assembling downsampled data for " + self.name + ".")

            # Get the intervals within this time range
            intervals = ds.getIntervals(starttime, stoptime)

            # Will hold the data points ready for output
            data = []

            # Assemble the data points
            for i in intervals:
                data.append([i.time.isoformat(), i.min, i.max, None])

            return {
                "labels": ['Date/Offset', 'Min', 'Max', self.name],
                "data": data
            }

        else:

            print("Assembling raw data for " + self.name + ".")

            # Determine the index of the first point to transmit for the view.
            # To do this, find the first point which occurs after the starttime
            # and take the index prior to that as the starting data point.
            startPointIndex = 0
            # i = 0
            # while i < len(self.rawDates) and (self.basetime + dt.timedelta(0, self.rawDates[i])) <= starttime:
            #     i = i + 1
            # startPointIndex = i - 1
            # if startPointIndex < 0:
            #     startPointIndex = 0
            # print("Old method start: " + str(startPointIndex))

            # Convert the start time into seconds offset from basetime
            startoffset = (starttime - self.basetime).total_seconds()

            startPointIndex = bisect.bisect(self.rawDates, startoffset) - 1
            if startPointIndex < 0:
                startPointIndex = 0

            print("Calculated start index at: " + str(startPointIndex))

            # Determine the index of the last point to transmit for the view. To
            # do this, find the first point which occurs after the stoptime and
            # take the index prior to that as the starting interval.
            # i = startPointIndex
            # while i < len(self.rawDates) and (self.basetime + dt.timedelta(0, self.rawDates[i])) <= stoptime:
            #     i = i + 1
            # stopPointIndex = i - 1
            # if stopPointIndex < 0:
            #     stopPointIndex = 0
            # print("Old method stop: "+str(stopPointIndex))

            # Convert the stop time into seconds offset from basetime
            stopoffset = (stoptime - self.basetime).total_seconds()

            stopPointIndex = bisect.bisect(self.rawDates, stopoffset) - 1
            if stopPointIndex < 0:
                stopPointIndex = 0

            print("Calculated start index at: " + str(stopPointIndex))

            # Will hold the data points ready for output
            data = []

            # Assemble the data points
            i = startPointIndex
            while i <= stopPointIndex:
                data.append([(self.basetime + dt.timedelta(0, self.rawDates[i])).isoformat(), None, None, self.rawValues[i]])
                i = i + 1

            print("Assembly complete for " + self.name + ".")

            return {
                "labels": ['Date/Offset', 'Min', 'Max', self.name],
                "data": data
            }

    def getFullOutput(self):

        # Will hold the data points ready for output
        data = []

        # Assemble the data points
        for i in self.downsampleSet.downsamples[0].intervals:
            data.append([i.time.isoformat(), i.min, i.max, None])

        return {
            "labels": ['Date/Offset', 'Min', 'Max', self.name],
            "data": data
        }

    def pullRawData(self):

        print("Reading raw series data into memory.")

        # Will hold the raw date values
        self.rawDates = []

        # Will hold the raw values
        self.rawValues = []

        # Get reference to the series datastream from the HDF5 file
        data = self.getData()

        # Iterate through the dates & values from the file, and copy them into
        # the object attributes.
        i = 0
        while i < len(data['datetime']):
            self.rawDates.append(data['datetime'][i])
            self.rawValues.append(data['value'][i])

            if i%50000==0:
                print(str(i))

            i = i + 1

        print("Finished reading raw series data into memory.")
