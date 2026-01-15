#!/usr/bin/env python
# setup.py
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import os
import re
import sys
from contextlib import closing
from setuptools import setup
__here__ = os.path.abspath(os.path.dirname(__file__))

NAME = 'cranix'
MODULES = []
PACKAGES = ['cranix']
DESCRIPTION = 'Config file reading, writing and validation.'
URL = 'https://github.com/Cranix-Solutions/cranix-python'

VERSION = ''
with closing(open(os.path.join(__here__, 'src', PACKAGES[0], '_version.py'), 'r')) as handle:
    for line in handle.readlines():
        if line.startswith('__version__'):
            VERSION = re.split('''['"]''', line)[1]
assert re.match(r"[0-9](\.[0-9]+)", VERSION), "No semantic version found in '._version'"

LONG_DESCRIPTION = """
**cranix** is a python API to the objects the CRANXI server

"""

CLASSIFIERS = [
    # Details at http://pypi.python.org/pypi?:action=list_classifiers
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 3',,
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13',
    'Operating System :: OS Independent',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

AUTHOR = 'Peter Varkoly'

AUTHOR_EMAIL = 'pvarkoly@cephalix.eu'

KEYWORDS = ['config', 'cranix']

project = dict(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    py_modules=MODULES,
    package_dir={'': 'src'},
    packages=PACKAGES,
    python_requires='>=3.7',
    classifiers=CLASSIFIERS,
    keywords=KEYWORDS,
    license='BSD-3-Clause',
)

if __name__ == '__main__':
    setup(**project)
