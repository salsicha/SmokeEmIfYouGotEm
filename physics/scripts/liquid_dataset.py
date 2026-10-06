"""Moved to the SEIYGE core submodule: unreal/Plugins/SEIYGECore/python/scripts/liquid_dataset.py."""
import importlib.util as _util
import sys as _sys
from pathlib import Path as _Path

_core_scripts = _Path(__file__).resolve().parents[2] / "unreal" / "Plugins" / "SEIYGECore" / "python" / "scripts"
if str(_core_scripts) not in _sys.path:
    _sys.path.append(str(_core_scripts))
_spec = _util.spec_from_file_location(__name__, _core_scripts / "liquid_dataset.py")
_module = _util.module_from_spec(_spec)
_sys.modules[__name__] = _module
_spec.loader.exec_module(_module)
