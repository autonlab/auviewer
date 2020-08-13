import logging
import time
import traceback
import pandas as pd

import audata

from . import config
from .annotationset import AnnotationSet
from .cylib import generateThresholdAlerts
from .series import Series, simpleSeriesName

# File represents a single patient data file. File may operate in file- or
# realtime-mode. In file-mode, all data is written to & read from a file. In
# realtime-mode, no file is dealt with and instead everything is kept in memory.
# If no filename parameter is passed to the constructor, File will operate in
# realtime-mode.
class File:

    def __init__(self, projparent, id, origFilePathObj, procFilePathObj, processNewFiles=True):

        logging.info(f"\n------------------------------------------------\nACCESSING FILE: (ID {id}) {origFilePathObj}\n------------------------------------------------\n")

        # Holds reference to the project parent
        self.projparent = projparent

        # File ID & paths
        self.id = id
        self.origFilePathObj = origFilePathObj
        self.procFilePathObj = procFilePathObj

        # Will hold the data series from the file
        self.series = []

        # Instantiate the AnnotationSet class for the file
        try:
            self.annotationSet = AnnotationSet(self)
        except:
            # An exception here likely means we're in serverless mode. Ignore.
            # TODO: Serverless mode? Is this for realtime?
            pass

        if self.mode() == 'file':

            # Open the original file
            self.f = audata.File.open(str(self.origFilePathObj), return_datetimes=False)

            # Load series data into memory
            self.load()

            # Load the processed file if it exists
            if self.procFilePathObj.exists():
                self.pf = audata.File.open(str(self.procFilePathObj), return_datetimes=False)

            # Otherwise, if we're supposed to process new file data, process it.
            elif processNewFiles:
                self.process()

            # Otherwise, raise an exception
            else:
                raise Exception(f"File {self.origFilePathObj} has not been processed, but cannot proceed with processing because processNewFiles=False.")

    def __del__(self):

        logging.info("Cleaning up closed file.")

        # Close the original file
        try:
            self.f.close()
        except:
            pass

        # Close the processed file
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

        if config['verbose']:
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
                "labels": ['Date/Offset', 'Min', 'Max', simpleSeriesName(s)],
                "data": [list(i) for i in zip(seriesData[s]['times'], nones, nones, seriesData[s]['values'])],
                "output_type": 'real'
            }

        if config['verbose']:
            print('addSeriesData() returning', update)

        return update

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

        logging.info(f"Assembling all event series for file {self.origFilePathObj}.")
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
        logging.info(f"Completed assembly of all event series for file {self.origFilePathObj}. Took {str(round(end - start, 5))}s.")

        return events

    # Produces JSON output for all series in the file at the maximum time range.
    def getInitialPayloadOutput(self):

        logging.info(f"Assembling all series full output for file {self.origFilePathObj}.")
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
        logging.info(f"Completed assembly of all series full output for file {self.origFilePathObj}. Took {str(round(end - start, 5))}s.")

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

        logging.info(f"Assembling series ranged output for file {self.origFilePathObj}, series [{', '.join(seriesids)}].")
        st = time.time()

        outputObject = {
            'series': {}
        }

        for s in self.series:
            if s.id in seriesids:
                outputObject['series'][s.id] = s.getRangedOutput(start, stop)

        et = time.time()
        logging.info(f"Completed assembly of series ranged output for file {self.origFilePathObj}, series [{', '.join(seriesids)}]. Took {str(round(et - st, 5))}s.")

        # Return the output object
        return outputObject

    # Loads the necessary data into memory for an already-processed data file
    # (does not load data though).Sets up classes for all series from file but
    # does not load series data into memory).
    def load(self):

        logging.info('Loading series from file.')

        # Iteratee through all datasets in the partial file
        for (ds, _) in self.f.recurse():
            self.loadSeriesFromDataset(ds)

        logging.info('Completed loading series from file.')

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
            logging.error(f"Did not find a time column in {self.origFilePathObj}.\nCols: {cols}")
            return
        else:
            logging.info(f'Using time column {ds.name}:{timecol}')

        # Iterate through all remaining columns and instantiate series for each
        for valcol in (c for c in cols if c != timecol):
            coltype = cols[valcol]['type']
            if coltype in ('real', 'integer'):
                logging.info(f'  - Adding {coltype} series: {ds.name}:{valcol}')
                self.series.append(Series(ds, timecol, valcol, self))
            else:
                logging.warning(f'  - Skipping unsupported {coltype} series: {valcol}')

    # Returns the mode in which File is operating, either "file" or "realtime".
    def mode(self):
        # TODO(gus): When reviving realtime functionality, revise this
        return 'file'

    # Process and store all downsamples for all series for the file.
    def process(self):

        try:

            logging.info(f"Processing & storing all series for file {self.origFilePathObj}.")
            start = time.time()

            # Create the file for storing processed data.
            self.pf = audata.File.new(str(self.procFilePathObj), overwrite=False, return_datetimes=False)

            # Process & store numeric series
            for s in self.series:
                s.processAndStore()

            self.pf.flush()

            # Reload series data in memory since we have new downsamples
            self.load()

            end = time.time()
            logging.info(f"Completed processing & storing all series for file {self.origFilePathObj}. Took {str(round((end - start) / 60, 3))} minutes).")

        except (KeyboardInterrupt, SystemExit):

            logging.warning("Interrupt detected. Aborting as requested.")
            logging.warning(f"Deleting partially completed processed file {self.procFilePathObj}.")

            # Close the file
            try:
                self.pf.close()
            except Exception as e:
                logging.error(f"Unable to close the processed file.\n{e}\n{traceback.format_exc()}")

            # Delete the processed data file
            self.procFilePathObj.unlink()

            logging.info("Partial processed file has been removed.")

            # Quit the program
            quit()

        except Exception as e:

            logging.error(f"There was an exception while processing & storing data for {self.origFilePathObj}.\n{e}\n{traceback.format_exc()}\nDeleting partially completed processed file {self.procFilePathObj}.")

            # Close the file
            try:
                self.pf.close()
            except Exception as e:
                logging.error(f"Unable to close the processed file.\n{e}\n{traceback.format_exc()}")

            # Delete the processed data file
            self.procFilePathObj.unlink(missing_ok=True)

            logging.info("File has been removed.")

            # Re-raise the exception
            raise
