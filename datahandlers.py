import datetime as dt
import downsample
import h5py

# Simplejson package is required in order to "ignore" NaN values and implicitly convert them into null values.
# RFC JSON spec left out NaN values, even though ES5 supports them (https://www.ecma-international.org/ecma-262/5.1/#sec-4.3.23).
# By default, Python "json" module will allow & json-encode NaN values, but the Chrome JS engine will throw an error when trying to parse them.
# Simplejson package, with ignore_nan=True, will implicitly convert NaN values into null values.
# Find "ignore_nan" here: https://simplejson.readthedocs.io/en/latest/
import simplejson as json

def getDSS():
    return TEMPDSS

def assembleOutput():

    # Open the HDF5 file
    f = h5py.File('output.h5', 'r')

    obj = {}

    for i in f['numeric'].keys():
        #obj[i] = assembleTimeSeriesDataset(f, 'numeric', i)
        res = assembleTimeSeriesDataset(f, 'numeric', i)
        j = 0
        arrlen = len(res)
        while j < arrlen:
            obj[i+str(j)] = res[j]
            j = j + 1
        break

    return json.dumps(
        obj, # assembleTimeSeriesDataset(f, 'ECG.I', 'numeric'),
        ignore_nan = True
    )

def assembleTimeSeriesDataset(f, outerContainerName, seriesName):

    # The datetime values are offsets, in seconds, from a basetime datetime.
    # This is set as a global variable for now but should be changed later.
    global basetime
    basetime = dt.datetime.strptime(f[outerContainerName][seriesName]['data']['datetime'].attrs['time_reference'], '%Y-%m-%d %H:%M:%S.%f %z').replace(tzinfo=None)

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
    #data = []
    #dss = downsample.DownsampleSet()
    #dss.build(f[outerContainerName][seriesName]['data'])
    #for i in dss.downsamples[0].intervals:
    #    data.append([i.time.isoformat(), i.min, i.max])
    #return {
    #    "labels": ['Date/Offset', seriesName+' Min', seriesName+' Max'],
    #    "data": data
    #}

    # Downsampled x 3

    ret = []
    dss = downsample.DownsampleSet()
    global TEMPDSS
    TEMPDSS=dss
    dss.build(f[outerContainerName][seriesName]['data'])
    i = 0
    while i < len(dss.downsamples):

        data = []

        for j in dss.downsamples[i].intervals:
            data.append([j.time.isoformat(), j.min, j.max])

        ret.append({
            "labels": ['Date/Offset', seriesName + ' Min', seriesName + ' Max'],
            "data": data
        })

        i = i + 1

    return ret

def addSecondsToBaseline(additionalSeconds):
    return (basetime + dt.timedelta(0,additionalSeconds)).isoformat()
