import pkg_resources
import numpy as np
from astropy import units as u

from ginga.util import wcs
from ginga.canvas.types.all import Polygon, Path
from ginga.util.bezier import get_bezier

from hcam_widgets.compo.utils import field_stop_centre, gtc_focalplane_equivalencies


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


class CompoPatrolArc(Path):
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
        theta = np.linspace(-65, 65, 40)*u.deg

        # circular arc, swapping dec sign
        X, Y = field_stop_centre(theta)
        points = u.Quantity([X, -Y])
        # transform to shape (N, 2) and units of degrees
        with u.set_enabled_equivalencies(gtc_focalplane_equivalencies):
            points = points.T.to_value(u.deg)
        # add offsets to pointing center
        points_wcs = [
            wcs.add_offset_radec(ra_ctr_deg, dec_ctr_deg, p[0], p[1])
            for p in points
        ]

        self.points = [image.radectopix(ra, dec) for (ra, dec) in points_wcs]
        self.bezier = get_bezier(30, self.points)
        super(CompoPatrolArc, self).__init__(self.points, **params)
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
