"""Shim file for backward compatibility. Forward all attribute access to _engine dynamically."""

import sys
import types
from typing import Any

from . import _engine


class ShimModule(types.ModuleType):
    """Module shim that forwards all attribute operations (get, set, del) to _engine."""

    def __getattr__(self, name: str) -> Any:
        return getattr(_engine, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(_engine, name, value)

    def __delattr__(self, name: str) -> None:
        delattr(_engine, name)


# Retrieve current module globals to initialize the ModuleType object properly
current_module = sys.modules[__name__]
shim = ShimModule(__name__, doc=current_module.__doc__)
sys.modules[__name__] = shim
