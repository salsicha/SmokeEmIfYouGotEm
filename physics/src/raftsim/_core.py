"""Locate the SEIYGE core water package (git submodule at <repo>/core)."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

CORE_PYTHON = Path(__file__).resolve().parents[3] / "unreal" / "Plugins" / "SEIYGECore" / "python"


def load(name: str) -> ModuleType:
    """Import seiyge_core.<name>, adding the submodule's src and scripts to sys.path if needed."""
    try:
        import seiyge_core  # noqa: F401
    except ImportError:
        if not (CORE_PYTHON / "src" / "seiyge_core").is_dir():
            raise ImportError(
                "The SEIYGE core submodule is not checked out at core/. "
                "Run: git submodule update --init core"
            ) from None
        sys.path.append(str(CORE_PYTHON / "src"))
    scripts = str(CORE_PYTHON / "scripts")
    if scripts not in sys.path:
        sys.path.append(scripts)
    return importlib.import_module("seiyge_core." + name)
