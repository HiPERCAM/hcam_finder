# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
import tempfile
import threading
import os
from functools import partial

import tkinter as tk
import numpy as np
from ginga.util import catalog, dp, wcs
from ginga.canvas.types.all import (Path, Polygon, Circle,
                                    CompoundObject)
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.coordinates.name_resolve import NameResolveError
from astropy.vo.client import conesearch

import hcam_widgets.widgets as w
from hcam_widgets.tkutils import get_root

from .finding_chart import make_finder
has_astroquery = True
try:
    from .skyview import SkyviewImageServer
except:
    has_astroquery = False

# Image Archives
image_archives = [('ESO', 'ESO DSS', catalog.ImageServer,
                  "http://archive.eso.org/dss/dss?ra=%(ra)s&dec=%(dec)s&mime-type=application/x-fits&x=%(width)s&y=%(height)s",
                   "ESO DSS archive"),
                  ('ESO', 'ESO DSS2 Red', catalog.ImageServer,
                   "http://archive.eso.org/dss/dss?ra=%(ra)s&dec=%(dec)s&mime-type=application/x-fits&x=%(width)s&y=%(height)s&Sky-Survey=DSS2-red",
                   "ESO DSS2 Red"),
                  ('ESO', 'ESO DSS2 Blue', catalog.ImageServer,
                   "http://archive.eso.org/dss/dss?Sky-Survey=DSS2-blue&ra=%(ra)s&dec=%(dec)s&mime-type=application/x-fits&x=%(width)s&y=%(height)s",
                   "ESO DSS2 Blue"),
                  ('ESO', 'ESO DSS2 IR', catalog.ImageServer,
                   "http://archive.eso.org/dss/dss?Sky-Survey=DSS2-infrared&ra=%(ra)s&dec=%(dec)s&mime-type=application/x-fits&x=%(width)s&y=%(height)s",
                   "ESO DSS2 IR")]

if has_astroquery:
    image_archives.extend([
                    ('SDSS', 'SDSS u', SkyviewImageServer,
                     "SDSSu",
                     "Skyview SDSS g"),
                    ('SDSS', 'SDSS g', SkyviewImageServer,
                     "SDSSg",
                     "Skyview SDSS g"),
                    ('SDSS', 'SDSS r', SkyviewImageServer,
                     "SDSSr",
                     "Skyview SDSS r"),
                    ('SDSS', 'SDSS i', SkyviewImageServer,
                     "SDSSi",
                     "Skyview SDSS i"),
                    ('SDSS', 'SDSS z', SkyviewImageServer,
                     "SDSSz",
                     "Skyview SDSS z"),
                    ('2MASS', '2MASS J', SkyviewImageServer,
                     "2MASS-J",
                     "Skyview 2MASS J")
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


class CCDWin(Polygon):
    def __init__(self, ra_ll_deg, dec_ll_deg, xs, ys,
                 image, **params):
        """
        Shape for drawing ccd window

        Parameters
        ----------
        ra_ll_deg : float
            lower left coordinate in ra (deg)
        dec_ll_deg : float
            lower left y coord in dec (deg)
        xs : float
            x size in degrees
        ys : float
            y size in degrees
        image : `~ginga.AstroImage`
            image to plot Window on
        """
        points_wcs = (
            (ra_ll_deg, dec_ll_deg),
            wcs.add_offset_radec(ra_ll_deg, dec_ll_deg, xs, 0.0),
            wcs.add_offset_radec(ra_ll_deg, dec_ll_deg, xs, ys),
            wcs.add_offset_radec(ra_ll_deg, dec_ll_deg, 0.0, ys)
        )
        self.points = [image.radectopix(ra, dec) for (ra, dec) in points_wcs]
        super(CCDWin, self).__init__(self.points, **params)
        self.name = params.pop('name', 'window')


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

    def __init__(self, master, fitsimage, logger):
        """
        fitsimage is reverence to ImageViewCanvas
        """
        tk.LabelFrame.__init__(self, master, pady=2, text='Object')

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
                          False, True, width=6)
        self.pa.grid(row=row, column=column, sticky=tk.W)

        column += 1
        row = 0
        self.query = tk.Button(self, width=12, fg='black', bg=g.COL['main'],
                               text='Query Simbad', command=self.query_simbad)
        self.query.grid(row=row, column=column, sticky=tk.W)

        row += 2
        self.launchButton = tk.Button(self, width=8, fg='black',
                                      text='Load Image', bg=g.COL['main'],
                                      command=self.set_and_load)
        self.launchButton.grid(row=row, column=column, sticky=tk.W)

        self.fitsimage = fitsimage
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

        # catalog servers
        for longname in conesearch.list_catalogs():
            shortname = longname
            url = ""    # astropy conesearch doesn't need URL
            description = longname
            obj = catalog.AstroPyCatalogServer(logger, longname, shortname,
                                               url, description)
            self.bank.addCatalogServer(obj)

        # canvas that we will draw on
        self.canvas = fitsimage.canvas

        root = get_root(self)
        menubar = tk.Menu(root)
        fileMenu = tk.Menu(menubar, tearoff=0)
        fileMenu.add_command(label='Publish', command=self.publish)

        # telescope chooser
        telChooser_cmd = partial(self.set_telins, g=g)
        telChooser = TelChooser(menubar, telChooser_cmd)

        menubar.add_cascade(label='Telescope', menu=telChooser)
        menubar.add_cascade(label='File', menu=fileMenu)
        root.config(menu=menubar)

    def targetMarker(self):
        coo = SkyCoord(self.targCoords.value(),
                       unit=(u.hour, u.deg))
        image = self.fitsimage.get_image()
        x, y = image.radectopix(coo.ra.deg, coo.dec.deg)
        circ = Circle(x, y, 10, fill=True,
                      color='red', fillalpha=0.3)
        self.canvas.deleteObjectByTag('Target')
        self.canvas.add(circ, tag='Target', redraw=True)

    def window_string(self):
        g = get_root(self).globals
        wframe = g.ipars.wframe
        if g.ipars.isFF():
            winlist = []
        if g.ipars.isDrift():
            winlist = [
                'xsl: {}, xsr: {}, ys: {}, nx: {}, ny: {}'.format(xsl, xsr, ys, nx, ny)
                for (xsl, xsr, ys, nx, ny) in wframe
            ]
        else:
            winlist = [
                'xsll: {}, xslr: {}, xsul: {}, xsur: {}, ys: {}, nx: {}, ny: {}'.format(
                    xsll, xslr, xsul, xsur, ys, nx, ny
                ) for (xsll, xsul, xslr, xsur, ys, nx, ny) in wframe
            ]
        return '\n'.join(winlist)

    def publish(self):
        print('publish')
        arr = self.fitsimage.get_image_as_array()
        make_finder(self.logger, arr, self.targName.value(),
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
            coo = SkyCoord.from_name(self.targName.value())
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
            obj = self.canvas.get_object_by_tag('ccd_overlay')
            ctr_x, ctr_y = image.radectopix(self.ctr_ra_deg, self.ctr_dec_deg)
            self.ctr_x, self.ctr_y = ctr_x, ctr_y
            old_x, old_y = image.radectopix(self.ra_as_drawn, self.dec_as_drawn)
            obj.move_delta(ctr_x - old_x, ctr_y - old_y)
            self.canvas.update_canvas()
            self.ra_as_drawn = self.ctr_ra_deg
            self.dec_as_drawn = self.ctr_dec_deg
        except:
            self.draw_ccd(*args)

    def update_rotation_cb(self, *args):
        image = self.fitsimage.get_image()
        if image is None:
            return
        try:
            obj = self.canvas.get_object_by_tag('ccd_overlay')
            pa = self.pa.value() - self.paOff
            if not self.EofN:
                pa *= -1
            obj.rotate(pa - self.pa_as_drawn, self.ctr_x, self.ctr_y)
            self.canvas.update_canvas()
            self.pa_as_drawn = pa
        except:
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
        Converts the current instrument settings to a ginga canvas object
        """
        # get window pair object from top widget
        g = get_root(self).globals
        wframe = g.ipars.wframe

        # all values in pixel coords of the FITS frame
        # get centre
        ctr_x, ctr_y = image.radectopix(self.ctr_ra_deg, self.ctr_dec_deg)
        self.ctr_x, self.ctr_y = ctr_x, ctr_y

        nx, ny = self.nxtot.value, self.nytot.value
        mainCCD = self._make_win(0, 0, nx, ny, image,
                                 fill=True, fillcolor='blue',
                                 fillalpha=0.3, name='mainCCD')

        # dashed lines to mark quadrants of CCD
        chip_ctr_ra, chip_ctr_dec = self._chip_cen()
        xright, ytop = wcs.add_offset_radec(chip_ctr_ra, chip_ctr_dec,
                                            self.fov_x/2, self.fov_y/2)
        xleft, ybot = wcs.add_offset_radec(chip_ctr_ra, chip_ctr_dec,
                                           -self.fov_x/2, -self.fov_y/2)
        points = [image.radectopix(ra, dec) for (ra, dec) in (
            (chip_ctr_ra, ybot), (chip_ctr_ra, ytop)
        )]
        hline = Path(points, color='red', linestyle='dash', linewidth=2)
        points = [image.radectopix(ra, dec) for (ra, dec) in (
            (xleft, chip_ctr_dec), (xright, chip_ctr_dec)
        )]
        vline = Path(points, color='red', linestyle='dash', linewidth=2)

        # list of objects for compound object
        l = [mainCCD, hline, vline]

        # iterate over window pairs
        # these coords in ccd pixel vaues
        params = dict(fill=True, fillcolor='red', fillalpha=0.3)
        if not g.ipars.isFF():
            if g.ipars.isDrift():
                for xsl, xsr, ys, nx, ny in wframe:
                    l.append(self._make_win(xsl, ys, nx, ny, image, **params))
                    l.append(self._make_win(xsr, ys, nx, ny, image, **params))
            else:
                for xsll, xsul, xslr, xsur, ys, nx, ny in wframe:
                    l.append(self._make_win(xsll, ys, nx, ny, image, **params))
                    l.append(self._make_win(xsul, 1024-ys, nx, -ny, image, **params))
                    l.append(self._make_win(xslr, ys, nx, ny, image, **params))
                    l.append(self._make_win(xsur, 1024-ys, nx, -ny, image, **params))

        obj = CompoundObject(*l)
        obj.editable = True
        return obj

    def draw_ccd(self, *args):
        image = self.fitsimage.get_image()
        if image is None:
            return
        try:
            obj = self._make_ccd(image)
            obj.showcap = True
            pa = self.pa.value() - self.paOff
            if not self.EofN:
                pa *= -1
            self.canvas.deleteObjectByTag('ccd_overlay')
            self.canvas.add(obj, tag='ccd_overlay', redraw=False)
            # rotate
            obj.rotate(pa, self.ctr_x, self.ctr_y)
            obj.color = 'red'

            # save old values so we don't have to recompute FOV if we're just moving
            self.pa_as_drawn = pa
            self.ra_as_drawn, self.dec_as_drawn = self.ctr_ra_deg, self.ctr_dec_deg

            self.canvas.update_canvas()
            # self.fitsimage.set_draw_mode('edit')
            # self.canvas.edit_select(obj)
        except Exception as err:
            errmsg = "failed to draw CCD: {}".format(str(err))
            self.logger.error(msg=errmsg)

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
                self.targetMarker()
                self.fitsimage.onscreen_message(None)

    def _load_image(self):
        try:
            fov_deg = 2*max(self.fov_x, self.fov_y)
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
            return

        self.imfilepath = dstpath
