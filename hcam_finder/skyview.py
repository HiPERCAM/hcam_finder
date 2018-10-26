# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
import six

from astroquery.skyview import SkyView
from ginga.misc import Bunch
from ginga.util import wcs
from astropy import coordinates as coord
from astropy import units as u

if six.PY2:
    from urllib2 import Request, urlopen, URLError, HTTPError
else:
    # python3
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError


class SkyviewImageServer(object):

    def __init__(self, logger, full_name, short_name, survey, description):
        self.logger = logger
        self.full_name = full_name
        self.short_name = short_name
        self.kind = 'astroquery-image'
        self.querymod = SkyView
        self.survey = survey

        # For compatibility with other Ginga catalog servers
        self.params = {}
        count = 0
        for label, key in (('RA', 'ra'), ('DEC', 'dec'),
                           ('Width', 'width'), ('Height', 'height')):
            self.params[key] = Bunch.Bunch(name=key, convert=str,
                                           label=label, order=count)
            count += 1

    def getParams(self):
        return self.params

    def search(self, dstpath, **params):
        """For compatibility with generic image catalog search."""

        self.logger.debug("search params=%s" % (str(params)))
        ra, dec = params['ra'], params['dec']
        if not (':' in ra):
            # Assume RA and DEC are in degrees
            ra_deg = float(ra)
            dec_deg = float(dec)
        else:
            # Assume RA and DEC are in standard string notation
            ra_deg = wcs.hmsStrToDeg(ra)
            dec_deg = wcs.dmsStrToDeg(dec)

        # Convert to degrees for search
        wd_deg = float(params['width']) / 60.0
        ht_deg = float(params['height']) / 60.0

        # Note requires astropy 3.x+
        c = coord.SkyCoord(ra_deg * u.degree,
                           dec_deg * u.degree,
                           frame='icrs')

        self.logger.info("Querying catalog: %s" % (self.full_name))
        results = self.querymod.get_image_list(c, self.survey,
                                               width=wd_deg * u.degree,
                                               height=ht_deg * u.degree,
                                               pixels=(1200, 1200),
                                               deedger="_skip_")

        if len(results) > 0:
            self.logger.info("Found %d images" % len(results))
        else:
            self.logger.warning("Found no images in this area" % len(results))
            return None

        # For now, we pick the first one found
        url = results[0]
        # fitspath = results[0].make_dataset_filename(dir="/tmp")

        # download file
        self.fetch(url, filepath=dstpath)

        # explicit return
        return dstpath

    def fetch(self, url, filepath=None):
        data = ""

        req = Request(url)

        try:
            self.logger.info("Opening url=%s" % (url))
            try:
                response = urlopen(req)

            except HTTPError as e:
                self.logger.error("Server returned error code %s" % (e.code))
                raise e
            except URLError as e:
                self.logger.error("Server URL failure: %s" % (str(e.reason)))
                raise e
            except Exception as e:
                self.logger.error("URL fetch failure: %s" % (str(e)))
                raise e

            self.logger.debug("getting HTTP headers")
            info = response.info()
            self.logger.debug(info)
            self.logger.debug("getting data")
            data = response.read()
            self.logger.debug("fetched %d bytes" % (len(data)))
            # data = data.decode('ascii')

        except Exception as e:
            self.logger.error("Error reading data from '%s': %s" % (
                url, str(e)))
            raise e

        if filepath:
            with open(filepath, 'wb') as out_f:
                out_f.write(data)
            return None

        else:
            return data
