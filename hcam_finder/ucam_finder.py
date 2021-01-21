# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
import itertools

from ginga.canvas.types.all import Line, CompoundObject
from ginga.util import wcs

from hcam_widgets.tkutils import get_root

from .finders import FovSetter


class UCAMFovSetter(FovSetter):

    def window_string(self):
        g = get_root(self).globals
        if g.ipars.isFF:
            retval = ''
        else:
            wframe = g.ipars.wframe
            winlist = [
                'xsl: {}, xsr: {}, ys: {}, nx: {}, ny: {}'.format(xsl, xsr, ys, nx, ny)
                for (xsl, xsr, ys, nx, ny) in wframe
            ]
            retval = '\n'.join(winlist)
        return retval

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
                                 fill=True, color='red',
                                 fillalpha=0.1, name='mainCCD')

        # dashed lines to mark quadrants of CCD
        chip_ctr_ra, chip_ctr_dec = self._chip_cen()
        x1, y1 = wcs.add_offset_radec(chip_ctr_ra, chip_ctr_dec,
                                      0, self.fov_y/2)
        x2, y2 = wcs.add_offset_radec(chip_ctr_ra, chip_ctr_dec,
                                      0, -self.fov_y/2)
        points = [image.radectopix(ra, dec) for (ra, dec) in (
            (x1, y1), (x2, y2)
        )]
        points = list(itertools.chain.from_iterable(points))
        vline = Line(*points, color='red', linestyle='dash', linewidth=2)

        # emphasis on bottom of CCD
        x1, y1 = wcs.add_offset_radec(chip_ctr_ra, chip_ctr_dec,
                                      -self.fov_x/2, -self.fov_y/2)
        x2, y2 = wcs.add_offset_radec(chip_ctr_ra, chip_ctr_dec,
                                      self.fov_x/2, -self.fov_y/2)
        points = [image.radectopix(ra, dec) for (ra, dec) in (
            (x1, y1), (x2, y2)
        )]
        points = list(itertools.chain.from_iterable(points))
        eline = Line(*points, color='red', linewidth=4)

        # list of objects for compound object
        obl = [mainCCD, vline, eline]

        # iterate over window pairs
        # these coords in ccd pixel vaues
        if not g.ipars.isFF:
            params = dict(fill=True, fillcolor='blue', fillalpha=0.3)
            for xsl, xsr, ys, nx, ny in wframe:
                obl.append(self._make_win(xsl, ys, nx, ny, image, **params))
                obl.append(self._make_win(xsr, ys, nx, ny, image, **params))

        obj = CompoundObject(*obl)
        obj.editable = True
        return obj
