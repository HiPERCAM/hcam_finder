import pkg_resources
import numpy as np
from astropy import units as u

from ginga.util import wcs
from ginga.canvas.types.all import Polygon
from ginga.util.bezier import get_bezier


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


class CompoPatrolArc(Polygon):
    def __init__(self, ra_ctr_deg, dec_ctr_deg, image, **params):
        """
        Shape for drawing allowed control arc, made using Bezier curves

        Parameters
        ----------
        ra_ctr_deg, dec_ctr_deg : float
              Tel pointing center (deg)
        image : `~ginga.AstroImage`
              image to plot Window on
        """
        # assume patrol arc of 90 degrees
        theta = np.linspace(-80, 80, 40)*u.deg

        # the centre of COMPO's arc describes a circular arc of 48.551' around
        # a point which is 51.1743' below the rotator centre.
        # the radius of the COMPO pickoff mirror is 24"
        pickoff_size = 24*u.arcsec
        alpha = 5.1851*u.arcmin
        beta = 5.4628*u.arcmin
        r_inner = alpha - pickoff_size/2
        r_outer = alpha + pickoff_size/2
        dec_off = beta.to(u.deg).value

        # circular arc
        points_inner = r_inner*u.Quantity([np.sin(theta), np.cos(theta)])
        points_outer = r_outer*u.Quantity([np.sin(theta), np.cos(theta)])

        # transform to shape (N, 2) and units of degrees
        points_inner = points_inner.T.to(u.deg).value
        points_outer = points_outer.T.to(u.deg).value

        # add offsets to pointing center
        points_wcs = [
            wcs.add_offset_radec(ra_ctr_deg, dec_ctr_deg, p[0], p[1]-dec_off)
            for p in points_inner
        ]

        points_wcs.extend([
            wcs.add_offset_radec(ra_ctr_deg, dec_ctr_deg, p[0], p[1]-dec_off)
            for p in points_outer[::-1]
        ])

        self.points = [image.radectopix(ra, dec) for (ra, dec) in points_wcs]
        self.bezier = get_bezier(30, self.points)
        super(CompoPatrolArc, self).__init__(self.bezier, **params)
        self.name = params.pop('name', 'patrol_arc')


class CompoFreeRegion(Polygon):
    def __init__(self, ra_ctr_deg, dec_ctr_deg, image, **params):
        """
        Shape for drawing unvignetted area available to patrol arm

        Parameters
        ----------
        ra_ctr_deg, dec_ctr_deg : float
              Tel pointing center (deg)
        image : `~ginga.AstroImage`
              image to plot Window on
        """
        guider_file = pkg_resources.resource_filename('hcam_finder',
                                                      'data/guider_hole_arcseconds.txt')
        points = np.loadtxt(guider_file) / 36000
        points_wcs = [wcs.add_offset_radec(ra_ctr_deg, dec_ctr_deg, p[0], p[1]) for p in points]
        self.points = [image.radectopix(ra, dec) for (ra, dec) in points_wcs]
        self.bezier = get_bezier(30, self.points)
        super(CompoFreeRegion, self).__init__(self.bezier, **params)
        self.name = params.pop('name', 'compo_free_region')
