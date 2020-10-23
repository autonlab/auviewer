Getting Started
===============

Overview
--------
AUViewer is a tool for viewing & annotating time series data. It can be used as a standalone tool or
as a web-based application served to many users for annotation.

Installation
------------
.. code-block:: bash

   pip install auviewer

Usage
-----

Single-File Mode
````````````````

To view a single file:

.. code-block:: bash

   auv myfile.h5

or

.. code-block:: bash

   python -m auviewer.serve myfile.h5

*Note*: A temporary data folder will be used, and thus any annotations, etc. made to the database will be lost.

To run the viewer normally:

.. code-block:: bash

   auv /path/to/auv_data_folder
   # or
   python -m auviewer.serve /path/to/auv_data_folder

*Note*: When running for the first time, specify an empty (or non-existent) folder. AUViewer will create the folder and
create the initial contents needed (including database, projects folder, etc).

File Format
-----------
AUViewer requires files in the *audata* or *ccdef* format. To convert other sources (e.g. csv, Pandas DataFrame) to
audata format, use the audata_ conversion tool.

.. _audata: https://audata.readthedocs.io/en/latest/