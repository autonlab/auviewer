Getting Started with Development
================================

Initial Setup
-------------

For initial dev setup, use the following steps.

Create and activate your virtual environment if desired, e.g.::

   conda create -n auv python=3.8 -y
   conda activate auv

Clone the repo and install requirements::

   git clone git@github.com:autonlab/auviewer.git
   cd auviewer
   pip install -r requirements.txt

Build the project::

   ./tools/rebuild

.. note::

   If you need to recompile cython (e.g. if you make changes to auviewer/cylib.pyx), change the RECOMPILE_CYTHON flag to True in setup.py.

Finally, run the viewer from source against the sample file (this must be done from the code root directory)::

   python -m auviewer.serve examples/sample_patient.h5