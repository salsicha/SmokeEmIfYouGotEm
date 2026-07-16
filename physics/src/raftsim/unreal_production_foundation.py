"""Synchronize authored Unreal production policy with project metadata."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


FOUNDATION_RELATIVE_PATH = Path(
    "unreal/Content/RaftSim/Production/production_foundation.json"
)
UPROJECT_RELATIVE_PATH = Path("unreal/SmokeEmIfYouGotEm.uproject")


def build_production_foundation(repo_root: Path) -> dict[str, Any]:
    """Return the authored foundation with project-derived fields normalized."""

    foundation_path = repo_root / FOUNDATION_RELATIVE_PATH
    project_path = repo_root / UPROJECT_RELATIVE_PATH
    foundation = json.loads(foundation_path.read_text(encoding="utf-8"))
    project = json.loads(project_path.read_text(encoding="utf-8"))

    normalized = copy.deepcopy(foundation)
    normalized["engine"]["engine_association"] = project["EngineAssociation"]
    normalized["enabled_project_plugins"] = [
        plugin["Name"]
        for plugin in project.get("Plugins", [])
        if plugin.get("Enabled", False)
    ]
    return normalized


def write_production_foundation(repo_root: Path) -> Path:
    """Normalize and rewrite the source-controlled foundation manifest."""

    output_path = repo_root / FOUNDATION_RELATIVE_PATH
    output_path.write_text(
        json.dumps(build_production_foundation(repo_root), indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
