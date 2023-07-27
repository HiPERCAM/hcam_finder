#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import glob
import os

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = ["ginga", "astropy", "six", "pillow", "configobj", "hcam_widgets>=1.1.1"]

test_requirements = [
    # TODO: put package test requirements here
]

# Treat everything in scripts except README.rst as a script to be installed
scripts = [
    fname
    for fname in glob.glob(os.path.join("scripts", "*"))
    if os.path.basename(fname) != "README.rst"
]

setup(
    name="hcam_finder",
    version="1.3.3",
    description="Observation planning and finding charts for HiPerCAM",
    long_description=readme + "\n\n" + history,
    author="Stuart Littlefair",
    author_email="s.littlefair@shef.ac.uk",
    url="https://github.com/HiPERCAM/hcam_finder",
    download_url="https://github.com/HiPERCAM/hcam_finder/archive/v1.3.3.tar.gz",
    packages=[
        "hcam_finder",
    ],
    package_dir={"hcam_finder": "hcam_finder"},
    include_package_data=True,
    scripts=scripts,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords="hcam_finder",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
    test_suite="tests",
    tests_require=test_requirements,
)
