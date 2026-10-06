# -*- coding: utf-8 -*-

# Copyright (c) 2026 Peter Varkoly <pvarkoly@cephalix.eu> All rights reserved.

"""
Common Python modules for CRANIX.

The package provides a native REST client for the CRANIX API, the shared
helper functions used by the CRANIX packages, the user import logic and the
Microsoft 365 synchronization helpers.
"""

from ._version import __version__

from . import api
from . import config
from . import functions
from . import vars

from .api import CrxApi
from .api import CrxApiError
from .api import CrxResponse

from .functions import check_password
from .functions import check_uid
from .functions import create_secure_pw
from .functions import print_error
from .functions import print_msg
from .functions import read_birthday

from .vars import attr_ext_name
from .vars import user_attributes

__all__ = [
    "__version__",
    "api",
    "config",
    "functions",
    "vars",
    "CrxApi",
    "CrxApiError",
    "CrxResponse",
    "attr_ext_name",
    "user_attributes",
    "check_password",
    "check_uid",
    "create_secure_pw",
    "print_error",
    "print_msg",
    "read_birthday",
]