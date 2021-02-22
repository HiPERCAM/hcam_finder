# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
import six

from ginga.misc import Bunch
from ginga.util import wcs
import numpy as np
from astropy.table import Table


if six.PY2:
    from urllib2 import Request, urlopen, URLError, HTTPError
else:
    # python3
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError


def getimages(ra, dec, size=240, filters="grizy"):

    """Query ps1filenames.py service to get a list of images

    ra, dec = position in degrees
    size = image size in pixels (0.25 arcsec/pixel)
    filters = string with filters to include
    Returns a table with the results
    """

    service = "https://ps1images.stsci.edu/cgi-bin/ps1filenames.py"
    url = ("{service}?ra={ra}&dec={dec}&size={size}&format=fits"
           "&filters={filters}").format(**locals())
    table = Table.read(url, format='ascii')
    return table


def geturl(ra, dec, size=240, output_size=None, filters="grizy", format="fits", color=False):

    """Get URL for images in the table

    ra, dec = position in degrees
    size = extracted image size in pixels (0.25 arcsec/pixel)
    output_size = output (display) image size in pixels (default = size).
                  output_size has no effect for fits format images.
    filters = string with filters to include
    format = data format (options are "jpg", "png" or "fits")
    color = if True, creates a color image (only for jpg or png format).
            Default is return a list of URLs for single-filter grayscale images.
    Returns a string with the URL
    """

    if color and format == "fits":
        raise ValueError("color images are available only for jpg or png formats")
    if format not in ("jpg", "png", "fits"):
        raise ValueError("format must be one of jpg, png, fits")
    table = getimages(ra, dec, size=size, filters=filters)
    url = ("https://ps1images.stsci.edu/cgi-bin/fitscut.cgi?"
           "ra={ra}&dec={dec}&size={size}&format={format}").format(**locals())
    if output_size:
        url = url + "&output_size={}".format(output_size)
    # sort filters from red to blue
    flist = ["yzirg".find(x) for x in table['filter']]
    table = table[np.argsort(flist)]
    urlbase = url + "&red="
    urls = []
    for filename in table['filename']:
        urls.append(urlbase+filename)
    return urls


class PS1ImageServer(object):

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

        # Convert to pixels for search
        wd_px = float(params['width']) * 60.0 / 0.25
        ht_px = float(params['height']) * 60.0 / 0.25
        sz = int(max(wd_px, ht_px))

        self.logger.info("Querying catalog: %s" % (self.full_name))

        results = geturl(ra_deg, dec_deg, size=sz, filters=self.survey)
        if len(results) > 0:
            self.logger.info("Found %d images" % len(results))
        else:
            self.logger.warning("Found no images in this area" % len(results))
            return None

        # For now, we pick the first one found
        url = results[0]

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
