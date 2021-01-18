# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division

from ginga.canvas.types.all import CompoundObject

from hcam_widgets.tkutils import get_root

from .finders import FovSetter


class USPECFovSetter(FovSetter):

    def window_string(self):
        g = get_root(self).globals
        if g.ipars.isDrift():
            wframe = g.ipars.pframe
            winlist = [
                'xsl: {}, xsr: {}, ys: {}, nx: {}, ny: {}'.format(xsl, xsr, ys, nx, ny)
                for (xsl, xsr, ys, nx, ny) in wframe
            ]
        else:
            wframe = g.ipars.wframe
            winlist = [
                'xstart: {}, ystart: {}, nx: {}, ny: {}'.format(
                    xs, ys, nx, ny
                ) for (xs, ys, nx, ny) in wframe
            ]
        return '\n'.join(winlist)

    def _make_ccd(self, image):
        """
        Converts the current instrument settings to a ginga canvas object
        """
        # get window pair object from top widget
        g = get_root(self).globals
        wframe = g.ipars.pframe if g.ipars.isDrift() else g.ipars.wframe

        # all values in pixel coords of the FITS frame
        # get centre
        ctr_x, ctr_y = image.radectopix(self.ctr_ra_deg, self.ctr_dec_deg)
        self.ctr_x, self.ctr_y = ctr_x, ctr_y

        nx, ny = self.nxtot.value, self.nytot.value
        mainCCD = self._make_win(0, 0, nx, ny, image,
                                 fill=False, color='black', name='mainCCD')
        imagingArea = self._make_win(16, 2, nx-32, ny-46, image,
                                     fill=True, fillcolor='blue',
                                     fillalpha=0.3, name='ImageArea')

        # list of objects for compound object
        obl = [mainCCD, imagingArea]

        # iterate over window pairs
        # these coords in ccd pixel vaues
        params = dict(fill=True, fillcolor='red', fillalpha=0.3)
        if g.ipars.isDrift():
            for xsl, xsr, ys, nx, ny in wframe:
                obl.append(self._make_win(xsl, ys, nx, ny, image, **params))
                obl.append(self._make_win(xsr, ys, nx, ny, image, **params))
        else:
            for xs, ys, nx, ny in wframe:
                obl.append(self._make_win(xs, ys, nx, ny, image, **params))

        obj = CompoundObject(*obl)
        obj.editable = True
        return obj
