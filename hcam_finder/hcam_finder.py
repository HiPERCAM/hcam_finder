# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
import tempfile
import threading
import os
from itertools import product

import tkinter as tk
from ginga.util import catalog, dp
from ginga.canvas.types.all import (Box, Polygon,
                                    CompoundObject)
from astropy import units as u
from astropy.coordinates import SkyCoord, Angle
from astropy.coordinates.name_resolve import NameResolveError

import hcam_drivers.utils.widgets as w
from hcam_drivers.utils import get_root

# Image Archives
image_archives = [('ESO', 'eso', catalog.ImageServer,
                  "http://archive.eso.org/dss/dss?ra=%(ra)s&dec=%(dec)s&mime-type=application/x-fits&x=%(width)s&y=%(height)s",
                   "ESO DSS archive"),
                  ]


class CCDWin(Polygon):
    def __init__(self, ctr_x, ctr_y, xs, ys, **params):
        """
        Shape for drawing ccd window

        Parameters
        ----------
        ctr_x : float
            x centre in image pixels
        ctr_y : float
            y centre in image pixels
        xs : float
            x size in image pixels
        ys : float
            y size in image pixels
        """
        points = ((ctr_x - xs/2, ctr_y - xs/2),
                  (ctr_x + xs/2, ctr_y - xs/2),
                  (ctr_x + xs/2, ctr_y + xs/2),
                  (ctr_x - xs/2, ctr_y + xs/2))
        super(CCDWin, self).__init__(points, **params)


class Sexagesimal(tk.Frame):
    def __init__(self, master, callback=None, unit='hms'):
        """
        Class to enter sexagesimal values. value function returns degrees
        """
        super(Sexagesimal, self).__init__(master, pady=2)
        if unit == 'hms':
            self.unit = u.hourangle
            self.widgets = [w.RangedInt(self, 0, 0, 23, callback, True, width=2),
                            w.RangedInt(self, 0, 0, 59, callback, True, width=2),
                            w.RangedFloat(self, 0.0, 0.0, 59.999, callback, False,
                                          width=6)]
        else:
            self.unit = u.deg
            self.widgets = [w.RangedInt(self, 0, -89, 89, callback, True, width=2),
                            w.RangedInt(self, 0, 0, 59, callback, True, width=2),
                            w.RangedFloat(self, 0.0, 0.0, 59.999, callback, False,
                                          width=6)]
        row = 0
        col = 0
        for nw, widget in enumerate(self.widgets):
            widget.grid(row=row, column=col, sticky=tk.W)
            col += 1
            if nw != len(self.widgets) - 1:
                tk.Label(self, text=':').grid(row=row, column=col, sticky=tk.W)
            col += 1

    def value(self):
        string = ':'.join((str(w.value()) for w in self.widgets))
        angle = Angle(string, unit=self.unit)
        return angle.to(u.deg).value

    def as_string(self):
        return ':'.join((str(w.value()) for w in self.widgets))

    def set(self, value):
        angle = Angle(value, unit=u.deg).to(self.unit)
        string = angle.to_string(sep=':')
        fields = string.split(':')
        for field, widget in zip(fields, self.widgets):
            widget.set(field)


class FovSetter(tk.LabelFrame):

    def __init__(self, master, fitsimage, canvas, logger):
        """
        fitsimage is reverence to ImageViewCanvas
        """
        super(FovSetter, self).__init__(master, pady=2,
                                        text='Object')

        g = get_root(self).globals

        row = 0
        column = 0
        tk.Label(self, text='Object Name').grid(row=row, column=column, sticky=tk.W)

        row += 1
        tk.Label(self, text='or Coords').grid(row=row, column=column, sticky=tk.W)

        row += 2
        tk.Label(self, text='Tel. RA').grid(row=row, column=column, sticky=tk.W)

        row += 1
        tk.Label(self, text='Tel. Dec').grid(row=row, column=column, sticky=tk.W)

        row += 1
        tk.Label(self, text='Tel. PA').grid(row=row, column=column, sticky=tk.W)

        # spacer
        column += 1
        tk.Label(self, text=' ').grid(row=0, column=column)

        row = 0
        column += 1
        self.targName = w.TextEntry(self, 22)
        self.targName.grid(row=row, column=column, sticky=tk.W)

        row += 1
        self.targCoords = w.TextEntry(self, 22)
        self.targCoords.grid(row=row, column=column, sticky=tk.W)

        row += 1
        self.launchButton = tk.Button(self, width=8, fg='black',
                                      text='Load Image', bg=g.COL['main'],
                                      command=self.set_and_load)
        self.launchButton.grid(row=row, column=column, sticky=tk.W)

        row += 1
        self.ra = Sexagesimal(self, callback=self.update_info_cb, unit='hms')
        self.ra.grid(row=row, column=column, sticky=tk.W)

        row += 1
        self.dec = Sexagesimal(self, callback=self.update_info_cb, unit='dms')
        self.dec.grid(row=row, column=column, sticky=tk.W)

        row += 1
        self.pa = w.RangedFloat(self, 0.0, 0.0, 359.99, self.update_info_cb,
                                False, True, width=6)
        self.pa.grid(row=row, column=column, sticky=tk.W)

        column += 1
        row = 0
        self.query = tk.Button(self, width=12, fg='black', bg=g.COL['main'],
                               text='Query Simbad', command=self.query_simbad)
        self.query.grid(row=row, column=column, sticky=tk.W)

        self.fitsimage = fitsimage
        self.imfilepath = None
        self.logger = logger

        self.fov = (10*u.arcmin).to(u.deg).value

        # Add our image servers
        self.bank = catalog.ServerBank(self.logger)
        for (longname, shortname, klass, url, description) in image_archives:
            obj = klass(self.logger, longname, shortname, url, description)
            self.bank.addImageServer(obj)
        self.servername = 'eso'
        self.tmpdir = tempfile.mkdtemp()

        # canvas that we will draw on
        self.canvas = canvas

    @property
    def ctr_ra_deg(self):
        return self.ra.value()

    @property
    def ctr_dec_deg(self):
        return self.dec.value()

    def query_simbad(self):
        g = get_root(self).globals
        try:
            coo = SkyCoord.from_name(self.targName.value())
        except NameResolveError:
            self.targName.config(bg='red')
            self.logger.warn(msg='Could not resolve target')
            return
        self.targName.config(bg=g.COL['main'])
        self.targCoords.set(coo.to_string(style='hmsdms', sep=':'))

    def update_info_cb(self, *args):
        print(args)
        self.draw_ccd(*args)

    def draw_ccd(self, *args):
        try:
            print(self.canvas.get_draw_mode())
            image = self.fitsimage.get_image()
            if image is None:
                return

            ctr_x, ctr_y = image.radectopix(self.ctr_ra_deg, self.ctr_dec_deg)
            self.ctr_x, self.ctr_y = ctr_x, ctr_y

            # list of things to draw
            l = []
            delta_pix = image.calc_radius_xy(ctr_x, ctr_y,
                                             self.fov/2)
            mainCCD = CCDWin(ctr_x, ctr_y, delta_pix, delta_pix,
                             fill=True, fillcolor='blue', fillalpha=0.5)
            l.append(mainCCD)

            obj = CompoundObject(*l)
            obj.editable = True

            pa = -self.pa.value()
            self.canvas.deleteObjectByTag('ccd_overlay')
            self.canvas.add(obj, tag='ccd_overlay', redraw=False)

            #print(obj.get_reference_pt())
            #print(ctr_x, ctr_y)
            #print(obj.get_data_points())
            obj.rotate_by(pa)
            #print(obj.get_reference_pt())
            #print(ctr_x, ctr_y)
            #print(obj.get_data_points())

            self.ccd_overlay = obj
            self.canvas.update_canvas()
            self.canvas.set_draw_mode('edit')
        except Exception as err:
            errmsg = "failed to draw CCD: {}".format(str(err))
            self.logger.error(msg=errmsg)

    def create_blank_image(self):
        self.fitsimage.onscreen_message("Creating blank field...",
                                        delay=1.0)
        image = dp.create_blank_image(self.ctr_ra_deg, self.ctr_dec_deg,
                                      3*self.fov,
                                      0.000047, 0.0,
                                      cdbase=[-1, 1],
                                      logger=self.logger)
        image.set(nothumb=True)
        self.fitsimage.set_image(image)

    def set_and_load(self):
        coo = SkyCoord(self.targCoords.value(),
                       unit=(u.hour, u.deg))
        self.ra.set(coo.ra.deg)
        self.dec.set(coo.dec.deg)
        self.load_image()

    def load_image(self):
        self.fitsimage.onscreen_message("Getting image; please wait...")
        # offload to non-GUI thread to keep viewer somewhat responsive?
        t = threading.Thread(target=self._load_image)
        t.daemon = True
        self.logger.debug(msg='starting image download')
        t.start()
        self.after(1000, self._check_image_load, t)

    def _check_image_load(self, t):
        if t.isAlive():
            self.logger.debug(msg='checking if image has arrrived')
            self.after(500, self._check_image_load, t)
        else:
            # load image into viewer
            try:
                get_root(self).load_file(self.imfilepath)
            except Exception as err:
                errmsg = "failed to load file {}: {}".format(
                    self.imfilepath,
                    str(err)
                )
                self.logger.error(msg=errmsg)
                return
            finally:
                self.draw_ccd()
                self.fitsimage.onscreen_message(None)

    def _load_image(self):
        try:
            fov_deg = 3*self.fov
            ra_txt = self.ra.as_string()
            dec_txt = self.dec.as_string()
            # width and height are specified in arcmin
            wd = 60*fov_deg
            ht = 60*fov_deg

            # these are the params to DSS
            params = dict(ra=ra_txt, dec=dec_txt, width=wd, height=ht)

            # query server and download file
            filename = 'sky.fits'
            filepath = os.path.join(self.tmpdir, filename)
            if os.path.exists(filepath):
                os.unlink(filepath)

            dstpath = self.bank.getImage(self.servername, filepath, **params)
        except Exception as err:
            errmsg = "Failed to download sky image: {}".format(str(err))
            self.logger.error(msg=errmsg)
            return

        self.imfilepath = dstpath
