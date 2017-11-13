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


Observation planning and finding charts for HiPerCAM

``hcam_finder`` provides a Python script ``hfinder`` for generating finding
charts for HiPerCAM on the WHT and GTC. ``hcam_finder`` is written in Python and is based on TKinter. It should be
compatible with Python2 and Python3.

Installation
------------

The software is written as much as possible to make use of core Python
components. It requires my own `hcam_widgets <https://github.com/StuartLittlefair/hcam_widgets>`_ module.
It also relies on the third party libraries `astropy <http://astropy.org/>`_ for astronomical
calculations and catalog lookup, as well as `ginga <https://ginga.readthedocs.io/en/latest/>`_ for
image display. Optionally, you can also use `astroquery <https://astroquery.readthedocs.io>`_ to expand
the range of surveys one can download images from.

Once you have installed these, install with the usual::

 pip install .

or if you don't have root access::

 pip install --user .

* Free software: MIT license
* Documentation: https://hcam-finder.readthedocs.io.



