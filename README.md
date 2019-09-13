# Medview Patient Data Viewer/Annotator

## Development

Most common setup and service management processes have been scripted in the _scripts_ directory.

### Initial Setup

Run the _setup.sh_ script to setup a new environment. The script assumes that Conda is installed and available with the ```conda``` command. The script will create a new Conda environment called "medview" and install application dependencies in the environment.

```bash
. setup.sh
```

### Configuration

Appplication config variables are located in three places:
* _scripts/config.sh_
* _server/config.py_
* _www/js/config.js_

See these files and their comments for the possible configurations. These are the parameters that will typically need to be changed for a new environment:
* ```MEDVIEW_BASE_DIR``` in _scripts/config.sh_
* ```originalFilesDir``` & ```processedFilesDir``` in _server/config.py_
* Mail-server related parameters in _server/config.py_

### Running the Server

To run the server, first run _activate.sh_ to activate the environment and set environment variables. Then run _start.sh_ to compile the Cython code and start the server.

```bash
. activate.sh
. start.sh
```

### Doing Things Manually

For the most part, look at the scripts to see how you would do things manually. However, here are a couple of hints.

#### Compiling Cython

The Cython files may be compiled by running the following while in the _server_ directory:

```bash
python setup.py build_ext --inplace
```

#### Running the Server Manually 

The server may be started manually by running the following while in the _server_ directory and after having activated the Conda environment:

```bash
python serve.py
```

Doing this step manually has the advantage of being able to skip the Cython compiling, which only needs to be done if the Cython code (_.pyx_ files) have changed. However, the Cython compiling is quite fast so it's often most convenient to use the scripts.

## API Methods

### Overview

A REST API is published for pulling patient data, making annotations, and other interactions.

API requests are submitted with GET http requests and, when applicable, GET parameters.

API responses are returned as JSON.

### Standard Data Response Format

All data series are delivered in the following standard JSON response format:

```json
{
    "seriesname": [
        [float:timeoffset, float:min, float:max, float:value],
        ...
    ],
    ...
}
```

The same format is used whether it is one series or multiple series, all time or time window.

The backend will decide whether to send downsampled values or real values and, for downsampled values, what scale of downsample to transmit. It decides this based on the goal of transmitting, at most, **M** downsampled values or 2**M** real values (**M** is configured in *server/config.py*).

For downsampled values, *min* & *max* will be defined and *value* will be null; conversely, for real values, *min* & *max* will be null and *value* will be defined.

If multiple series are requested, there may be a mix of series with downsampled values and series with real values. However, a given series will not have multiple types of values.

### /all_series_all_data

#### Request

http://[medview]/all_series_all_data

#### Response

See *Standard Data Response Format* above. All data series available for the patient for all time will be transmitted.

### /all_series_ranged_data

#### Request

http://[medview]/all_series_ranged_data?start=[float]&stop=[float]

The *start* & *stop* parameters are time offset floating-point values.

#### Response

See *Standard Data Response Format* above. All data series available for the patient in the given time window will be transmitted.

### /single_series_ranged_data

#### Request

http://[medview]/single_series_ranged_data?series=[string]start=[float]&stop=[float]

The *start* & *stop* parameters are time offset floating-point values, and the series is the URL-encoded name of the series.

#### Response

See *Standard Data Response Format* above. The requested data series in the given time window will be transmitted.

## Assumptions (TO BE FINALIZED)

* There is enough system memory to hold one entire series and one downsample level in memory with margin leftover for normal application overhead.