"""Finalize South Fork HLOD evidence from an Unreal commandlet build log."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..south_fork_hlod_evidence import finalize_south_fork_hlod_manifest


def _default_repo_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "TODO.md").exists():
            return candidate
    return Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    parser.add_argument("--commandlet-log", type=Path, required=True)
    args = parser.parse_args(argv)

    evidence = finalize_south_fork_hlod_manifest(args.repo_root, args.commandlet_log)
    result = evidence["commandlet_result"]
    print(f"hlod_actor_count={result['world_actor_count']}")
    print(f"built_actor_count={result['built_actor_count']}")
    print("hlod_generation_complete=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
