=========
ULTRACAM
=========

The primary consideration when observing with ULTRACAM is to realise that its frame-transfer
CCDs have no shutter. Instead, an image is rapidly moved into the storage area, which begins
a new exposure in the image area. The image continues to expose whilst the storage area is
reading out; this sets a *minimum exposure time* equal to the time needed to readout an image.

For a full-frame image with slow readout speed, this minimum exposure time is around 2.1 seconds.
Longer exposures can be obtained by entering an :guilabel:`Exposure Delay`, but shorter
exposures will require the use of :ref:`windows`, :ref:`drift_mode` or :ref:`clear_mode`.

Outputs
-------
ULTRACAM has two seperate outputs, or channels, per CCD. Each of these outputs has slightly
different gains and bias levels; **avoid putting critical targets on the boundary between
outputs**.

.. _windows:

Windowed mode
-------------
To enable higher frame rates, ULTRACAM can use up to three windows per output channel. Since there
are two outputs, we refer to *window pairs* to define window settings. You can enable
windowed mode by selecting :guilabel:`Wins` for the :guilabel:`Mode` option in the instrument
setup panel.

A window pair is defined by the x-start positions of each window, the size of the
windows in x and y, and a y-start value. Both windows in a pair must be the same shape, and
all share the same y-start value. Increasing y-start moves the windows in from the edges of
the CCD towards the centre.

If there are two window pairs, they cannot overlap in y.

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

For example, if the storage area takes 6s to read out, clear mode is enabled and the exposure delay
is set to 1s, then an image would be take every 7s with a duty cycle of 14%.

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
longer exposures at the blue or red extremes. ULTRACAM supports *exposure multipliers*. These
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
    Higher readout speeds reduce the time taken to read the storage area and increase the frame rate.
    This comes at the expense of increased readout noise. The impact of this on the S/N of your
    target is shown in ``ufinder``.

Overscan
    Enable the recording of the overscan regions at the left and right edges of the chip. Can be
    useful if precise measurement of the bias in each frame is needed. This is important for the
    highest levels of photometric precision, so consider this option for, e.g. exoplanet transit
    observations.
