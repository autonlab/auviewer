from flask import Flask, Blueprint, send_from_directory, request
from file import File
from project import Project

# These imports are temporary for performance testing
import config
import time

file = File('test_wave_20190626.h5', config.originalFilesDir)

#mf = File('test_wave_20190626.h5')
#mf.prepareAllNumericSeries()
#mf.prepareAllWaveformSeries()
#mf.prepareAllSeries()

# project = Project()
# project.processUnprocessedFiles()
# print("Done.")
# quit()

# project = Project()
# project.processUnprocessedFiles()
# file = project.files[0]

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
app.register_blueprint(Blueprint('css', __name__, static_url_path='/css', static_folder='../www/css'))
app.register_blueprint(Blueprint('js', __name__, static_url_path='/js', static_folder='../www/js'))

@app.route('/')
@app.route('/index.html')
def index():
    return send_from_directory('../www', 'index.html')

@app.route('/bokeh.html')
def bokeh():
    return send_from_directory('../www', 'bokeh.html')

@app.route('/all_data_all_series')
def all_data_all_series():

    # Return the full (zoomed-out but downsampled if appropriate) datasets for
    # all data series.
    return file.getFullOutputAllSeries()

@app.route('/data_window_all_series', methods=['GET'])
def data_window_all_series():

    if request.method == 'GET' and len(request.args.get('start', default='')) > 0 and len(request.args.get('stop', default='')) > 0:

        # Parse the start & stop times
        start = request.args.get('start', type=float)
        stop = request.args.get('stop', type=float)

        return file.getRangedOutputAllSeries(start, stop)

    else:
        return "Invalid request."

@app.route('/data_window_single_series', methods=['GET'])
def data_window_single_series():

    if request.method == 'GET' and len(request.args.get('start', default='')) > 0 and len(request.args.get('start', default='')) > 0 and len(request.args.get('stop', default='')) > 0:

        # Parse the series name and start & stop times
        series = request.args.get('series')
        start = request.args.get('start', type=float)
        stop = request.args.get('stop', type=float)

        return file.getRangedOutputSingleSeries(series, start, stop)
    
@app.route('/get_alerts', methods=['GET'])
def get_alerts():
    
    # Parse the series name and alert parameters
    series = request.args.get('series')
    threshold = request.args.get('threshold', type=float)
    duration = request.args.get('duration', type=float)
    dutycycle = request.args.get('dutycycle', type=float)
    maxgap = request.args.get('maxgap', type=float)
    
    return file.generateAlerts(series, threshold, duration, dutycycle, maxgap)

@app.route('/get_unprocessed_files')
def get_unprocessed_files():

    return str(project.getUnprocessedFiles())