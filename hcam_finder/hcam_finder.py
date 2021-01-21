# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
import six
from os.path import expanduser
import json
import itertools

from ginga.util import wcs
from ginga.canvas.types.all import (Line, CompoundObject)
from astropy import units as u
from astropy.coordinates import SkyCoord

from hcam_widgets.compo.utils import (InjectionArm, PickoffArm, INJECTOR_THETA, PARK_POSITION)
from hcam_widgets.tkutils import get_root

from .finders import FovSetter
from .shapes import (CompoPatrolArc, CompoFreeRegion)

if not six.PY3:
    import tkFileDialog as filedialog
else:
    from tkinter import filedialog


class HCAMFovSetter(FovSetter):

    overlay_names = ['ccd_overlay', 'compo_overlay']

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

    def saveconf(self):
        fname = filedialog.asksaveasfilename(
            initialdir=expanduser("~"),
            defaultextension='.json',
            filetypes=[('config files', '.json')],
            title='Name of setup file')
        if not fname:
            print('Aborted save to disk')
            return False

        g = get_root(self).globals
        data = dict()
        data['appdata'] = g.ipars.dumpJSON()

        # add user info that we should know of
        # includes target, user and proposal
        user = dict()
        user['target'] = self.targName.value()
        data['user'] = user

        # target info
        target = dict()
        target['target'] = self.targName.value()
        targ_coord = SkyCoord(self.targCoords.value(), unit=(u.hour, u.deg))
        target['TARG_RA'] = targ_coord.ra.to_string(sep=':', unit=u.hour, pad=True, precision=2)
        target['TARG_DEC'] = targ_coord.dec.to_string(sep=':', precision=1, unit=u.deg,
                                                      alwayssign=False, pad=True)
        target['RA'] = self.ra._value.to_string(sep=':', unit=u.hour, pad=True, precision=2)
        target['DEC'] = self.dec._value.to_string(sep=':', precision=1, pad=True, unit=u.deg, alwayssign=False)
        target['PA'] = self.pa.value()
        data['target'] = target

        # write file
        with open(fname, 'w') as of:
            of.write(json.dumps(data, sort_keys=True, indent=4,
                                separators=(',', ': ')))
        print('Saved setup to ' + fname)
        return True

    def _step_ccd(self):
        """
        Move CCD to next nod position
        """
        g = get_root(self).globals
        try:
            np = g.ipars.nodPattern
            if not np:
                raise ValueError('no nod pattern defined')
            nd = len(np['ra'])
            di = self.dither_index % nd
            raoff = np['ra'][di]
            decoff = np['dec'][di]
            self.dither_index += 1
        except Exception as err:
            self.logger.warn('could not get dither position {}: {}'.format(di, str(err)))
            return

        self.logger.info('moving CCD to dither position {:d} ({} {})'.format(
            di, raoff, decoff
        ))

        # get new dither cen
        ra, dec = wcs.add_offset_radec(
            self.ctr_ra_deg, self.ctr_dec_deg,
            raoff/3600., decoff/3600.)
        image = self.fitsimage.get_image()
        xc, yc = image.radectopix(self.ra_as_drawn, self.dec_as_drawn)
        xn, yn = image.radectopix(ra, dec)
        # update latest dither centre
        self.ra_as_drawn, self.dec_as_drawn = ra, dec

        obj = self.canvas.get_object_by_tag('ccd_overlay')
        obj.move_delta(xn-xc, yn-yc)
        self.canvas.update_canvas()

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
        points = list(itertools.chain.from_iterable(points))
        hline = Line(*points, color='red', linestyle='dash', linewidth=2)

        points = [image.radectopix(ra, dec) for (ra, dec) in (
            (xleft, chip_ctr_dec), (xright, chip_ctr_dec)
        )]
        points = list(itertools.chain.from_iterable(points))
        vline = Line(*points, color='red', linestyle='dash', linewidth=2)

        # list of objects for compound object
        obl = [mainCCD, hline, vline]

        # iterate over window pairs
        # these coords in ccd pixel vaues
        params = dict(fill=True, fillcolor='red', fillalpha=0.3)
        if not g.ipars.isFF():
            if g.ipars.isDrift():
                for xsl, xsr, ys, nx, ny in wframe:
                    obl.append(self._make_win(xsl, ys, nx, ny, image, **params))
                    obl.append(self._make_win(xsr, ys, nx, ny, image, **params))
            else:
                for xsll, xsul, xslr, xsur, ys, nx, ny in wframe:
                    obl.append(self._make_win(xsll, ys, nx, ny, image, **params))
                    obl.append(self._make_win(xsul, 1024-ys, nx, -ny, image, **params))
                    obl.append(self._make_win(xslr, ys, nx, ny, image, **params))
                    obl.append(self._make_win(xsur, 1024-ys, nx, -ny, image, **params))

        obj = CompoundObject(*obl)
        obj.editable = True
        return obj

    def _make_compo(self, image):
        # get COMPO widget from main GUI
        g = get_root(self).globals

        compo_angle = g.compo_hw.setup_frame.pickoff_angle.value()
        compo_side = g.compo_hw.setup_frame.injection_side.value()

        # get chip coordinates - COMPO is aligned to chip
        chip_ctr_ra, chip_ctr_dec = self._chip_cen()

        if compo_side == 'R':
            ia = -INJECTOR_THETA
        elif compo_side == 'L':
            ia = INJECTOR_THETA
        else:
            ia = PARK_POSITION

        # add COMPO components
        compo_arc = CompoPatrolArc(chip_ctr_ra, chip_ctr_dec, image,
                                   linewidth=10, color='black', linestyle='dash',
                                   name='COMPO_Arc')
        compo_free = CompoFreeRegion(chip_ctr_ra, chip_ctr_dec, image,
                                     fill=True, fillcolor='green', fillalpha=0.1,
                                     name='compo_free_region')

        compo_pickoff = PickoffArm().to_ginga_object(compo_angle*u.deg, chip_ctr_ra*u.deg, chip_ctr_dec*u.deg,
                                                     fill=True, fillcolor='yellow', fillalpha=0.3,
                                                     name='COMPO_pickoff')

        compo_injector = InjectionArm().to_ginga_object(ia, chip_ctr_ra*u.deg, chip_ctr_dec*u.deg,
                                                        color='yellow', fillalpha=0.3, fill=True,
                                                        name='COMPO_injector')

        obl = [compo_arc, compo_free, compo_pickoff, compo_injector]
        obj = CompoundObject(*obl)
        obj.editable = True
        return obj

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

        try:
            g = get_root(self).globals
            if g.ipars.compo():
                obj = self._make_compo(image)
                obj.showcap = True
                self.canvas.deleteObjectByTag('compo_overlay')
                self.canvas.add(obj, tag='compo_overlay', redraw=False)
                # rotate
                obj.rotate(pa, self.ctr_x, self.ctr_y)
            else:
                self.canvas.deleteObjectByTag('compo_overlay')
        except Exception as err:
            errmsg = "failed to draw COMPO: {}".format(str(err))
            self.logger.error(msg=errmsg)

        self.canvas.update_canvas()
