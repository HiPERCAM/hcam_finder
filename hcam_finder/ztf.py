# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
import six

from ginga.misc import Bunch
from ginga.util import wcs
from astropy.io import ascii


if six.PY2:
    from urllib2 import Request, urlopen, URLError, HTTPError
else:
    # python3
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError


def geturl(ra, dec, width, height, filter_code):

    """Get URL for images in the table

    ra, dec = position in degrees
    width, height =  image size in decimal degrees
    filter_code = one of 'zg', 'zr', 'zi'
    format = data format (options are "jpg", "png" or "fits")
    Returns a string with the URL
    """
    base_url = 'https://irsa.ipac.caltech.edu/ibe/search/ztf/products/ref'
    # search for metadata
    fid = 1 + ['zg', 'zr', 'zi'].index(filter_code)
    url = base_url + "?POS={ra},{dec}&SIZE={width},{height}&INTERSECT=COVERS&ct=csv&WHERE=fid={fid}".format(
        **{
            'fid': fid, 'ra': ra, 'dec': dec, 'width': width, 'height': height
        }
    )
    req = Request(url)
    response = urlopen(req)
    data = response.read()
    t = ascii.read(data.decode())
    t.sort('maglimit')
    prefield = [f"{frame['field']:06d}"[0:3] for frame in t]
    t.add_column(prefield, name='prefield')
    frame = t[-1]
    url = (
        base_url.replace('search', 'data') +
        "/{prefield}/field{field:06d}/{filtercode}/ccd{ccdid:02d}/q{qid}/ztf_{field:06d}_{filtercode}_c{ccdid:02d}_q{qid}_refimg.fits".format(**frame)
    )
    # add cutout
    wd_arcsec = 3600*max(width, height)
    url += "?center={},{}&size={}arcsec&gzip=false".format(ra, dec, wd_arcsec)
    return url


class ZTFImageServer(object):

    def __init__(self, logger, full_name, short_name, survey, description):
        self.logger = logger
        self.full_name = full_name
        self.short_name = short_name
        self.kind = 'astroquery-image'
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
        self.logger.info("Querying catalog: %s" % (self.full_name))

        try:
            url = geturl(ra_deg, dec_deg, wd_deg, ht_deg, self.survey)
            self.logger.info("Found image")
        except Exception:
            self.logger.warning("Found no images in this area")
            return None

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
