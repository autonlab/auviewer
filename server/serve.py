from flask import Flask, Blueprint, send_from_directory, request
from project import Project

# Simplejson package is required in order to "ignore" NaN values and implicitly
# convert them into null values. RFC JSON spec left out NaN values, even though
# ES5 supports them (https://www.ecma-international.org/ecma-262/5.1/#sec-4.3.23).
# By default, Python "json" module will allow & json-encode NaN values, but the
# Chrome JS engine will throw an error when trying to parse them. Simplejson
# package, with ignore_nan=True, will implicitly convert NaN values into null
# values. Find "ignore_nan" here: https://simplejson.readthedocs.io/en/latest/
import simplejson as json

# These imports are temporary for performance testing
import config
import time

# file = File('test_wave_20190626.h5', config.originalFilesDir)

#mf = File('test_wave_20190626.h5')
#mf.prepareAllNumericSeries()
#mf.prepareAllWaveformSeries()
#mf.prepareAllSeries()

# project = Project()
# project.processUnprocessedFiles()
# print("Done.")
# quit()

project = Project()
# project.processFiles()
project.loadProcessedFiles()

# # TESTING: Begin test code
#
# file = File('test_wave_20190626.h5', config.originalFilesDir)
#
# def test(fn):
#
#     n = 5
#     t = 0
#
#     for i in range(n):
#         file.loadProcessedFileOverrideTEMP(fn, config.processedFilesDir)
#         start = time.time()
#         output = file.getFullOutputAllSeries()
#         end = time.time()
#         t = t + (end-start)
#         # print("\t\t\t\t\t\t\t\t\t\t" + fn + ": " + str(round(end - start, 5)) + "s")
#         # print("\t\t\t\t\t\t\t\t\t\t" + fn + ": " + format((end-start)*1000, 'f') + "ms")
#
#     print("\t\t\t\t\t\t\t\t\t\t" + fn + ": " + format(t/n*1000, 'f') + "ms (AVG)")
#
# # Attach and test no-compression
# test('test_wave_20190626_processed_nocmp.h5')
# test('test_wave_20190626_processed_gzip_1.h5')
# test('test_wave_20190626_processed_gzip_4.h5')
# test('test_wave_20190626_processed_gzip_9.h5')
# test('test_wave_20190626_processed_lzf.h5')
# test('test_wave_20190626_processed_shuf_gzip_1.h5')
# test('test_wave_20190626_processed_shuf_gzip_4.h5')
# test('test_wave_20190626_processed_shuf_gzip_9.h5')
# test('test_wave_20190626_processed_shuf_lzf.h5')
# quit()
#
# # TESTING: End test code

# Instantiate the Flask web application class
app = Flask(__name__)

# Map our static assets to be served
app.register_blueprint(Blueprint('css', __name__, static_url_path=config.rootWebPath+'/css', static_folder='../www/css'))
app.register_blueprint(Blueprint('js', __name__, static_url_path=config.rootWebPath+'/js', static_folder='../www/js'))

@app.route(config.rootWebPath+'/')
@app.route(config.rootWebPath+'/index.html')
def index():
    return send_from_directory('../www', 'index.html')

@app.route(config.rootWebPath+'/bokeh.html')
def bokeh():
    return send_from_directory('../www', 'bokeh.html')

@app.route(config.rootWebPath+'/all_data_all_series')
def all_data_all_series():

    if request.method == 'GET' and len(request.args.get('file', default='')) > 0:

        # Parse the filename
        filename = request.args.get('file')

        # Get the file
        file = project.getFile(filename)

        # Return the full (zoomed-out but downsampled if appropriate) datasets for
        # all data series.
        output = file.getFullOutputAllSeries()
        json_output = json.dumps(output, ignore_nan=True)
        
        return json_output

    else:
        return "Invalid request."

@app.route(config.rootWebPath+'/data_window_all_series', methods=['GET'])
def data_window_all_series():

    if request.method == 'GET' and len(request.args.get('file', default='')) > 0 and len(request.args.get('start', default='')) > 0 and len(request.args.get('stop', default='')) > 0:

        # Parse the start & stop times
        filename = request.args.get('file')
        start = request.args.get('start', type=float)
        stop = request.args.get('stop', type=float)

        # Get the file
        file = project.getFile(filename)

        output = file.getRangedOutputAllSeries(start, stop)
        json_output = json.dumps(output, ignore_nan=True)
        
        return json_output

    else:
        return "Invalid request."

@app.route(config.rootWebPath+'/data_window_single_series', methods=['GET'])
def data_window_single_series():

    if request.method == 'GET' and len(request.args.get('file', default='')) > 0 and len(request.args.get('start', default='')) > 0 and len(request.args.get('start', default='')) > 0 and len(request.args.get('stop', default='')) > 0:

        # Parse the series name and start & stop times
        filename = request.args.get('file')
        series = request.args.get('series')
        start = request.args.get('start', type=float)
        stop = request.args.get('stop', type=float)

        # Get the file
        file = project.getFile(filename)

        output = file.getRangedOutputSingleSeries(series, start, stop)
        json_output = json.dumps(output, ignore_nan=True)
        
        return json_output
    
@app.route(config.rootWebPath+'/get_alerts', methods=['GET'])
def get_alerts():

    # TODO(gus): Add checks here
    
    # Parse the series name and alert parameters
    filename = request.args.get('file')
    series = request.args.get('series')
    threshold = request.args.get('threshold', type=float)
    duration = request.args.get('duration', type=float)
    dutycycle = request.args.get('dutycycle', type=float)
    maxgap = request.args.get('maxgap', type=float)

    # Get the file
    file = project.getFile(filename)

    output = file.generateAlerts(series, threshold, duration, dutycycle, maxgap)
    return json.dumps(output, ignore_nan=True)

@app.route(config.rootWebPath+'/get_files')
def get_files():

    output = project.getActiveFileListOutput()
    return json.dumps(output, ignore_nan=True)