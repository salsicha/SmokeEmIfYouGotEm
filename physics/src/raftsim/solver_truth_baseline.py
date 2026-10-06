"""Moved to the SEIYGE core submodule: seiyge_core.solver_truth_baseline (unreal/Plugins/SEIYGECore/python/src)."""
import sys as _sys

from raftsim._core import load as _load

_sys.modules[__name__] = _load("solver_truth_baseline")
