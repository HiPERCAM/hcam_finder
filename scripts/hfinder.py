#! /usr/bin/env python
#
# example2_tk.py -- Simple, configurable FITS viewer.
#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#
from __future__ import print_function

import sys, os
import logging
import tkinter as tk
from tkinter.filedialog import askopenfilename

from ginga import AstroImage
from ginga.util import wcs, dp, catalog
from ginga.tkw.ImageViewTk import ImageViewCanvas

import hcam_drivers.utils as utils
from hcam_drivers.globals import Container
import hcam_drivers.utils.widgets as w
from hcam_drivers.config import (load_config, write_config,
                                 check_user_dir, dump_app)
from hcam_drivers.utils import hcam

STD_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s'


class FitsViewer(tk.Tk):

    def __init__(self, logger):
        super(FitsViewer, self).__init__()
        self.logger = logger

        # add a container object
        self.globals = Container()
        self.globals.cpars = dict()
        load_config(self.globals)
        self.globals.cpars['file_logging_on'] = 0
        self.globals.cpars['hcam_server_on'] = 0
        self.globals.cpars['eso_server_online'] = False
        # style
        utils.addStyle(self)


        # Now we make the HiPERCAM widgets
        # including some widgets that will not be displayed,
        # because the hipercam widgets want to talk to them.
        # The order here is determined by the fact that some widgets
        # need to reference the simpler ones, so they have to
        # initialised first.
        self.globals.clog = w.LabelGuiLogger('CMM', self, 5, 56, 'Command log')
        self.globals.rlog = w.LabelGuiLogger('RSP', self, 5, 56, 'Response log')

        # This one is actually displayed!
        # Instrument params
        self.globals.ipars = hcam.InstPars(self)

        self.globals.rpars = hcam.RunPars(self)
        self.globals.info = w.InfoFrame(self)
        self.globals.observe = hcam.Observe(self)

        # counts and S/N frame. Also displayed!
        self.globals.count = hcam.CountsFrame(self)

        # container canvas
        viewerFrame = tk.Canvas(self, bg="grey", height=512, width=512)
        # GINGA Image view
        fi = ImageViewCanvas(logger)
        fi.set_widget(viewerFrame)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        fi.enable_autozoom('on')
        fi.enable_draw(False)
        fi.set_callback('none-move', self.motion)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_setActive(True)
        fi.show_pan_mark(False)
        self.fitsimage = fi

        bd = fi.get_bindings()
        bd.enable_all(True)

        # canvas that we will draw on
        DrawingCanvas = fi.getDrawClass('drawingcanvas')
        canvas = DrawingCanvas()
        canvas.enable_draw(True)
        #canvas.enable_edit(True)
        canvas.setSurface(fi)
        self.canvas = canvas
        # add canvas to view
        fi.add(canvas)
        canvas.ui_setActive(True)

        fi.configure(512, 512)

        infoFrame = tk.Frame(self)
        self.readout = tk.Label(infoFrame, text='')

        # now layout
        self.globals.ipars.grid(row=0, column=0, sticky=tk.W+tk.N, padx=10, pady=10)
        self.globals.count.grid(row=1, column=0, sticky=tk.W+tk.N, padx=10, pady=10)
        viewerFrame.grid(row=0, column=1, sticky=tk.W+tk.N, padx=10, pady=10,
                         rowspan=3)
        infoFrame.grid(row=4, column=1, sticky=tk.W+tk.N, padx=10, pady=10)

        # configure
        self.title('hfinder')
        self.protocol("WM_DELETE_WINDOW", self.quit)

        # run checks
        self.globals.ipars.check()
        self.update()

    def get_widget(self):
        return self

    def set_drawparams(self, evt):
        kind = self.wdrawtype.get()
        color = self.wdrawcolor.get()
        alpha = 0.4
        fill = True

        params = {'color': color,
                  'alpha': alpha,
                  }
        if kind in ('circle', 'rectangle', 'polygon', 'triangle',
                    'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = fill
            params['fillalpha'] = alpha

        self.canvas.set_drawtype(kind, **params)

    def clear_canvas(self):
        self.canvas.deleteAllObjects()

    def load_file(self, filepath):
        self.update()
        image = AstroImage.AstroImage(logger=self.logger)
        image.load_file(filepath)
        self.fitsimage.set_image(image)

    def open_file(self):
        filename = askopenfilename(filetypes=[("allfiles", "*"),
                                              ("fitsfiles", "*.fits")])
        self.load_file(filename)

    def motion(self, fitsimage, button, data_x, data_y):

        # Get the value under the data coordinates
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = fitsimage.get_data(int(data_x+0.5), int(data_y+0.5))
        except Exception:
            value = None

        fits_x, fits_y = data_x + 1, data_y + 1
        # Calculate WCS RA
        try:
            # NOTE: image function operates on DATA space coords
            image = fitsimage.get_image()
            if image is None:
                # No image loaded
                return
            ra_txt, dec_txt = image.pixtoradec(fits_x, fits_y,
                                               format='str', coords='fits')
        except Exception as e:
            self.logger.warning("Bad coordinate conversion: %s" % (
                str(e)))
            ra_txt = 'BAD WCS'
            dec_txt = 'BAD WCS'

        text = "RA: %s  DEC: %s  X: %.2f  Y: %.2f  Value: %s" % (
            ra_txt, dec_txt, fits_x, fits_y, value)
        self.readout.config(text=text)

    def quit(self):
        self.destroy()
        return True


def main():

    logger = logging.getLogger("example1")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(STD_FORMAT)
    stderrHdlr = logging.StreamHandler()
    stderrHdlr.setFormatter(fmt)
    logger.addHandler(stderrHdlr)

    fv = FitsViewer(logger)
    fv.open_file()
    top = fv.get_widget()
    top.mainloop()


if __name__ == "__main__":
    main()

# END
