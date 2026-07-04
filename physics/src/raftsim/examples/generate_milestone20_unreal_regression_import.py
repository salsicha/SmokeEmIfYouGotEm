"""Generate the Milestone 20 Unreal water regression fixture import manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone20 import write_unreal_regression_fixture_import


def _default_repo_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "TODO.md").exists():
            return candidate
    return Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    parser.add_argument(
        "--output-json",
        type=Path,
        default=_default_repo_root()
        / "unreal/Content/RaftSim/Automation/water_regression_fixture_import.json",
    )
    args = parser.parse_args(argv)

    generated = write_unreal_regression_fixture_import(
        repo_root=args.repo_root,
        output_json=args.output_json,
    )
    print(f"manifest={args.output_json}")
    print(f"fixtures={generated.manifest['total_fixture_count']}")
    print(f"status={generated.manifest['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
