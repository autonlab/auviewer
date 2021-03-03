Getting Started
===============

Installation
------------
.. code-block:: bash

   pip install auviewer

For further details, see :doc:`installation`.

*Requires Python 3.8*

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

Regular Mode
````````````

To run the viewer normally:

.. code-block:: bash

   auv /path/to/auv_data_folder

or

.. code-block:: bash

   python -m auviewer.serve /path/to/auv_data_folder

*Note*: When running for the first time, specify an empty (or non-existent) folder. AUViewer will create the folder and
create the initial contents needed (including database, projects folder, etc).

File Format
-----------
AUViewer requires files in the *audata* or *ccdef* format. To convert other sources (e.g. csv, Pandas DataFrame) to
audata format, use the audata_ conversion tool.

.. _audata: https://audata.readthedocs.io/en/latest/

Sample File
```````````

You may download a `sample file`_ to test the viewer (the file is in the *ccdef* format, which is a superset of the *audata* data standard).

.. _sample file: https://github.com/autonlab/auviewer/blob/master/examples/sample_patient.h5