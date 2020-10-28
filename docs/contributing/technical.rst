Technical Overview
==================

Introduction
------------
We will cover here technical aspects of the viewer which are important for
contributing to the project. It is worthwhile to begin by reviewing the Design
Choices and Tradeoffs & Implications sections on the About_ page.

.. _About: about

Building & Publishing
---------------------

Build from source & install locally
```````````````````````````````````
::

    cd tools
    ./rebuild

Clean up source builds
``````````````````````
::

    cd tools
    ./clean

Generate Sphinx documentation
`````````````````````````````
::

    cd tools
    ./mkdocs

Build from source and publish Linux (wheels and source)
```````````````````````````````````````````````````````
::

    cd tools
    ./publish_linux

*Note: Requires Docker in order to build with manywheel*

Build from source and publish Mac wheel
```````````````````````````````````````
::

    cd tools
    ./publish_mac

Viewer Use Cases
------------------

Viewer allows the following primary use cases:

* Visualize & analyze time series data in a Jupyter Notebook
* Work on a project of time series data in a web-based interface
* Allow multi-user annotation of time series data in a web-based interface
* Serve via intranet or internet

Detailed Viewer Use Cases
```````````````````````````

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

Technical Documentation
-----------------------

Technical Architecture
``````````````````````

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
            * `Annotation` (extends `Member`)
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

Strategies
++++++++++

Because AUViewer is meant for visualization & annotation of large datasets, one important architectural strategy is to lazy load the data from disk (i.e. no caching in memory) with the exception of metadata which is not likely to grow too large for memory. For example, when the AUViewer web service starts, it loads the projects, file lists, and series lists but not the data contained therein. Each time an API request comes in to load a file, the data is read from disk, served, and then immediately purged from memory.

Patterns & Conventions
++++++++++++++++++++++

Communication between the web application frontend and backend takes place via an HTTP REST API interface using GET parameters for client-to-backend requests and JSON for backend-to-client responses. As a general design pattern, the classes (mentioned above) output generalized data structures (e.g. lists, dicts), and the encapsulation of response data into JSON takes place in the http handler functions in the `serve` module. This breakdown makes sense since AUViewer can be used both as a Python/Jupyter Notebook module and a web server.

As a function naming convention, getters are named `get[Thing]`, but getters which return output structured primarily for web transmission are named `get[Thing]Output` (for API transmission) or `get[Thing]Payload` (for an initial data payload embedded in an html template).

Backend Configuration
`````````````````````

Backend config consists of the following types of configuration parameters:

* General settings (e.g. verbose output)
* Tuning parameters (e.g. target data points per series transmission)
* Asset locations
* Web server configuration (e.g. root web directory, Flask config)

AUViewer comes with default config parameters for everything except the data directory location, which must be specified. Configuration is loaded and managed by the `auviewer.config` module.
