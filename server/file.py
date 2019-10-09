import h5py
import config
import os.path
from os import remove as rmfile
import time

from series import Series
from annotationset import AnnotationSet
from exceptions import ProcessedFileExists

# File represents a single patient data file.
class File:

    def __init__(self, filename, path):

        print("\n------------------------------------------------\nACCESSING FILE: " + filename + "\n------------------------------------------------\n")

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
        self.series = []
        
        # Instantiate the AnnotationSet class for the file
        self.annotationSet = AnnotationSet(self)

        # Open the original file
        self.openOriginalFile()

        # Attempt to open the processed data file. Set the newlyProcessData
        # property accordingly. If the processed file is not present, we need
        # to newly process data.
        self.newlyProcessData = not self.openProcessedFile()

        # If we need to newly process data, do so now.
        if self.newlyProcessData:
            self.process()
        else:
            self.load()

    # Creates & opens a new HDF5 data file for storing processed data.
    def createProcessedFile(self):
    
        # Verify that the processed file does not already exist
        if os.path.isfile(self.getProcessedFilepath()):
            print("Processed file already exists. Raising ProcessedFileExists exception.")
            raise ProcessedFileExists
    
        # Create the file which will be used to store processed data
        try:
            print("Creating processed file.")
            self.pf = h5py.File(self.getProcessedFilepath(), "w")
        except:
            print("There was an exception while h5py was creating the processed file. Raising ProcessedFileExists exception.")
            raise ProcessedFileExists
        
    def generateAlerts(self, seriesid, thresholdlow, thresholdhigh, mode, duration, dutycycle, maxgap):

        # Find the series
        for s in self.series:
            if s.id == seriesid:
                return s.generateThresholdAlerts(thresholdlow, thresholdhigh, mode, duration, dutycycle, maxgap).tolist()

    # Returns the complete path to the original data file, including filename.
    def getFilepath(self):
        return os.path.join(self.path, self.filename)

    # Produces JSON output for all series in the file at the maximum time range.
    def getInitialFilePayload(self):

        print("Assembling all series full output for file " + self.filename + ".")
        start = time.time()

        outputObject = {
            'annotations': self.annotationSet.getAnnotations().tolist(),
            'metadata': self.getMetadata(),
            'series': {}
        }

        for s in self.series:
            outputObject['series'][s.id] = s.getFullOutput()

        end = time.time()
        print("Completed assembly of all series full output for file " + self.filename + ". Took " + str(round(end - start, 5)) + "s.")

        # Return the output object
        return outputObject
    
    # Returns a dict of file metadata.
    def getMetadata(self):
        metadata = {}
        for property in self.f.attrs:
            metadata[property] = self.f.attrs[property]
        return metadata
    
    # Returns a reference to the processed data file, or None if there is none.
    def getProcessedFile(self):
        
        if not hasattr(self, 'pf') or not self.pf or self.pf is None:
            return None
        else:
            return self.pf

    # Returns the complete path to the processed data file, including filename.
    def getProcessedFilepath(self):
        return os.path.join(self.processedPath, self.processedFilename)
    
    # Returns the series instance corresponding to the provided series ID, or
    # None if the series cannot be found.
    def getSeries(self, seriesid):
        
        # TODO(gus): We temporarily have to traverse both nueric and waveform
        # series until this is consolidated.
        for s in self.series:
            if s.id == seriesid:
                return s
        return None

    # Produces JSON output for a given list of series in the file at a specified
    # time range.
    def getSeriesRangedOutput(self, seriesids, start, stop):

        print("Assembling series ranged output for file " + self.filename + ", series ]" + ', '.join(seriesids) + "].")
        st = time.time()

        outputObject = {
            'series': {}
        }

        for s in self.series:
            if s.id in seriesids:
                outputObject['series'][s.id] = s.getRangedOutput(start, stop)

        et = time.time()
        print("Completed assembly of series ranged output for file " + self.filename + ", series [" + ', '.join(seriesids) + "]. Took " + str(round(et - st, 5)) + "s.")

        # Return the output object
        return outputObject
    
    # Loads the necessary data into memory for an already-processed data file.
    def load(self):
    
        # Load data series into memory from file (does not load data though)
        self.loadSeriesFromFile()
        
    # Sets up classes for all series from file (but does not load series data
    # into memory).
    def loadSeriesFromFile(self):
        
        print('Loading series from file.')

        if 'numerics' in self.f.keys():
            for name in self.f['numerics']:
                self.series.append(Series(['numerics', name, 'data'], self))

        if 'waveforms' in self.f.keys():
            for name in self.f['waveforms']:
                self.series.append(Series(['waveforms', name, 'data'], self))
            
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
            self.pf = h5py.File(self.getProcessedFilepath(), "r+")
        except Exception as e:
            print("Unable to open the processed data file " + self.getProcessedFilepath() + ".\n", e)
            return False
        
        # If an exception was not raised, that means the file was opened
        return True

    # Process and store all downsamples for all series for the file.
    def process(self):
        
        try:
    
            print("Processing & storing all series for file " + self.filename + ".")
            start = time.time()

            # Load data series into memory from file (does not load data though)
            self.loadSeriesFromFile()
        
            # Create the file for storing processed data.
            self.createProcessedFile()
        
            # Process & store numeric series
            for s in self.series:
                s.processAndStore()
        
            end = time.time()
            print("Completed processing & storing all series for file " + self.filename + ". Took " + str(round((end - start) / 60, 3)) + " minutes).")

        # For ProcessedFileExists exception, don't delete the file but simply
        # re-raise the exception.
        except ProcessedFileExists:
            raise

        except (KeyboardInterrupt, SystemExit):

            print("Interrupt detected. Aborting as requested.")
            print("Deleting partially completed processed file " + self.getProcessedFilepath() + ".")

            # Delete the processed data file
            rmfile(self.getProcessedFilepath())

            print("File has been removed.")

            # Quit the program
            quit()
            
        except Exception as e:
        
            print("There was an exception while processing & storing data for " + self.filename + ".")
            print(e)
            print("Deleting partially completed processed file " + self.getProcessedFilepath() + ".")
            
            # Delete the processed data file
            rmfile(self.getProcessedFilepath())
            
            print("File has been removed.")
            
            # Re-aise the exception
            raise
