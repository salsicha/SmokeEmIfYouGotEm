"""Generate Unreal live-water manifests from the current Milestone 20 lock."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..live_water_bridge_manifest import write_live_water_bridge_manifests


def _default_repo_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "TODO.md").exists():
            return candidate
    return Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    args = parser.parse_args(argv)

    generated = write_live_water_bridge_manifests(args.repo_root)
    print(f"live_bridge_status={generated.live_bridge['status']}")
    print(f"runtime_candidate_status={generated.runtime_candidate['status']}")
    print(
        "live_stepping_enabled="
        f"{generated.live_bridge['water_runtime']['live_stepping_enabled']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
