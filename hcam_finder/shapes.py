import pkg_resources
import numpy as np
from astropy import units as u
from astropy.coordinates import CartesianRepresentation, SphericalRepresentation

from ginga import trcalc
from ginga.util import wcs
from ginga.canvas.types.all import Polygon, Path, CompoundObject, Circle, Box
from ginga.util.bezier import get_bezier

from hcam_widgets.compo import (PICKOFF_SIZE, MIRROR_SIZE, field_stop_centre,
                                SHADOW_X, SHADOW_Y, INJECTOR_THETA)


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


class CompoInjectorArm(CompoundObject):
    def __init__(self, corner, side, image, **params):
        """
        Shape for drawing injector mirror for COMPO
        """
        cx, cy = corner
        yoff = SHADOW_Y - SHADOW_X*np.tan(INJECTOR_THETA) + SHADOW_Y*np.tan(INJECTOR_THETA)**2
        if side == 'L':
            mul = -1
        else:
            mul = 1

        p1 = (cx, cy)
        p2 = wcs.add_offset_radec(cx, cy, -mul*SHADOW_X.to(u.deg).value, 0.0)
        p3 = wcs.add_offset_radec(p2[0], p2[1], mul*(SHADOW_Y*np.tan(INJECTOR_THETA)).to(u.deg).value,
                                  SHADOW_Y.to(u.deg).value)
        p4 = wcs.add_offset_radec(cx, cy, 0, yoff.to(u.deg).value)

        points_wcs = (p1, p2, p3, p4)
        vignetting = Polygon(points_wcs, coord='wcs', **params)

        circle_y = cy + PICKOFF_SIZE.to(u.deg).value/2
        circle_x = cx - mul * PICKOFF_SIZE.to(u.deg).value/2
        mirror = Circle(circle_x, circle_y, MIRROR_SIZE.to(u.deg).value/2, coord='wcs', **params)
        super(CompoInjectorArm, self).__init__(vignetting, mirror)

        self.name = params.pop('name', 'injector')


class CompoPickoffArm(CompoundObject):
    def __init__(self, ra_ctr_deg, dec_ctr_deg, compo_theta_deg, image, **params):
        """
        Shape for drawing pickoff mirror

        Parameters
        ----------
        ra_ctr_deg, dec_ctr_deg : float
            Tel pointing center (deg)
        compo_theta_deg : float
            Rotation angle of compo pickoff arm (deg)
        image : `~ginga.AstroImage`
            image to plot Window on
        """
        X, Y = field_stop_centre(compo_theta_deg*u.deg)
        compo_ra_cen, compo_dec_cen = wcs.add_offset_radec(
            ra_ctr_deg, dec_ctr_deg, X.to(u.deg).value, -Y.to(u.deg).value
        )
        self.theta = compo_theta_deg
        self.ra_cen = compo_ra_cen
        self.dec_cen = compo_dec_cen
        self.cen_x, self.cen_y = image.radectopix(self.ra_cen, self.dec_cen)

        baffle_x = (542 * 0.08086 * u.arcsec).to(u.deg).value
        baffle_y = (664 * 0.08086 * u.arcsec).to(u.deg).value
        points_wcs = (
            wcs.add_offset_radec(compo_ra_cen, compo_dec_cen, -baffle_x/2, -baffle_y/2),
            wcs.add_offset_radec(compo_ra_cen, compo_dec_cen, -baffle_x/2, baffle_y/2),
            wcs.add_offset_radec(compo_ra_cen, compo_dec_cen, baffle_x/2, baffle_y/2),
            wcs.add_offset_radec(compo_ra_cen, compo_dec_cen, baffle_x/2, -baffle_y/2)
        )
        points = [image.radectopix(ra, dec) for (ra, dec) in points_wcs]
        points = trcalc.rotate_coord(points, [self.theta], (self.cen_x, self.cen_y))
        baffle = Polygon(points, **params)

        # pixel coord for circle
        radius_pix = image.calc_radius_xy(self.cen_x, self.cen_y, MIRROR_SIZE.to(u.deg).value/2.)
        mirror = Circle(self.cen_x, self.cen_y, radius_pix, **params)

        super(CompoPickoffArm, self).__init__(baffle, mirror)
        self.name = params.pop('name', 'pickoff')


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
        theta = np.linspace(-80, 80, 40)*u.deg

        # circular arc, swapping dec sign
        X, Y = field_stop_centre(theta)
        points = u.Quantity([X, -Y])
        # transform to shape (N, 2) and units of degrees
        points = points.T.to(u.deg).value
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
