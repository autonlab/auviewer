import h5py as h5
import config
import os.path
import time
from annotationset import AnnotationSet
from exceptions import ProcessedFileExists
from helpers import gather_datasets_recursive
from os import remove as rmfile
from series import Series

# File represents a single patient data file. File may operate in file- or
# realtime-mode. In file-mode, all data is written to & read from a file. In
# realtime-mode, no file is dealt with and instead everything is kept in memory.
# If no filename parameter is passed to the constructor, File will operate in
# realtime-mode.
class File:

    def __init__(self, orig_filename='', proc_filename='', orig_dir='', proc_dir=''):

        print("\n------------------------------------------------\nACCESSING FILE: " + os.path.join(orig_dir, orig_filename) + "\n------------------------------------------------\n")

        # Holds the original filename
        self.orig_filename = orig_filename

        # Holds the directory that contains the original file
        self.orig_dir = orig_dir

        # Holds the procesed filename
        self.proc_filename = proc_filename

        # Holds the directory that contains the processed file
        self.proc_dir = proc_dir

        # Will hold the data series from the file
        self.series = []
        
        # Instantiate the AnnotationSet class for the file
        try:
            self.annotationSet = AnnotationSet(self)
        except:
            # An exception here likely means we're in serverless mode. Ignore.
            pass

        if self.mode() == 'file':

            # Open the original file
            self.openOriginalFile()

            # Attempt to open the processed data file. Set the newlyProcessData
            # property accordingly. If the processed file is not present, we need
            # to newly process data.
            self.newlyProcessData = not self.openProcessedFile()

            # If we need to newly process data, do so now. Currently, if we process
            # data, we do not load data (so File will be unusable for reading data
            # after it finishes processing a file). This may be changed in future.
            if self.newlyProcessData:
                self.process()
            else:
                self.load()

    def __del__(self):
        print("Cleaning up closed file.")
        try:
            self.f.close()
        except:
            pass

        try:
            self.pf.close()
        except:
            pass

    # Takes new data to add to one or more data series for the file (currently
    # works only in realtime-mode). The new data is assumed to occur after any
    # existing data. The parameter, seriesData, should be a dict of dicts of
    # lists as follows:
    #
    #   {
    #     'seriesName': {
    #       'times': [ t1, t2, ... , tn ],
    #       'values': [ v1, v2, ... , vn ]
    #     }, ...
    #   }
    #
    # Returns updated file data for transmission to realtime subscribers.
    def addSeriesData(self, seriesData):

        if config.verbose:
            print('Adding series data.', seriesData)

        if self.mode() != 'realtime':
            raise Exception('Can only addSeriesData() while in mem-mode.')

        if not isinstance(seriesData, dict):
            raise Exception('Invalid seriesData parameter received for addSeriesData().')

        # This will hold the update data to return
        update = {
            'series': {}
        }

        for s in seriesData:

            if not isinstance(seriesData[s], dict):
                raise Exception('Invalid seriesData[s] parameter received for addSeriesData().')

            # Retrieve or create the series
            series = self.getSeriesOrCreate(s)

            # If that failed, raise an exception
            if series is None:
                raise Exception('Attempting to create or retrieve series failed:', s)

            # Add the new series data
            series.addData(seriesData[s])

            nones = [None] * len(seriesData[s]['times'])

            update['series'][s] = {
                "id": s,
                "labels": ['Date/Offset', 'Min', 'Max', s],
                "data": [list(i) for i in zip(seriesData[s]['times'], nones, nones, seriesData[s]['values'])],
                "output_type": 'real'
            }

        if config.verbose:
            print('addSeriesData() returning', update)

        return update

    # Creates & opens a new HDF5 data file for storing processed data.
    def createProcessedFile(self):
    
        # Verify that the processed file does not already exist
        if os.path.isfile(self.getProcessedFilepath()):
            print("Processed file already exists. Raising ProcessedFileExists exception.")
            raise ProcessedFileExists
    
        # Create the file which will be used to store processed data
        try:
            print("Creating processed file.")
            self.pf = h5.File(self.getProcessedFilepath(), "w-")
        except:
            print("There was an exception while h5 was creating the processed file. Raising ProcessedFileExists exception.")
            raise ProcessedFileExists
        
    def detectAnomalies(self, series, thresholdlow=None, thresholdhigh=None, duration=300, persistence=.7, maxgap=300):

        # Determine the mode (see generateThresholdAlerts function description
        # for details on this parameter).
        if thresholdlow is None and thresholdhigh is None:
            # We must have at least one of thresholdlow or thresholdhigh.
            print("Error: We need at least one of threshold low or threshold high in order to perform anomaly detection.")
            return []
        if thresholdhigh is None:
            mode = 0
            thresholdhigh = 0
        elif thresholdlow is None:
            mode = 1
            thresholdlow = 0
        else:
            mode = 2

        # Find the series
        for s in self.series:
            if s.id == series:
                return s.generateThresholdAlerts(thresholdlow, thresholdhigh, mode, duration, persistence, maxgap).tolist()

    # Returns all event series
    def getEvents(self):
        
        print("Assembling all event series for file " + self.orig_filename + ".")
        start = time.time()
        
        events = {}

        # If we're in realtime-mode, we have no events to return, so return now.
        if self.mode() == 'realtime':
            return events
        
        try:
        
            # Prepare references to HDF5 data
            meds = self.f['meds']['all']['data'][()]
            meds_attributes = dict(self.f['meds']['all']['data'].attrs)
            meds_columns = list(meds.dtype.fields.keys())
            meds_columns.remove('time')
            slookup = self.f['meds']['all']['strings'][()]
            
            # Initialize the prepared meds data as a list comprehension with time
            events['meds'] = [[t, ''] for t in meds['time']]
            
            for i in range(len(events['meds'])):
                for c in meds_columns:
                    if 'Ftype_'+c in meds_attributes and meds_attributes['Ftype_'+c] == 'string':
                        events['meds'][i][1] += ("\n" if len(events['meds'][i][1]) > 0 else '') + c + ': ' + str(slookup[meds[c][i]])
                    else:
                        events['meds'][i][1] += ("\n" if len(events['meds'][i][1]) > 0 else '') + c + ': ' + str(meds[c][i])
            
        except Exception as e:
            print("Error retrieving meds.", e)
            
        try:
            
            # Prepare references to HDF5 data
            ce = self.f['ce']['all']['data'][()]
            ce_attributes = dict(self.f['ce']['all']['data'].attrs)
            ce_columns = list(ce.dtype.fields.keys())
            ce_columns.remove('date')
            slookup = self.f['ce']['all']['strings'][()]

            # Initialize the prepared ce data as a list comprehension with time
            events['ce'] = [[t, ''] for t in ce['date']]

            for i in range(len(events['ce'])):
                for c in ce_columns:
                    if 'Ftype_' + c in ce_attributes and ce_attributes['Ftype_' + c] == 'string':
                        events['ce'][i][1] += ("\n" if len(events['ce'][i][1]) > 0 else '') + c + ': ' + str(slookup[ce[c][i]])
                    else:
                        events['ce'][i][1] += ("\n" if len(events['ce'][i][1]) > 0 else '') + c + ': ' + str(ce[c][i])
            
        except Exception as e:
            print("Error retrieving ce.", e)

        end = time.time()
        print("Completed assembly of all event series for file " + self.orig_filename + ". Took " + str(round(end - start, 5)) + "s.")
        
        return events

    # Returns the complete path to the original data file, including filename.
    def getFilepath(self):
        return os.path.join(self.orig_dir, self.orig_filename)

    # Produces JSON output for all series in the file at the maximum time range.
    def getInitialPayloadOutput(self):

        print("Assembling all series full output for file " + self.orig_filename + ".")
        start = time.time()

        outputObject = {
            # 'annotations': self.annotationSet.getAnnotations().tolist(),
            'annotations': self.annotationSet.getAnnotations(),
            'baseTime': 0 if self.mode() == 'realtime' or 'meta' not in self.f or 'baseTime' not in self.f['meta'].attrs else self.f['meta'].attrs['baseTime'],
            'events': self.getEvents(),
            'metadata': self.getMetadata(),
            'series': {}
        }

        for s in self.series:
            outputObject['series'][s.id] = s.getFullOutput()

        end = time.time()
        print("Completed assembly of all series full output for file " + self.orig_filename + ". Took " + str(round(end - start, 5)) + "s.")

        # Return the output object
        return outputObject
    
    # Returns a dict of file metadata.
    def getMetadata(self):
        metadata = {}

        # Metadata is currently only available in realtime mode.
        if self.mode() == 'file':
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
        return os.path.join(self.proc_dir, self.proc_filename)
    
    # Returns the series instance corresponding to the provided series ID, or
    # None if the series cannot be found.
    def getSeries(self, seriesid):
        
        # TODO(gus): We temporarily have to traverse both nueric and waveform
        # series until this is consolidated.
        for s in self.series:
            if s.id == seriesid:
                return s
        return None

    # Returns a list of series names available in the file.
    def getSeriesNames(self):

        seriesNames = []
        for s in self.series:
            seriesNames.append(s.id)
        return seriesNames

    # Retreves or creates & returns the series corresponding to the provided
    # series ID.
    def getSeriesOrCreate(self, seriesid):

        # Attempt to retrieve the series
        series = self.getSeries(seriesid)

        # Otherwise, create the series
        if series is None:

            # Create new series
            self.series.append(Series([seriesid], 'time', 'value', self))

            # Retrieve the newly-created series
            series = self.getSeries(seriesid)

        return series

    # Produces JSON output for a given list of series in the file at a specified
    # time range.
    def getSeriesRangedOutput(self, seriesids, start, stop):

        print("Assembling series ranged output for file " + self.orig_filename + ", series ]" + ', '.join(seriesids) + "].")
        st = time.time()

        outputObject = {
            'series': {}
        }

        for s in self.series:
            if s.id in seriesids:
                outputObject['series'][s.id] = s.getRangedOutput(start, stop)

        et = time.time()
        print("Completed assembly of series ranged output for file " + self.orig_filename + ", series [" + ', '.join(seriesids) + "]. Took " + str(round(et - st, 5)) + "s.")

        # Return the output object
        return outputObject
        
    # Loads the necessary data into memory for an already-processed data file
    # (does not load data though).Sets up classes for all series from file but
    # does not load series data into memory).
    def load(self):
        
        print('Loading series from file.')

        # Iteratee through all datasets in the partial file
        for (ds, path) in gather_datasets_recursive(self.f):

            self.loadSeriesFromDataset(path)

        # if 'numerics' in self.f.keys():
        #     for name in self.f['numerics']:
        #         self.loadSeriesFromDataset(['numerics', name, 'data'])
        #
        # if 'waveforms' in self.f.keys():
        #     for name in self.f['waveforms']:
        #         self.loadSeriesFromDataset(['waveforms', name, 'data'])
            
        print('Completed loading series from file.')

    # Load all available series from a dataset
    def loadSeriesFromDataset(self, h5path):

        h5path_string = '/'.join(h5path)

        # Grab the dataset
        ds = self.f.get(h5path_string)

        # We expect fields to be available
        if ds.dtype.fields is None:
            print("Dataset", h5path_string, "has no fields.")
            return

        # Grab the column names
        cols = ds.dtype.fields.keys()

        # Determine the time column name
        timecol = 'timestamp' if 'timestamp' in cols else 'time'

        # If time column not available, print an error & return
        if timecol not in cols:
            print("Did not find a time column in " + self.orig_filename + '.', 'Cols:', cols)
            return

        # Iterate through all remaining columns and instantiate series for each
        for valcol in (c for c in cols if c != timecol):
            self.series.append(Series(h5path, timecol, valcol, self))

    # Returns the mode in which File is operating, either "file" or "realtime".
    def mode(self):
        return 'file' if self.orig_filename != '' else 'realtime'

    # Opens the HDF5 file.
    def openOriginalFile(self):

        # Open the HDF5 file
        self.f = h5.File(self.getFilepath(), 'r')
        
    # Opens the processed HDF5 data file. Returns boolean whether able to open.
    def openProcessedFile(self):

        # Open the processed data file
        try:
            self.pf = h5.File(self.getProcessedFilepath(), "r")
        except Exception as e:
            print("Unable to open the processed data file " + self.getProcessedFilepath() + ".\n", e)
            return False
        
        # If an exception was not raised, that means the file was opened
        return True

    # Process and store all downsamples for all series for the file.
    def process(self):
        
        try:
    
            print("Processing & storing all series for file " + self.orig_filename + ".")
            start = time.time()

            # Load data series into memory from file (does not load data though)
            self.load()
        
            # Create the file for storing processed data.
            self.createProcessedFile()
        
            # Process & store numeric series
            for s in self.series:
                s.processAndStore()
        
            end = time.time()
            print("Completed processing & storing all series for file " + self.orig_filename + ". Took " + str(round((end - start) / 60, 3)) + " minutes).")

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
        
            print("There was an exception while processing & storing data for " + self.orig_filename + ".")
            print(e)
            print("Deleting partially completed processed file " + self.getProcessedFilepath() + ".")
            
            # Delete the processed data file
            rmfile(self.getProcessedFilepath())
            
            print("File has been removed.")
            
            # Re-aise the exception
            raise
