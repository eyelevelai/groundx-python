from .client import AsyncGroundx, Groundx

from .legacy import Groundx as LegacyGroundx

AsyncGroundX = AsyncGroundx
GroundX = Groundx

import warnings


class DeprecatedGroundxWrapper(LegacyGroundx):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "\n\n\tThis version of the SDK and its methods are deprecated and will be removed in a future release.\n\n"
            "\tPlease switch to the new SDK and its methods.\n\n"
            "\tSee https://documentation.groundx.ai for more information.\n",
            DeprecationWarning,
            stacklevel=2,
        )
        self._legacy_client = LegacyGroundx(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._legacy_client, name)


Groundx = DeprecatedGroundxWrapper

import sys
import inspect
from . import legacy
from . import __name__ as package_name

groundx_module = sys.modules[package_name]
for name, obj in inspect.getmembers(legacy):
    if inspect.isclass(obj):
        setattr(groundx_module, name, obj)

groundx_module.Groundx = Groundx
