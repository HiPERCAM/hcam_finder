===============================
hcam-finder
===============================


.. image:: https://img.shields.io/pypi/v/hcam_finder.svg
        :target: https://pypi.python.org/pypi/hcam_finder

.. image:: https://img.shields.io/travis/StuartLittlefair/hcam_finder.svg
        :target: https://travis-ci.org/StuartLittlefair/hcam_finder

.. image:: https://readthedocs.org/projects/hcam-finder/badge/?version=latest
        :target: https://hcam-finder.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/StuartLittlefair/hcam_finder/shield.svg
     :target: https://pyup.io/repos/github/StuartLittlefair/hcam_finder/
     :alt: Updates


Observation planning and finding charts for HiPERCAM, ULTRACAM and ULTRASPEC

**IMPORTANT: as of v0.5 hcam_finder has updated the rotator centre and
offset for the GTC. If you installed prior to this, make sure you delete the
config file `~/.hfinder/config` and update to the latest version.**

``hcam_finder`` provides a Python scripts ``hfinder``, ``ufinder`` and ``usfinder``
for observation planning with HiPERCAM on the WHT and GTC, ULTRACAM on the NTT and
ULTRASPEC on the TNT.

These tools allow you to generate finding charts as well as specify the instrument setup
you require, whilst providing an estimate of observing cadence, exposure time and
S/N estimates.

``hcam_finder`` is written in Python and is based on TKinter. It should be compatible
with Python2 and Python3.

Installation
------------

The software is written as much as possible to make use of core Python
components. It requires my own `hcam_widgets <https://github.com/HiPERCAM/hcam_widgets>`_ module.
It also relies on the third party libraries `astropy <http://astropy.org/>`_ for astronomical
calculations and catalog lookup, as well as `ginga <https://ginga.readthedocs.io/en/latest/>`_ for
image display. Optionally, you can also use `astroquery <https://astroquery.readthedocs.io>`_ to expand
the range of surveys one can download images from.

Installing using ``pip`` should take care of these dependencies. Simply install with::

 pip install hcam_finder

or if you don't have root access::

 sudo pip install hcam_finder

or::

 pip install --user hcam_finder

* Free software: MIT license
* Documentation: https://hcam-finder.readthedocs.io.



