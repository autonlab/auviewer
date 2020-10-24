# New Content (to be organized)

## Building & Publishing

To build from source and install locally:
```bash
cd tools
./rebuild
```

To build from source and publish Linux (wheels and source):
```bash
cd tools
./publish_linux
```

To build from source and publish Mac wheel:
```bash
cd tools
./publish_mac
```

## AUViewer Use Cases

AUViewer allows the following primary use cases:

* Visualize & analyze time series data in a Jupyter Notebook
* Work on a project of time series data in a web-based interface
* Allow multi-user annotation of time series data in a web-based interface
* Serve via intranet or internet

## Technical Documentation

### Technical Architecture

AUViewer is comprised of:
* A Python codebase in the form of a package built of modules, and
* A static HTML/JS/CSS codebase which makes up the frontend web application.

The Python code is organized primarily around classes which represent the most important conceptual components of the data:
* `Project`
  * `File`
    * `Series`
      * `DownsampleSet`
      * `RawData`

Other conceptual components, in the backend, are represented exclusively by database models (e.g. models.Annotation, models.PatternSet, and models.Pattern). The differentiating factor is that the Python classes, while the application is running, are treated as the primary source of truth for the associated data, and the database is a persistence medium; whereas, for the conceptual components which are only represented by database models, the database is the source of truth while the application is running.

Other important Python technical components are:
* Flask web server
* Cython functions for downsampling
* Database models and connectivity logic
* Config module
* Shared helper functions

Similar to Python, the web client JavaScript codebase is organized primarily around classes which represent the important conceptual components of the data:
* `Project`
  * `File`
    * `AnnotationSet` (extends `Set`)
      * TODO: `Annotation` (extends `Member`)
    * `AssignmentSet` (extends `Set`)
      * `Assignment` (extends `Member`)
    * `PatternSet` (extends `Set`)
      * `Pattern` (extends `Member`)
    * `Graph`

Additionally, a few technical components are implemented in classes:
* `GlobalStateManager` (instantiated as a global variable `globalStateManager`)
* `RequestHandler` (instantiated as a global variable `requestHandler`)
* `TemplateSystem` (instantiated as a global variable `templateSystem`)

No persistence or caching layer is used by the frontend codebase.

#### Strategies

Because AUViewer is meant for visualization & annotation of large datasets, one important architectural strategy is to lazy load the data from disk (i.e. no caching in memory) with the exception of metadata which is not likely to grow too large for memory. For example, when the AUViewer web service starts, it loads the projects, file lists, and series lists but not the data contained therein. Each time an API request comes in to load a file, the data is read from disk, served, and then immediately purged from memory.

#### Patterns & Conventions

Communication between the web application frontend and backend takes place via an HTTP REST API interface using GET parameters for client-to-backend requests and JSON for backend-to-client responses. As a general design pattern, the classes (mentioned above) output generalized data structures (e.g. lists, dicts), and the encapsulation of response data into JSON takes place in the http handler functions in the `serve` module. This breakdown makes sense since AUViewer can be used both as a Python/Jupyter Notebook module and a web server.

As a function naming convention, getters are named `get[Thing]`, but getters which return output structured primarily for web transmission are named `get[Thing]Output` (for API transmission) or `get[Thing]Payload` (for an initial data payload embedded in an html template).

### Detailed AUViewer Use Cases

In detail, from a perspective of technical architecture, the following use cases are accommodated:

* Jupyter Notebook Interface
  * Visualize/explore time series data ad-hoc
  * Visualize/explore project data
  * Analyze project data
  * Analyze annotations
  
* Python Module
  * Add project data
  * Analyze project data
  * Analyze annotations
  
* Web Server
  * Visualize/explore and/or annotate project data in single-user mode
  * Perform analytical tasks (e.g. create & manage annotation assignments, etc.)
  * Multi-user visualization & annotation by human subject matter experts
  * Optional user authentication integration
   
### Data Directory

When AUViewer is being used to visualize ad-hoc data, a data directory (including database) are _not_ required. In all other cases, a data directory is required.

The data directory is specified either as a function parameters (e.g. when used as a Python module) or as a command-line argument (when starting the web server via command line).

The data directory will contain project files, templates, config, and the database. The directory may be initially empty or pre-populated with some data. The organization of the directory is as follows, and assets will be created by AUViewer as needed if they do not already exist:
* config
  * _config.json_
* database
  * _db.sqlite_
* global_templates
  * _interface_templates.json_
  * _project_template.json_
* projects
  * \[project name\]
    * originals
    * processed
    * templates
      * _interface_templates.json_
      * _project_template.json_

(???) With the exception of the config file, the locations of all data directory assets above may be changed (???)

### Backend Configuration

Backend config consists of the following types of configuration parameters:
* General settings (e.g. verbose output)
* Tuning parameters (e.g. target data points per series transmission)
* Asset locations
* Web server configuration (e.g. root web directory, Flask config)

AUViewer comes with default config parameters for everything except the data directory location, which must be specified. Configuration is loaded and managed by the `auviewer.config` module.

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
