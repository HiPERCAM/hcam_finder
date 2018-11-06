=========
HiPERCAM
=========

The primary consideration when observing with HiPERCAM is to realise that its frame-transfer
CCDs have no shutter. Instead, an image is rapidly moved into the storage area, which begins
a new exposure in the image area. The image continues to expose whilst the storage area is
reading out; this sets a *minimum exposure time* equal to the time needed to readout an image.

For a full-frame image with slow readout speed, this minimum exposure time is around 2.1 seconds.
Longer exposures can be obtained by entering an :guilabel:`Exposure Delay`, but shorter
exposures will require the use of :ref:`windows`, :ref:`drift_mode` or :ref:`clear_mode`.

Outputs
-------
HiPERCAM has four seperate outputs, or channels, per CCD. The division between these
outputs is clearly shown in the FoV in ``hfinder``. Each of these outputs has slightly
different gains and bias levels; **avoid putting critical targets on the boundary between
outputs**.

.. _windows:

Windowed mode
-------

To enable higher frame rates, HiPERCAM can use one or two windows per output. Since there
are four outputs, we refer to *window quads* to define window settings. You can enable
windowed mode by selecting :guilabel:`Wins` for the :guilabel:`Mode` option in the instrument
setup panel.

A window quad is defined by the x-start positions of the four quadrants, the size of the
windows in x and y, and a y-start value. All windows in a quad must be the same shape, and
all share the same y-start value. Increasing y-start moves the windows in from the edges of
the CCD towards the centre.

If there are two window quads, they cannot overlap in y.

Synchronising windows
`````````````````````

If on-chip binning is enabled, it is possible to define windows that do not align with the
boundarys of the binned pixels. This is fine, but it does mean that one cannot bin
calibration frames taken with 1x1 binning (such as sky flats) to match the windowed data.
If windows are not synchronised in this manner, the :guilabel:`Sync` button will be enabled.
Clicking this will align the windows with the boundaries of binned pixels.

.. _clear_mode:

Clear mode
----------

Sometimes extremely short exposures are needed, even with full frame data. Sky flats would be
one example. It is possible to *clear* the image area of the CCD, just after the storage area
is read out. This allows exposure times as short as 10 microseconds. These short exposures come
at the expense of efficiency, since the charge accumulated whilst the storage area was reading
out is lost.

For example, if the storage area takes 2s to read out, clear mode is enabled and the exposure delay
is set to 1s, then an image would be take every 3s with a duty cycle of 30%.

As a result, if the user needs short exposure times to avoid saturation, it is often
preferable to use a faster readout speed, :ref:`windows` or :ref:`drift_mode` to achieve
this without sacrificing observing efficiency.

Clear mode is enabled by selecting the :guilabel:`Clear` checkbox.

.. _drift_mode:

Drift mode
----------

Drift mode is used to enable the highest frame rates. Instead of shifting the entire image area
into the storage area at the end of each exposure, only a small window at the bottom of the CCD
is shifted into the storage area. This minimises the dead time involved in shifting charge to the
storage area and allows frame rates of ~1 kHz for relatively small windows.

In drift mode, a number of windows are present in the storage area at any one time. At the same
time, any charge in pixels above the windows is eventually clocked into the windows, and becomes
part of that frame. To prevent bright stars from contaminating the drift mode data, a blade
is inserted into the focal plane, blocking off most of the image area of the CCD. Because the
windows in drift mode spend longer on the chip, they accumulate dark current; drift mode should
only be used for frame rates faster than ~10 Hz as a result.

For more information about drift mode, see the
`ULTRACAM instrument paper <https://ui.adsabs.harvard.edu/#abs/2007MNRAS.378..825D/abstract>`_
and it's appendix.

Exposure multipliers
--------------------

The instrument setup will determine the exposure time and cadence of your data. It is unlikely
that this exposure time will be optimal for your target in all bands. Many objects will need
longer exposures at the blue or red extremes. HiPERCAM supports *exposure multipliers*. These
allow a CCD to be readout once every N exposures, and can be changed in the fields labelled
:guilabel:`nu`, :guilabel:`ng`...

With, for example, nu=2, the u-band CCD will read out every two frames. This allows you to
double the exposure time for the u-band CCD only. Note that the S/N estimates in ``hfinder``
do *not* take account of the exposure multipliers.

Miscellaneous settings
-----------------------

The remaining settings you can change are described below:

Num. exposures
    The number of exposures to take before stopping. Most HiPERCAM users will want to take a
    continuous series of exposures and stop after an alloted time. In which case this field
    should be set to 0.

Readout speed
    Fast readout speed reduces the minimum exposure time in full-frame readout from 2.2s to 1.3s.
    This comes at the expense of increased readout noise. The impact of this on the S/N of your
    target is shown in ``hfinder``.

Fast clocks
    Users wanting the ultimate in high speed performance can enable this option. This increases the
    rate at which charge is clocked in the CCDs. It will have an impact on charge transfer efficiency.
    As of today, this impact has not been well characterised, but we do not think it is serious.

Overscan
    Enable the recording of the overscan regions at the left and right edges of the chip. Can be
    useful if precise measurement of the bias in each frame is needed. This is important for the
    highest levels of photometric precision, so consider this option for, e.g. exoplanet transit
    observations.


.. _nod:

Dithering the Telescope
---------------------

It is possible to dither the telescope between frames. This can be useful if, for example, you
want to make a flat-field directly from the night sky observations themselves. :ref:`clear_mode`
is always enabled when dithering the telescope, to avoid trails from bright stars appearing
in the image.

The overheads involved in moving the telescope mean that there is little point in
using any mode other than full-frame readout with this option.

If you wish to nod the telescope, check the  :guilabel:`Nodding` checkbox. You will be prompted
for a plain text file specifying the offset pattern you require. The format of this file is a
simple list of *absolute* RA, Dec offsets in arcseconds as shown below::

    0  0
    0  20
    20 20
    20 0
    0  20

This offset pattern will be repeated until your exposures are finished. ``hfinder``
will estimate the impact of nodding on your cadence and overal signal-to-noise.

If you wish to visualise the dithering pattern on the sky, pressing the ``n`` key
will cycle through the dithering pattern.
