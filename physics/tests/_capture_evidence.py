"""Shared helper for capture-evidence assertions after the July 17, 2026 trim.

Superseded-version capture binaries under the pruned roots are removed from
the working tree (their review JSONs keep path + hash as the evidence record,
and the pre-rewrite archive keeps the binaries). Evidence anywhere else must
still exist on disk.
"""

from __future__ import annotations

from pathlib import Path

PRUNED_ROOTS = (
    "docs/environment-captures/photoreal_river_previews/landscape_candidates",
    "unreal/Content/RaftSim/Maps/EnvironmentPreviews",
)


def _is_prunable(path: Path) -> bool:
    text = str(path)
    return any(root in text for root in PRUNED_ROOTS)


def assert_capture_recorded(path: Path) -> None:
    if _is_prunable(path):
        if path.exists():
            assert path.stat().st_size > 0
    else:
        assert path.is_file()
        assert path.stat().st_size > 0
