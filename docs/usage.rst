=====
Usage
=====

To start ``hfinder``, simply type::

    hfinder

Other finding chart tools are started in a similar way, e.g. ``ufinder`` to start the ULTRACAM
tool and ``usfinder`` for the ULTRASPEC tool. The main GUI window will display, shown below
(windows for all tools are similar).

.. image:: images/main.png
    :alt: main gui window
    :align: center

Telescope Selection
-------------------

Before proceeding any further, make sure the correct telescope is selected using the
:guilabel:`Telescope` menu item. If you wish to make your selection permanent, see
:ref:`config-file`.

Target Setup
------------

Enter your Object Name in the appropriate box. You can query
`SIMBAD <http://simbad.u-strasbg.fr/simbad/>`_ using your entered target name by
pressing the :guilabel:`Query Simbad` button. If SIMBAD lookup fails, you can enter
your target coordinates by hand.

Select a sky survey to grab images from and press the :guilabel:`Load Image` button. If an
image is available in the selected sky survey it will be downloaded and displayed, along with
the HiPERCAM field of view (FoV).

Manipulating the FoV
---------------------

You can change the telescope pointing either by click-dragging the FoV, or by changing the values
in the :guilabel:`Tel. RA` and :guilabel:`Tel. Dec` fields. Like all numerical entry boxes in ``hfinder``
the right and left arrow keys will increment or decrement the values. Holding :kbd:`Shift` whilst
pressing the arrow keys will make larger changes.

The Sky PA can be click-dragging on the corner of the displayed FoV. This will rotate the FoV. Alternately,
edit the value in the :guilabel:`Tel. PA` field.

Interacting with the displayed image
------------------------------------

Basic instructions for manipulating the displayed image (pan, zoom etc) are displayed below the
image itself. ``hfinder`` uses the `ginga <https://ginga.readthedocs.io/en/latest/>`_ package
for image display. For a fuller reference about interacting with the image area, see the
`Ginga Quick Reference <http://ginga.readthedocs.io/en/latest/quickref.html/>`_.

Choosing an Instrument Setup
----------------------------

Each finding chart tool includes a panel that is used to configure the instrument. For example, the
instrument panel for ``hfinder`` is shown below:

.. image:: images/inst.png
    :alt: instrument config panel
    :align: center

As you make changes to this panel, the displayed FoV will update to reflect your choices
of readout mode and window settings. The exposure time, cadence and signal-to-noise
estimates in the panel above will also update.

Use this panel to select an instrument setup that best suits your observing needs. For more details of
the different settings, and a guide to using each instrument, see:

- :doc:`Using HiPERCAM <hipercam>`
- :doc:`Using ULTRACAM <ultracam>`
- :doc:`Using ULTRASPEC <ultraspec>`

Once you've got a setup and a pointing you are happy with, you can save a finding chart
and export an instrument configuration file. To do this, select
:menuselection:`Save --> Finding Chart`. For HiPERCAM, you should also save a
JSON copy of your instrument setup by selecting :menuselection:`Save --> Inst. Setup File`
respectively. This will create two files which you should upload as part of your
phase II submission.

.. _config-file:

Changing the config file
------------------------

A default configuration is written to :file:`.hfinder/config` in the user's home directory.
This has many settings in it, the vast majority of which should not normally be changed by
the user. Two which are of interest are ``telins_name``, which sets the default telescope.
Set this to ``GTC`` or ``WHT`` as required.

The other option which may be useful is the ``font_size``. Change this setting to increase or
decrease the font size if the GUI does not fit well on your screen.
