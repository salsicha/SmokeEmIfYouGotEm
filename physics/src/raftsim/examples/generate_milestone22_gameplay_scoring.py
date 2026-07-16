"""Generate the Milestone 22 gameplay telemetry and scoring manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone22 import write_gameplay_telemetry_scoring_manifest


def _default_repo_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "TODO.md").exists():
            return candidate
    return Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    args = parser.parse_args(argv)

    generated = write_gameplay_telemetry_scoring_manifest(args.repo_root)
    print(f"status={generated.manifest['status']}")
    print(f"schema={generated.manifest['schema']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
