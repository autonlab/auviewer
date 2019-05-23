import datetime as dt
import downsample as ds
import h5py

# Simplejson package is required in order to "ignore" NaN values and implicitly convert them into null values.
# RFC JSON spec left out NaN values, even though ES5 supports them (https://www.ecma-international.org/ecma-262/5.1/#sec-4.3.23).
# By default, Python "json" module will allow & json-encode NaN values, but the Chrome JS engine will throw an error when trying to parse them.
# Simplejson package, with ignore_nan=True, will implicitly convert NaN values into null values.
# Find "ignore_nan" here: https://simplejson.readthedocs.io/en/latest/
import simplejson as json

def assembleOutput():

    # Open the HDF5 file
    f = h5py.File('output.h5', 'r')

    obj = {}

    for i in f['numeric'].keys():
        obj[i] = assembleTimeSeriesDataset(f, 'numeric', i)
        break

    return json.dumps(
        obj, # assembleTimeSeriesDataset(f, 'ECG.I', 'numeric'),
        ignore_nan = True
    )

def assembleTimeSeriesDataset(f, outerContainerName, seriesName):

    # The datetime values are offsets, in seconds, from a baseline datetime.
    # This is set as a global variable for now but should be changed later.
    global baseline
    baseline = dt.datetime.strptime(f[outerContainerName][seriesName]['data']['datetime'].attrs['time_reference'], '%Y-%m-%d %H:%M:%S.%f %z')

    ### Limited number of data points
    #return {
        #"labels": ['Date/Offset', seriesName],
        #"data": list(zip(map(addSecondsToBaseline, f[outerContainerName][seriesName]['data']['datetime'][0:4000]), f[outerContainerName][seriesName]['data']['value'][0:4000]))

    #}

    ### All data points
    #return {
        #"labels": ['Date/Offset', seriesName],
        #"data": list(zip(map(addSecondsToBaseline, f[outerContainerName][seriesName]['data']['datetime']), f[outerContainerName][seriesName]['data']['value']))
    #}

    ### Downsampled
    data = []
    intervals = ds.downsample(f[outerContainerName][seriesName]['data'])
    for i in intervals:
        data.append([i.time.isoformat(), i.min, i.max])
    return {
        "labels": ['Date/Offset', seriesName+' Min', seriesName+' Max'],
        "data": data
    }

def addSecondsToBaseline(additionalSeconds):
    return (baseline + dt.timedelta(0,additionalSeconds)).isoformat()
