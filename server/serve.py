from flask import Flask, Blueprint, send_from_directory, request
from file import File

mf = File('test_wave_20190626.h5')
#mf.prepareAllNumericSeries()
#mf.prepareAllWaveformSeries()
mf.prepareAllSeries()

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
    return mf.getFullOutputAllSeries()

@app.route('/data_window_all_series', methods=['GET'])
def data_window_all_series():

    if request.method == 'GET' and len(request.args.get('start', default='')) > 0 and len(request.args.get('stop', default='')) > 0:

        # Parse the start & stop times
        start = request.args.get('start', type=float)
        stop = request.args.get('stop', type=float)

        return mf.getRangedOutputAllSeries(start, stop)

    else:
        return "Invalid request."

@app.route('/data_window_single_series', methods=['GET'])
def data_window_single_series():

    if request.method == 'GET' and len(request.args.get('start', default='')) > 0 and len(request.args.get('start', default='')) > 0 and len(request.args.get('stop', default='')) > 0:

        # Parse the series name and start & stop times
        series = request.args.get('series')
        start = request.args.get('start', type=float)
        stop = request.args.get('stop', type=float)

        return mf.getRangedOutputSingleSeries(series, start, stop)