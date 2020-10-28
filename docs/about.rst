About
=====

Design Choices
--------------
AUViewer is designed to enable web-based viewing & annotation of large
time-series data via a web browser and across the internet in a portable way.
To unpack some of these terms:

large time-series data
    E.g. 20-100GB per file and beyond. File size can theoretically grow without
    limit and still remain performant for a user in a browser on a standard
    internet connection.
across the internet
    Using a basic internet connection, e.g. 1 Mbps download
portable
    Many software packages for working with large datasets require software
    installation. AUViewer was made to handle such tasks with no software
    installation, special compute resources, or special bandwidth required of
    the end user.

Tradeoffs & Implications
------------------------
Any non-trivial system involves design choices and tradeoff decisions. AUViewer
prioritizes performance and memory efficiency over disk efficiency.

Specifically, in order to render large time-series datasets in the browser
quickly and without significant backend memory requirements, the system
pre-computes and stores to disk min-max downsample representations of all
original files which it serves. Generally, this leads to a doubling of original
data disk space requirements (e.g. a 20GB original file will require on the
order of 20GB of additional space for pre-computed downsample data).

Created for You By
------------------
Auton Universal Viewer was created for you by `Gus Welter`_, `Anthony Wertz`_, and `Dr. Artur Dubrawski`_ of the
`Auton Lab`_ at `Carnegie Mellon University`_.

.. _Gus Welter: https://www.ri.cmu.edu/ri-people/gus-welter/
.. _Anthony Wertz: https://www.ri.cmu.edu/ri-people/anthony-t-wertz/
.. _Dr. Artur Dubrawski: https://www.ri.cmu.edu/ri-faculty/artur-w-dubrawski/
.. _Auton Lab: https://www.autonlab.org/
.. _Carnegie Mellon University: https://www.cmu.edu/

Additional Contributors
```````````````````````

Additional contributors & collaborators include:

* `Dr. Michael R. Pinsky`_, Critical Care Medicine, University of Pittsburgh Medical Center
* `Dr. Gilles Clermont`_, Critical Care Medicine, University of Pittsburgh Medical Center
* `Dr. Marilyn Hravnak`_, University of Pittsburgh School of Nursing
* `Victor Leonard`_, Auton Lab, Carnegie Mellon University
* Many others who provided valuable input & feedback.

.. _Dr. Michael R. Pinsky: https://www.ccm.pitt.edu/node/241
.. _Dr. Gilles Clermont: https://www.ccm.pitt.edu/node/261
.. _Dr. Marilyn Hravnak: https://www.nursing.pitt.edu/person/marilyn-hravnak
.. _Victor Leonard: https://www.ri.cmu.edu/ri-people/victor-leonard/

Interested in Contributing?
```````````````````````````

Are you interested in contributing to Auton Universal Viewer? Please see :doc:`contributing/motivation`