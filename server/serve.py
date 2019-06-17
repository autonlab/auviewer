from datetime import datetime as dt
from flask import Flask, Blueprint, send_from_directory, request
from file import File

print("Unpickling output.h5")
mf = File.unpickle('output.h5')
if not mf:
    print("Unpickling failed.")
    mf = File('output.h5')
    #mf.prepareAllWaveformSeries()
    mf.prepareAllNumericSeries()
    print("Pickling output.h5 for later use.")
    mf.pickle()
    print("Done pickling.")

else:
    print("Unpickled successfully.")

# Instantiate the Flask web application class
app = Flask(__name__)

# Map our static assets to be served
app.register_blueprint(Blueprint('css', __name__, static_url_path='/css', static_folder='../www/css'))
app.register_blueprint(Blueprint('js', __name__, static_url_path='/js', static_folder='../www/js'))

@app.route('/')
@app.route('/index.html')
def index():
    return send_from_directory('../www', 'index.html')

@app.route('/all_data_all_series')
def all_data_all_series():

    # Return the full (zoomed-out but downsampled if appropriate) datasets for
    # all data series.
    return mf.getFullOutput()

@app.route('/data_window_single_series', methods=['GET'])
def data_window_single_series():

    if request.method == 'GET' and len(request.args.get('start', default='')) > 0 and len(request.args.get('stop', default='')) > 0:

        # Parse the start & stop times
        start = dt.fromtimestamp(request.args.get('start', type=float) / 1000)
        stop = dt.fromtimestamp(request.args.get('stop', type=float) / 1000)

        return mf.getRangedOutput(start, stop)

    else:
        return "Invalid request."