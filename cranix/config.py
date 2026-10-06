# -*- coding: utf-8 -*-

# Copyright (c) 2026 Peter Varkoly <pvarkoly@cephalix.eu> All rights reserved.

"""
Configuration discovery for the CRANIX API client.
"""

import os

from bashconfigparser import BashConfigParser

DEFAULT_API_URL = "http://localhost:9080/api"
DEFAULT_PROPERTIES_FILE = "/opt/cranix-java/conf/cranix-api.properties"
TOKEN_KEY = "de.cranix.api.auth.localhost"


def get_base_url():
    """Return the base URL of the CRANIX API.

    The URL can be overridden with the ``CRANIX_API_URL`` environment variable.
    """
    return os.environ.get("CRANIX_API_URL", DEFAULT_API_URL).rstrip("/")


def get_properties_file():
    """Return the path of the CRANIX API properties file.

    The path can be overridden with the ``CRANIX_API_PROPERTIES`` environment
    variable.
    """
    return os.environ.get("CRANIX_API_PROPERTIES", DEFAULT_PROPERTIES_FILE)


def read_properties(path=None):
    """Read the CRANIX API properties file and return a BashConfigParser."""
    return BashConfigParser(config_file=path or get_properties_file())


def read_token(path=None):
    """Read the localhost API token from the CRANIX API properties file."""
    parser = read_properties(path)
    return parser.get(TOKEN_KEY, "") or ""