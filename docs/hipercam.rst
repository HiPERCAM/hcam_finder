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

Windows
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

Synchronising Windows
`````````````````````

If on-chip binning is enabled, it is possible to define windows that do not align with the
boundarys of the binned pixels. This is fine, but it does mean that one cannot bin
calibration frames taken with 1x1 binning (such as sky flats) to match the windowed data.
If windows are not synchronised in this manner, the :guilabel:`Sync` button will be enabled.
Clicking this will align the windows with the boundaries of binned pixels.

.. _clear_mode:

Clear Mode
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

Clear mode is also enabled automatically when :ref:`nod`, since not clearing the CCD would
lead to trailing of bright stars in the images.

.. _drift_mode:

Drift Mode
----------

Drift mode is used to enable the highest frame rates.

.. _nod:

Nodding the Telescope
---------------------