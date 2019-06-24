import h5py
import pickle
import config
from series import Series
import time

# Simplejson package is required in order to "ignore" NaN values and implicitly
# convert them into null values. RFC JSON spec left out NaN values, even though
# ES5 supports them (https://www.ecma-international.org/ecma-262/5.1/#sec-4.3.23).
# By default, Python "json" module will allow & json-encode NaN values, but the
# Chrome JS engine will throw an error when trying to parse them. Simplejson
# package, with ignore_nan=True, will implicitly convert NaN values into null
# values. Find "ignore_nan" here: https://simplejson.readthedocs.io/en/latest/
import simplejson as json

# File represents a single patient data file.
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

    # Produces JSON output for all series in the file at the maximum time range.
    def getFullOutputAllSeries(self):

        outputObject = {}

        for s in self.numericSeries:

            outputObject[s.name] = s.getFullOutputAllSeries()

        return json.dumps(outputObject, ignore_nan = True)

    # Produces JSON output for all series in the file at a specified time range.
    def getRangedOutputAllSeries(self, start, stop):

        outputObject = {}

        for s in self.numericSeries:

            outputObject[s.name] = s.getRangedOutput(start, stop)

        return json.dumps(outputObject, ignore_nan = True)

    # Produces JSON output for a given series in the file at a specified
    # time range.
    def getRangedOutputSingleSeries(selfself, series, start, stop):

        outputObject = {}

        for s in self.numericSeries:

            if s.name == series:

                outputObject[s.name] = s.getRangedOutput(start, stop)

        return json.dumps(outputObject, ignore_nan = True)

    # Opens the HDF5 file.
    def loadFile(self):

        # Open the HDF5 file
        self.f = h5py.File(config.originalFilesDir+self.filename, 'r')

    # Pickles the class instance to a file named [filename].pkl. To pickle
    # itself, an instance will remove its self.f file reference because the
    # the h5py file objects cannot be pickled/unpickled.
    def pickle(self):

        print("Pickling " + self.filename + " for later use.")

        # Remove the file reference
        self.f = None

        # Pickle this object
        with open(config.scratchFilesDir+self.filename+'.alt.new.pkl', 'wb') as f:
            pickle.dump(self, f)

        print("Done pickling.")

    # Prepare a specific series by both pulling the raw data into memory and
    # producing & storing in memory all necessary downsamples. Type is either
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

        print("Finished preparing series " + name + ".")

    # Prepare all numeric series by both pulling the raw data into memory and
    # producing & storing in memory all necessary downsamples.
    def prepareAllNumericSeries(self):

        start = time.time()

        print("Preparing all numeric series for file.")

        for s in self.f['numeric']:
            self.prepareSeries('numeric', s)

        end = time.time()
        print("Completed preparing all numeric series for file (took " + str(round((end-start)/60, 3)) + " minutes).")

    # Prepare all waveform series by both pulling the raw data into memory and
    # producing & storing in memory all necessary downsamples.
    def prepareAllWaveformSeries(self):

        start = time.time()

        print("Preparing all waveform series for file.")

        for s in self.f['waveform']:
            self.prepareSeries('waveform', s)

        end = time.time()
        print("Completed preparing all waveform series for file (took " + str(round((end-start)/60, 3)) + " minutes).")

    # Attempts to unpickle the pickle file for filename, and returns the
    # unpickled object if successful.
    @staticmethod
    def unpickle(filename):

        try:

            # Unpickle this object
            print("Unpickling " + config.scratchFilesDir+filename+'.pkl')
            with open(config.scratchFilesDir+filename+'.pkl', 'rb') as f:
                obj = pickle.load(f)

            # Reopen the HDF5 file
            obj.loadFile()

            # Return the object
            print("Unpickling successful.")
            return obj

        except:

            print("Unpickling failed.")
            return
