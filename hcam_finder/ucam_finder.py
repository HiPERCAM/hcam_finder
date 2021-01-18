# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division

from ginga.canvas.types.all import CompoundObject

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
                                 fill=True, color='blue',
                                 fillalpha=0.1, name='mainCCD')

        # list of objects for compound object
        obl = [mainCCD]

        # iterate over window pairs
        # these coords in ccd pixel vaues
        if not g.ipars.isFF:
            params = dict(fill=True, fillcolor='red', fillalpha=0.3)
            for xsl, xsr, ys, nx, ny in wframe:
                obl.append(self._make_win(xsl, ys, nx, ny, image, **params))
                obl.append(self._make_win(xsr, ys, nx, ny, image, **params))

        obj = CompoundObject(*obl)
        obj.editable = True
        return obj
