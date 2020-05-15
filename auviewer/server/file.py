import os.path
import time
from os import remove as rmfile
import traceback
import pandas as pd

import audata

from . import config
from .annotationset import AnnotationSet
from .cylib import generateThresholdAlerts
from .exceptions import ProcessedFileExists
from .series import Series

# File represents a single patient data file. File may operate in file- or
# realtime-mode. In file-mode, all data is written to & read from a file. In
# realtime-mode, no file is dealt with and instead everything is kept in memory.
# If no filename parameter is passed to the constructor, File will operate in
# realtime-mode.
class File:

    def __init__(self, projparent, orig_filename='', proc_filename='', orig_dir='', proc_dir=''):

        print("\n------------------------------------------------\nACCESSING FILE: " + os.path.join(orig_dir, orig_filename) + "\n------------------------------------------------\n")

        # Holds reference to the project parent
        self.projparent = projparent

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
            self.pf = audata.AUFile.new(self.getProcessedFilepath(), overwrite=False, return_datetimes=False)
            return self.pf
        except:
            print("There was an exception while h5 was creating the processed file. Raising ProcessedFileExists exception.")
            raise ProcessedFileExists

    def detectAnomalies(self, type, series, thresholdlow=None, thresholdhigh=None, duration=300, persistence=.7, maxgap=300, series2=None):

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

        if type == 'anomalydetection':

            # Find the series & run anomaly detection
            for s in self.series:
                if s.id == series:
                    return s.generateThresholdAlerts(thresholdlow, thresholdhigh, mode, duration, persistence, maxgap).tolist()

        elif type == 'correlation':

            # TODO(Gus): TEMP!
            series2 = '/data/numerics/HR.HR:value'
            timewindow='10min'

            # The series2 parameter is required for correlation detection.
            if series2 is None:
                print("Error: Correlation detection requires series2 parameter.")
                return []

            # Find the series
            for s in self.series:
                if s.id == series:
                    s1 = s
                if s.id == series2:
                    s2 = s

            t1, v1 = s1.pullRawDataIntoMemory(returnValuesOnly=True)
            t2, v2 = s2.pullRawDataIntoMemory(returnValuesOnly=True)

            s1Data = pd.DataFrame({
                'time': t1,
                'val1': v1
            })
            s2Data = pd.DataFrame({
                'time': t2,
                'val2': v2
            })

            # Assemble into series 1 & series 2 dataframes
            # s1Data = pd.concat((t1, v1), axis=1)
            # s2Data = pd.concat((t2, v2), axis=1)
            #
            # # Assert column names
            # s1Data.columns = ['time', 'val1']
            # s2Data.columns = ['time', 'val2']

            # Create an inner joined dataset with common time column
            df = s1Data.merge(s2Data, on='time')

            # Filter out null values
            df = df[df.notnull()]

            # Create a datetime column
            df['time_conv'] = pd.to_datetime(df.time, unit='s')

            # Set the index to the datetime column
            df.set_index('time_conv', inplace=True)

            print(df)

            # Generate the rolling-window correlation
            corr = df['val1'].rolling(timewindow).corr(other=df['val2'])

            # Now run anomaly detection on the rolling-window correlation
            alerts = generateThresholdAlerts(df['time'].to_numpy(), corr.to_numpy(), thresholdlow, thresholdhigh, mode, duration, persistence, maxgap).tolist()

            return alerts

    # Returns all event series
    def getEvents(self):

        print("Assembling all event series for file " + self.orig_filename + ".")
        start = time.time()

        events = {}

        # If we're in realtime-mode, we have no events to return, so return now.
        if self.mode() == 'realtime':
            return events

        def catcols(row, idcol=None):
            idx = row[idcol]
            return (idx, '\n'.join(
                [f'{row[c]}' for c in row.index \
                    if (c is not idcol) and (row[c] is not None) and (row[c] != '')]))

        try:

            # Prepare references to HDF5 data
            meds = self.f['ehr/medications'][:]
            events['meds'] = meds.apply(catcols, 1, idcol='time').tolist()

        except Exception:
            print("Error retrieving meds.")
            traceback.print_exc()

        try:

            # Prepare references to HDF5 data
            ce = self.f['low_rate'][:]
            events['ce'] = ce.apply(catcols, 1, idcol='date').tolist()

        except Exception:
            print("Error retrieving ce.")
            traceback.print_exc()

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
            'baseTime': 0, # ATW: Not sure if this is still necessary.
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
            metadata['audata'] = self.f.meta_audata
            metadata['data'] = self.f.meta_data

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
        for (ds, _) in self.f.recurse():

            self.loadSeriesFromDataset(ds)

        # if 'numerics' in self.f.keys():
        #     for name in self.f['numerics']:
        #         self.loadSeriesFromDataset(['numerics', name, 'data'])
        #
        # if 'waveforms' in self.f.keys():
        #     for name in self.f['waveforms']:
        #         self.loadSeriesFromDataset(['waveforms', name, 'data'])

        print('Completed loading series from file.')

    # Load all available series from a dataset
    def loadSeriesFromDataset(self, ds):

        # Grab the columns.
        cols = ds.columns

        # Determine the time column name. Look for a column names 'time', 'timestampe',
        # or the first time column, in that order.
        timecol = None
        if 'time' in cols:
            timecol = 'time'
        elif 'timestamp' in cols:
            timecol = 'timestamp'
        else:
            for col in cols:
                if cols[col]['type'] == 'time':
                    timecol = col
                    break

        # If time column not available, print an error & return
        if timecol is None:
            print(f"Did not find a time column in {self.orig_filename}.", 'Cols:', cols)
            return
        else:
            print(f'Using time column {ds.name}:{timecol}')

        # Iterate through all remaining columns and instantiate series for each
        for valcol in (c for c in cols if c != timecol):
            coltype = cols[valcol]['type']
            if coltype in ('real', 'integer'):
                print(f'  - Adding {coltype} series: {ds.name}:{valcol}')
                self.series.append(Series(ds, timecol, valcol, self))
            else:
                print(f'  - Skipping unsupported {coltype} series: {valcol}')

    # Returns the mode in which File is operating, either "file" or "realtime".
    def mode(self):
        return 'file' if self.orig_filename != '' else 'realtime'

    # Opens the HDF5 file.
    def openOriginalFile(self):

        # Open the HDF5 file
        self.f = audata.AUFile.open(self.getFilepath(), return_datetimes=False)

    # Opens the processed HDF5 data file. Returns boolean whether able to open.
    def openProcessedFile(self):

        # Open the processed data file
        try:
            self.pf = audata.AUFile.open(self.getProcessedFilepath(), return_datetimes=False)
        except Exception as e:
            print("Unable to open the processed data file " + self.getProcessedFilepath() + ".\n", e)
            traceback.print_exc()
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
            f = self.createProcessedFile()

            # Process & store numeric series
            for s in self.series:
                s.processAndStore()

            f.flush()

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
            if os.path.isfile(self.getProcessedFilepath()):
                rmfile(self.getProcessedFilepath())

            print("File has been removed.")

            # Re-aise the exception
            raise
