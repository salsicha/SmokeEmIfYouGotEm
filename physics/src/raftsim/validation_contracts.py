"""Moved to the SEIYGE core submodule: seiyge_core.validation_contracts (unreal/Plugins/SEIYGECore/python/src)."""
import sys as _sys

from raftsim._core import load as _load

_sys.modules[__name__] = _load("validation_contracts")
