Installation
============

PyPI
----

The auviewer Python package may be installed from PyPI_ with::

   pip install auviewer

.. _PyPI: https://pypi.org/project/auviewer/

*Requires Python 3.8*

Building from Source
--------------------
You may build from source using the bash script `tools/rebuild`_.

.. _tools/rebuild: https://github.com/autonlab/auviewer/blob/master/tools/rebuild

Portions of AUViewer are written in Cython_, which compiles into C code. The .c
files are included in source so that running the Cython compilation is not
necessary to build from source. However, if you wish to re-compile the Cython
code, ensure that Cython is installed, and set :code:`RECOMPILE_CYTHON = False`
in `setup.py`_.

.. _Cython: https://cython.org/
.. _setup.py: https://github.com/autonlab/auviewer/blob/master/setup.py