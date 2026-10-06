"""Moved to the SEIYGE core submodule: seiyge_core.examples.run_analytic_fixture_validation."""
import runpy as _runpy
import sys as _sys

from raftsim._core import load as _load

if __name__ == "__main__":
    _load("examples")
    _runpy.run_module("seiyge_core.examples.run_analytic_fixture_validation", run_name="__main__", alter_sys=True)
else:
    _sys.modules[__name__] = _load("examples.run_analytic_fixture_validation")
