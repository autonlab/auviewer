# Medview Patient Data Viewer/Annotator

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Development](#development)
3. [API Methods](#api-methods)
4. [File Standard](#file-standard)

## <a name="system-requirements"></a>System Requirements

* There is enough system memory to hold approximately twice the size of the largest data series which the system will handle, with margin leftover for normal application overhead.

## <a name="development"></a>Development

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
* ```originalsDir``` & ```processedFilesDir``` in _server/config.py_
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

## <a name="api-methods"></a>API Methods

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

### /initial_project_payload

#### Request

http://[medview]/initial_project_payload

#### Response

Returns an array of filenames available for the project.

### /initial_file_payload

#### Request

http://[medview]/initial_file_payload?file=[string]

#### Response

Returns initial payload of data related to a file, including annotations, metadata, and all series' data for all time. See *Standard Data Response Format* above.

### /series_ranged_data

#### Request

http://[medview]/series_ranged_data?file=[string]&series[]=[string]...&start=[float]&stop=[float]

The *series[]* parameter is an array of series names whose data should be returned. For example, if 'series1' and 'series2' are requested, these parameters would appear as ```series[]=series1&series[]=series2``` in the URL. The *start* & *stop* parameters are time offset floating-point values.

#### Response

See *Standard Data Response Format* above. All series data in the file for the given time window will be transmitted.

## <a name="file-standard"></a>File Schema

### Version

The following is the file schema for version ```0.2```.

### Vocabulary

AUView uses the HDF5 file format. AUView and HDF5 each has its own vocabulary, so let us first introduce this vocabulary.

HDF5 is built around __groups__, __datasets__, and __attributes__. In a nutshell, __datasets__ hold tabular data, and they may be stored in an arbitrary hierarchy of __groups__ (like folders on a file system). Both __groups__ and __datasets__ may have __attributes__. In this sense, HDF is characterized as a "self-describing" data format.

AUView is built around __projects__, __files__, and __data series__. A __project__ holds a collection of any number of __files__ (HDF5 files), and a __file__ holds any number of __data series__ (HDF5 datasets). AUView will index all __data series__ in a __file__ agnostic of the grouping structure, other than the fact that the __data series__ ID is the collation of HDF5 group names and dataset name joined by forward slashes (e.g. the dataset located at File->Group1->Group2->DatasetX has ID ```Group1/Group2/DatasetX```).

### File Spec

AUView will extract the following from HDF5 files:
* System-related metadata (e.g. version)
* Metadata about the file
* Data series (time series or event data)

The HDF5 files should have the following structure:
* The root group should have the following attributes:
  * ```version```: specifies the file schema version
  * Any other metadata about the file (to be displayed on the viewer)
* The grouping structure for datasets is arbitrary to the system.
* Each dataset should have the following attributes:
  * ```name```: name of the series
  * ```type=[timeseries|enumerated_timeseries|events]```: specifies the type of data
  * ```Ftype_<colname>=[time|string|numeric]```: specifies each column's data type
    * Each column should have one such attribute on the dataset.
    * There must only be one ```time``` column type per dataset.
  * ```Funits_<colname>=<unit>```: specifies each column's unit as a string, usually plural (e.g. "seconds")
  * ```Flookup_<col>=<dsetpath>```: specifies the path to an optional string lookup dataset for a string column, in the form of slash-separated group names followed by dataset name, e.g. _'/grp1/grp2/somedset'_ or _'/somedset'_ (details below)

#### String Lookup Table

If you have a string column in your dataset, you may optionally specify a string lookup table. The reason to do this would be if you have repeated string values which unnecessarily bloat file size.

The format of the lookup dataset should be simply a 1d array of string values. The original dataset string column then specifies the dataset index of the value in the lookup table.

For example, say we have the following original dataset:

| Time | Event |
|------|-------|
| 127  | flex  |
| 192  | pulse |
| 207  | flex  |
| 248  | pulse |

We change this dataset to:

| Time | Event |
|------|-------|
| 127  | 0     |
| 192  | 1     |
| 207  | 0     |
| 248  | 1     |

And create the following string lookup dataset:

| (index) |       |
|---------|-------|
| (0)     | flex  |
| (1)     | pulse |
