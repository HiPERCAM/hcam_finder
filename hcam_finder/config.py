# read in config
from __future__ import absolute_import, print_function, division
import configobj
import pkg_resources
import os
import validate


def check_user_dir(g, app_name='hfinder'):
    """
    Check directories exist for saving apps/configs etc. Create if not.
    """
    direc = os.path.expanduser('~/.' + app_name)
    if not os.path.exists(direc):
        try:
            os.mkdir(direc)
        except Exception as err:
            g.clog.warn('Failed to make directory ' + str(err))


def load_config(g, app_name='hfinder', env_var='HCAM_FINDER_CONF'):
    """
    Populate application level globals from config file
    """
    configspec_file = pkg_resources.resource_filename('hcam_finder',
                                                      'data/configspec.ini')
    # try and load config file.
    # look in the following locations in order
    # - HCAM_FINDER_CONF environment variable
    # - ~/.hfinder directory
    # - package resources
    paths = []
    if env_var in os.environ:
        paths.append(os.environ[env_var])
    paths.append(os.path.expanduser('~/.' + app_name))
    resource_dir = pkg_resources.resource_filename('hcam_finder', 'data')
    paths.append(resource_dir)

    # now load config file
    config = configobj.ConfigObj({}, configspec=configspec_file)
    for loc in paths:
        try:
            with open(os.path.join(loc, "config")) as source:
                config = configobj.ConfigObj(source, configspec=configspec_file)
            break
        except IOError:
            pass

    # validate ConfigObj, filling defaults from configspec if missing from config file
    validator = validate.Validator()
    result = config.validate(validator)
    if result is not True:
        g.clog.warn('Config file validation failed')

    # now update globals with config
    g.cpars.update(config)


def write_config(g, app_name='hfinder'):
    """
    Dump application level globals to config file
    """
    configspec_file = pkg_resources.resource_filename('hcam_finder',
                                                      'data/configspec.ini')
    config = configobj.ConfigObj({}, configspec=configspec_file)
    config.update(g.cpars)
    config.filename = os.path.expanduser('~/.{}/config'.format(app_name))
    if not os.path.exists(config.filename):
        try:
            config.write()
        except Exception as err:
            g.clog.warn("Could not write config file:\n" + str(err))
