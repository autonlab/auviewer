import h5py
import config
import os.path
import os.remove
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

    def __init__(self, filename, path):

        # Holds the filename
        self.filename = filename

        # Holds the path of the file (not including filename)
        self.path = path

        # Holds the filename of the processed data file (may not exist yet)
        self.processedFilename = os.path.splitext(self.filename)[0] + '_processed.h5'

        # Holds the path of the processed data file (not including filename;
        # may not exist yet)
        self.processedPath = config.processedFilesDir

        # Will hold the numeric series from the file
        self.numericSeries = []

        # Will hold the waveform series from the file
        self.waveformSeries = []

        # Open the original file
        self.openOriginalFile()

        # Attempt to open the processed data file. Set the newlyProcessData
        # property accordingly. If the processed file is not present, we need
        # to newly process data.
        self.newlyProcessData = not self.openProcessedFile()
        
        # Load data series into memory from file (does not load data though)
        self.loadSeriesFromFile()
        
        # If we need to newly process data, do so now.
        if self.newlyProcessData:
            self.processAndStore()

    def generateAlerts(self, seriesname, threshold, duration, dutycycle, maxgap):

        # Find the series
        for s in self.numericSeries:

            if s.name == seriesname:

                return json.dumps(s.generateThresholdAlerts(threshold, duration, dutycycle, maxgap).tolist())

    # Returns the complete path to the original data file, including filename.
    def getFilepath(self):
        return os.path.join(self.path, self.filename)

    # Returns the complete path to the processed data file, including filename.
    def getProcessedFilepath(self):
        return os.path.join(self.processedPath, self.processedFilename)

    # Produces JSON output for all series in the file at the maximum time range.
    def getFullOutputAllSeries(self):

        print("Assembling all series full output for file " + self.filename + ".")
        start = time.time()

        outputObject = {}

        for s in self.numericSeries:
            outputObject["Numeric: "+s.name] = s.getFullOutput()

        for s in self.waveformSeries:
            outputObject["Waveform: "+s.name] = s.getFullOutput()

        end = time.time()
        print("Completed assembly of all series full output for file " + self.filename + ". Took " + str(round(end - start, 5)) + "s.")

        # TEMP -- MOVE THIS TO BEFORE END TIME LATER
        # Encode the JSON string
        jsonStr = json.dumps(outputObject, ignore_nan=True)

        # Return JSON-encoded string
        return jsonStr
    
    # Produces JSON output for all series in the file at a specified time range.
    def getRangedOutputAllSeries(self, starttime, stoptime):

        print("Assembling all series ranged output for file " + self.filename + ".")
        start = time.time()

        outputObject = {}
            
        for s in self.numericSeries:
            outputObject["Numeric: "+s.name] = s.getRangedOutput(starttime, stoptime)

        for s in self.waveformSeries:
            outputObject["Waveform: "+s.name] = s.getRangedOutput(starttime, stoptime)

        end = time.time()
        print("Completed assembly of all series ranged output for file " + self.filename + ". Took " + str(round(end - start, 5)) + "s.")

        # TEMP -- MOVE THIS TO BEFORE END TIME LATER
        # Encode the JSON string
        jsonStr = json.dumps(outputObject, ignore_nan=True)

        # Return JSON-encoded string
        return jsonStr

    # Produces JSON output for a given series in the file at a specified
    # time range.
    def getRangedOutputSingleSeries(self, series, start, stop):
        
        print("Assembling single series ranged output for file " + self.filename + ", series " + series + ".")
        st = time.time()

        outputObject = {}

        for s in self.numericSeries:
            if "Numeric: " + s.name == series:
                outputObject["Numeric: " + s.name] = s.getRangedOutput(start, stop)

        for s in self.waveformSeries:
            if "Waveform: " + s.name == series:
                outputObject["Waveform: " + s.name] = s.getRangedOutput(start, stop)

        et = time.time()
        print("Completed assembly of single series ranged output for file " + self.filename + ", series " + series + ". Took " + str(round(et - st, 5)) + "s.")

        # TEMP -- MOVE THIS TO BEFORE END TIME LATER
        # Encode the JSON string
        jsonStr = json.dumps(outputObject, ignore_nan=True)

        # Return JSON-encoded string
        return jsonStr
            
    # Sets up classes for all series from file (but does not load series data
    # into memory).
    def loadSeriesFromFile(self):
        
        print('Loading series from file.')

        for name in self.f['numerics']:
            self.numericSeries.append(Series(name, ['numerics', name, 'data'], self))

        for name in self.f['waveforms']:
            self.waveformSeries.append(Series(name, ['waveforms', name, 'data'], self))
            
        print('Completed loading series from file.')

    # Opens the HDF5 file. Returns boolean whether able to open.
    def openOriginalFile(self):

        # Open the HDF5 file
        try:
            self.f = h5py.File(self.getFilepath(), 'r')
        except Exception as e:
            print("Unable to open the original data file " + self.getProcessedFilepath() + ".\n", e)
            return False

        # If an exception was not raised, that means the file was opened
        return True
        
    # Opens the processed HDF5 data file. Returns boolean whether able to open.
    def openProcessedFile(self):

        # Open the processed data file
        try:
            self.pf = h5py.File(self.getProcessedFilepath(), "r")
        except Exception as e:
            print("Unable to open the processed data file " + self.getProcessedFilepath() + ".\n", e)
            return False
        
        # If an exception was not raised, that means the file was opened
        return True
    
    # Creates & opens a new HDF5 data file for storing processed data.
    def openProcessedFileForWriting(self):
    
        # Verify that the processed file does not already exist
        if os.path.isfile(self.getProcessedFilepath()):
            print("Processed file already exists. Aborting.")
            return False
    
        # Create the file which will be used to store processed data
        self.pf = h5py.File(self.getProcessedFilepath(), "w")

    # Process and store all downsamples for all series for the file.
    def processAndStore(self):
        
        try:
    
            print("Processing & storing all series for file " + self.filename + ".")
            start = time.time()
        
            # Create the file for storing processed data.
            self.openProcessedFileForWriting()
        
            # Process & store numeric series
            for s in self.numericSeries:
                s.processAndStore()
        
            # Process & store waveform series
            for s in self.waveformSeries:
                s.processAndStore()
        
            end = time.time()
            print("Completed processing & storing all series for file " + self.filename + ". Took " + str(round((end - start) / 60, 3)) + " minutes).")
            
        except Exception as e:
        
            print("There was an exception while processing & storing data for " + self.filename + ".")
            
            # Print the exception
            print(e)
            
            print("Deleting partially completed processed file " + self.getProcessedFilepath() + ".")
            
            # Delete the processed data file
            os.remove(self.getProcessedFilepath())
            
            print("File has been removed.")

    
    
    
    
    
    
    
    
    
    
    
    
    
    # Opens the processed HDF5 dta file.
    def loadProcessedFileOverrideTEMP(self, fn, path):

        self.processedFilename = fn
        self.processedPath = path

        # Open the processed data file
        try:
            self.pf = h5py.File(self.getProcessedFilepath(), "r")
        except Exception as e:
            print("Unable to open the processed data file " + self.getProcessedFilepath() + ".\n", e)

    def closeAndReopenProcessedTEMP(self):
        self.pf.close()
        self.openProcessedFile()
