# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
import tempfile
import threading
import os
import six

import numpy as np
from ginga.util import catalog, dp, wcs
from ginga.canvas.types.all import Circle
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.coordinates.name_resolve import NameResolveError

import hcam_widgets.widgets as w
from hcam_widgets.tkutils import get_root

from .finding_chart import make_finder
from .shapes import CCDWin

has_astroquery = True
try:
    from .skyview import SkyviewImageServer
except ImportError:
    has_astroquery = False

if not six.PY3:
    import Tkinter as tk
else:
    import tkinter as tk

# Image Archives
DSS_URL = "http://archive.eso.org/dss/dss?ra=%(ra)s&dec=%(dec)s&mime-type=application/x-fits&x=%(width)s&y=%(height)s"
DSS2R_URL = DSS_URL + "&Sky-Survey=DSS2-red"
DSS2B_URL = DSS_URL + "&Sky-Survey=DSS2-blue"
DSS2IR_URL = DSS_URL + "&Sky-Survey=DSS2-infrared"
image_archives = [('ESO', 'ESO DSS', catalog.ImageServer, DSS_URL, "ESO DSS archive"),
                  ('ESO', 'ESO DSS2 Red', catalog.ImageServer, DSS2R_URL, "ESO DSS2 Red"),
                  ('ESO', 'ESO DSS2 Blue', catalog.ImageServer, DSS2B_URL, "ESO DSS2 Blue"),
                  ('ESO', 'ESO DSS2 IR', catalog.ImageServer, DSS2IR_URL, "ESO DSS2 IR")]

if has_astroquery:
    image_archives.extend([
        ('SDSS', 'SDSS u', SkyviewImageServer, "SDSSu", "Skyview SDSS g"),
        ('SDSS', 'SDSS g', SkyviewImageServer, "SDSSg", "Skyview SDSS g"),
        ('SDSS', 'SDSS r', SkyviewImageServer, "SDSSr", "Skyview SDSS r"),
        ('SDSS', 'SDSS i', SkyviewImageServer, "SDSSi", "Skyview SDSS i"),
        ('SDSS', 'SDSS z', SkyviewImageServer, "SDSSz", "Skyview SDSS z"),
        ('2MASS', '2MASS J', SkyviewImageServer, "2MASS-J", "Skyview 2MASS J")
    ])


@u.quantity_input(px_val=u.pix)
@u.quantity_input(px_scale=u.arcsec/u.pix)
def _px_deg(px_val, px_scale):
    """
    convert from pixels to degrees
    """
    return px_val.to(
        u.deg,
        equivalencies=u.pixel_scale(px_scale)
    ).value


@u.quantity_input(deg_val=u.deg)
@u.quantity_input(px_scale=u.arcsec/u.pix)
def _deg_px(deg_val, px_scale):
    """
    convert from degrees/arcmins etc to pixels
    """
    return deg_val.to(
        u.pix,
        equivalencies=u.pixel_scale(px_scale)
    ).value


class TelChooser(tk.Menu):
    """
    Provides a menu to choose the telescope.

    The telescope setting affects the signal/noise calculations
    and routines for pulling RA/Dec etc from the TCS.
    """
    def __init__(self, master, command, *args):
        """
        Parameters
        ----------
        master : tk.Widget
            the containing widget, .e.g toolbar menu
        """
        tk.Menu.__init__(self, master, tearoff=0)
        g = get_root(self).globals

        self.val = tk.StringVar()
        tel = g.cpars.get('telins_name', list(g.TINS)[0])
        self.val.set(tel)
        self.val.trace('w', self._change)
        for tel_name in g.TINS.keys():
            self.add_radiobutton(label=tel_name, value=tel_name, variable=self.val)
        self.args = args
        self.root = master
        self.command = command

    def _change(self, *args):
        g = get_root(self).globals
        g.cpars['telins_name'] = self.val.get()
        g.count.update()
        self.command()


class FovSetter(tk.LabelFrame):

    overlay_names = ['ccd_overlay']

    def __init__(self, master, fitsimage, logger):
        """
        This is an abstract class for a widget for displaying images and CCD setups.

        fitsimage is reverence to ImageViewCanvas.

        Normally, concrete classes will only have to implement _make_ccd and window_string.
        More complex concrete classes may have to also change the overlay names and provide
        a custom draw_ccd method.
        """
        tk.LabelFrame.__init__(self, master, pady=2, text='Object')

        self.fitsimage = fitsimage

        g = get_root(self).globals
        self.set_telins(g)

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
        self.targName.bind('<Return>', lambda event: self.query_simbad())
        self.targName.grid(row=row, column=column, sticky=tk.W)

        row += 1
        self.targCoords = w.TextEntry(self, 22)
        self.targCoords.grid(row=row, column=column, sticky=tk.W)

        row += 1
        surveyList = [archive[1] for archive in image_archives]
        self.surveySelect = w.Choice(self, surveyList, width=20)
        self.surveySelect.grid(row=row, column=column, sticky=tk.W)

        row += 1
        self.ra = w.Sexagesimal(self, callback=self.update_pointing_cb, unit='hms', width=10)
        self.ra.grid(row=row, column=column, sticky=tk.W)

        row += 1
        self.dec = w.Sexagesimal(self, callback=self.update_pointing_cb, unit='dms', width=10)
        self.dec.grid(row=row, column=column, sticky=tk.W)

        row += 1
        self.pa = w.PABox(self, 0.0, 0.0, 359.99, self.update_rotation_cb,
                          False, True, width=6, nplaces=2)
        self.pa.grid(row=row, column=column, sticky=tk.W)

        column += 1
        row = 0
        self.query = tk.Button(self, width=14, fg='black', bg=g.COL['main'],
                               text='Query Simbad', command=self.query_simbad)
        self.query.grid(row=row, column=column, sticky=tk.W)

        row += 2
        self.launchButton = tk.Button(self, width=14, fg='black',
                                      text='Load Image', bg=g.COL['main'],
                                      command=self.set_and_load)
        self.launchButton.grid(row=row, column=column, sticky=tk.W)

        self.imfilepath = None
        self.logger = logger

        # add callbacks to fits viewer for dragging FOV around
        self.fitsimage.canvas.add_callback('cursor-down', self.click_cb)
        self.fitsimage.canvas.add_callback('cursor-move', self.click_drag_cb)
        self.fitsimage.canvas.add_callback('cursor-up', self.click_release_cb)
        self.currently_moving_fov = False
        self.currently_rotating_fov = False

        # Add our image servers
        self.bank = catalog.ServerBank(self.logger)
        for (longname, shortname, klass, url, description) in image_archives:
            obj = klass(self.logger, longname, shortname, url, description)
            self.bank.addImageServer(obj)
        self.tmpdir = tempfile.mkdtemp()

        # current dither index
        self.dither_index = 0

        # catalog servers
        """
        for longname in conesearch.list_catalogs():
            shortname = longname
            url = ""    # astropy conesearch doesn't need URL
            description = longname
            obj = catalog.AstroPyCatalogServer(logger, longname, shortname,
                                               url, description)
            self.bank.addCatalogServer(obj)
        """

        # canvas that we will draw on
        self.canvas = fitsimage.canvas

    def targetMarker(self):
        g = get_root(self).globals
        coo = SkyCoord(self.targCoords.value(),
                       unit=(u.hour, u.deg))
        image = self.fitsimage.get_image()
        x, y = image.radectopix(coo.ra.deg, coo.dec.deg)
        size = 10 if g.cpars['telins_name'] == 'WHT' else 3
        circ = Circle(x, y, size, fill=True,
                      color='red', fillalpha=0.3)
        self.canvas.deleteObjectByTag('Target')
        self.canvas.add(circ, tag='Target', redraw=True)

    def window_string(self):
        raise NotImplementedError

    def publish(self):
        g = get_root(self).globals
        arr = self.fitsimage.get_image_as_array()
        make_finder(self.logger, arr, self.targName.value(), g.cpars['telins_name'],
                    self.ra.as_string(), self.dec.as_string(), self.pa.value(),
                    self.window_string())

    @property
    def servername(self):
        return self.surveySelect.value()

    def click_cb(self, *args):
        canvas, event, x, y = args
        try:
            obj = self.canvas.get_object_by_tag('ccd_overlay')
            self.currently_moving_fov = obj.contains(x, y)
            if self.currently_moving_fov:
                self.ref_pos_x = x
                self.ref_pos_y = y
            else:
                mainCCD = None
                for thing in obj.objects:
                    if thing.name == 'mainCCD':
                        mainCCD = thing
                points = np.array(mainCCD.points)
                ref = np.array((x, y))
                dists = np.sum(np.sqrt((points-ref)**2), axis=1)
                if np.any(dists < 20):
                    self.currently_rotating_fov = True
                    self.ref_pa = np.degrees(
                        np.arctan2(y - self.ctr_y, x - self.ctr_x))
        except Exception as err:
            errmsg = "failed to draw CCD: {}".format(str(err))
            self.logger.warn(errmsg)

    def click_drag_cb(self, *args):
        canvas, event, x, y = args
        image = self.fitsimage.get_image()
        if self.currently_moving_fov and image is not None:
            xoff = x - self.ref_pos_x
            yoff = y - self.ref_pos_y
            new_ra, new_dec = image.pixtoradec(self.ctr_x + xoff,
                                               self.ctr_y + yoff)
            self.ref_pos_x = x
            self.ref_pos_y = y
            # update ra, dec boxes; triggers redraw callback
            self.ra.set(new_ra)
            self.dec.set(new_dec)
        elif self.currently_rotating_fov and image is not None:
            pa = np.degrees(np.arctan2(y - self.ctr_y, x - self.ctr_x))
            delta_pa = pa - self.ref_pa
            if not self.EofN:
                delta_pa *= -1
            self.pa.set(self.pa.value() + delta_pa)
            self.ref_pa = pa

    def click_release_cb(self, *args):
        canvas, event, x, y = args
        self.currently_moving_fov = False
        self.currently_rotating_fov = False

    def set_telins(self, g):
        telins = g.cpars['telins_name']
        self.px_scale = g.cpars[telins]['px_scale'] * u.arcsec/u.pix
        self.nxtot = g.cpars[telins]['nxtot'] * u.pix
        self.nytot = g.cpars[telins]['nytot'] * u.pix
        self.fov_x = _px_deg(self.nxtot, self.px_scale)
        self.fov_y = _px_deg(self.nytot, self.px_scale)

        # rotator centre position in pixels
        self.rotcen_x = g.cpars[telins]['rotcen_x'] * u.pix
        self.rotcen_y = g.cpars[telins]['rotcen_y'] * u.pix
        # is image flipped E-W?
        self.flipEW = g.cpars[telins]['flipEW']
        self.fitsimage.t_['flip_x'] = self.flipEW
        # does increasing PA rotate towards east from north?
        self.EofN = g.cpars[telins]['EofN']
        # rotator position in degrees when chip runs N-S
        self.paOff = g.cpars[telins]['paOff']
        if hasattr(self, 'fitsimage'):
            self.draw_ccd()

    @property
    def ctr_ra_deg(self):
        return self.ra.value()

    @property
    def ctr_dec_deg(self):
        return self.dec.value()

    def query_simbad(self):
        g = get_root(self).globals
        try:
            try:
                coo = SkyCoord.from_name(self.targName.value())
            except NameResolveError:
                # see if we can get coords from name itself
                coo = SkyCoord.from_name(self.targName.value(), parse=True)
        except NameResolveError:
            self.targName.config(bg='red')
            self.logger.warn(msg='Could not resolve target')
            return
        self.targName.config(bg=g.COL['main'])
        self.targCoords.set(coo.to_string(style='hmsdms', sep=':'))

    def update_pointing_cb(self, *args):
        image = self.fitsimage.get_image()
        if image is None:
            return
        try:
            objs = [self.canvas.get_object_by_tag(name) for name in self.overlay_names]
            ctr_x, ctr_y = image.radectopix(self.ctr_ra_deg, self.ctr_dec_deg)
            self.ctr_x, self.ctr_y = ctr_x, ctr_y
            old_x, old_y = image.radectopix(self.ra_as_drawn, self.dec_as_drawn)
            for obj in objs:
                if obj is not None:
                    obj.move_delta(ctr_x - old_x, ctr_y - old_y)
            self.canvas.update_canvas()
            self.ra_as_drawn = self.ctr_ra_deg
            self.dec_as_drawn = self.ctr_dec_deg
        except Exception:
            self.draw_ccd(*args)

    def update_rotation_cb(self, *args):
        image = self.fitsimage.get_image()
        if image is None:
            return
        try:
            objs = [self.canvas.get_object_by_tag(name) for name in self.overlay_names]
            pa = self.pa.value() - self.paOff
            if not self.EofN:
                pa *= -1
            for obj in objs:
                if obj is not None:
                    obj.rotate(pa - self.pa_as_drawn, self.ctr_x, self.ctr_y)
            self.canvas.update_canvas()
            self.pa_as_drawn = pa
        except Exception:
            self.draw_ccd(*args)

    def _chip_cen(self):
        """
        return chip centre in ra, dec
        """
        xoff_hpix = (self.nxtot/2 - self.rotcen_x)
        yoff_hpix = (self.nytot/2 - self.rotcen_y)
        yoff_deg = _px_deg(yoff_hpix, self.px_scale)
        xoff_deg = _px_deg(xoff_hpix, self.px_scale)

        if not self.flipEW:
            xoff_deg *= -1

        return wcs.add_offset_radec(self.ctr_ra_deg, self.ctr_dec_deg,
                                    xoff_deg, yoff_deg)

    def _make_win(self, xs, ys, nx, ny, image, **params):
        """
        Make a canvas object to represent a CCD window

        Parameters
        ----------
        xs, ys, nx, ny : float
            xstart, ystart and size in instr pixels
        image : `~ginga.AstroImage`
            image reference for calculating scales
        params : dict
            parameters passed straight through to canvas object
        Returns
        -------
        win : `~ginga.canvas.CompoundObject`
            ginga canvas object to draw on FoV
        """
        # need bottom left coord and xy size of window in degrees
        # offset of bottom left coord window from chip ctr in degrees
        xoff_hpix = (xs*u.pix - self.rotcen_x)
        yoff_hpix = (ys*u.pix - self.rotcen_y)
        yoff_deg = _px_deg(yoff_hpix, self.px_scale)
        xoff_deg = _px_deg(xoff_hpix, self.px_scale)

        if not self.flipEW:
            xoff_deg *= -1

        ll_ra, ll_dec = wcs.add_offset_radec(self.ctr_ra_deg, self.ctr_dec_deg,
                                             xoff_deg, yoff_deg)
        xsize_deg = _px_deg(nx*u.pix, self.px_scale)
        ysize_deg = _px_deg(ny*u.pix, self.px_scale)
        if not self.flipEW:
            xsize_deg *= -1
        return CCDWin(ll_ra, ll_dec, xsize_deg, ysize_deg, image, **params)

    def _make_ccd(self, image):
        """
        Converts the current instrument settings to a ginga canvas object.

        Must be implemented by concrete sub class
        """
        raise NotImplementedError()

    def draw_ccd(self, *args):
        image = self.fitsimage.get_image()
        if image is None:
            return

        try:
            pa = self.pa.value() - self.paOff
            if not self.EofN:
                pa *= -1
        except Exception as err:
            errmsg = "failed to find rotation: {}".format(str(err))
            self.logger.error(errmsg)

        try:
            obj = self._make_ccd(image)
            obj.showcap = True

            self.canvas.deleteObjectByTag('ccd_overlay')
            self.canvas.add(obj, tag='ccd_overlay', redraw=False)
            # rotate
            obj.rotate(pa, self.ctr_x, self.ctr_y)
            obj.color = 'red'

            # save old values so we don't have to recompute FOV if we're just moving
            self.pa_as_drawn = pa
            self.ra_as_drawn, self.dec_as_drawn = self.ctr_ra_deg, self.ctr_dec_deg
        except Exception as err:
            errmsg = "failed to draw CCD: {}".format(str(err))
            self.logger.error(msg=errmsg)

        self.canvas.update_canvas()

    def create_blank_image(self):
        self.fitsimage.onscreen_message("Creating blank field...",
                                        delay=1.0)
        image = dp.create_blank_image(self.ctr_ra_deg, self.ctr_dec_deg,
                                      2*self.fov,
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
        if t.is_alive():
            self.logger.debug(msg='checking if image has arrrived')
            self.after(500, self._check_image_load, t)
        else:
            # load image into viewer
            if self.imfilepath is None:
                # no image from server
                msg = 'No image for this location in {}'.format(
                    self.servername
                )
                self.fitsimage.onscreen_message(msg)
                return

            try:
                get_root(self).load_file(self.imfilepath)
            except Exception as err:
                errmsg = "failed to load file {}:\n{}".format(
                    self.imfilepath,
                    str(err)
                )
                self.logger.error(msg=errmsg)
                self.fitsimage.onscreen_message(errmsg)
            else:
                self.draw_ccd()
                self.targetMarker()
            finally:
                self.fitsimage.onscreen_message(None)

    def _load_image(self):
        try:
            fov_deg = 5*max(self.fov_x, self.fov_y)
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
            print(self.servername, self.bank.getServerNames())
            dstpath = self.bank.getImage(self.servername, filepath, **params)
        except Exception as err:
            errmsg = "Failed to download sky image: {}".format(str(err))
            self.logger.error(msg=errmsg)
            self.imfilepath = None
            return

        self.imfilepath = dstpath
