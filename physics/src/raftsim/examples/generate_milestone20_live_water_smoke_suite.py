"""Generate the Milestone 20 live-water Unreal smoke suite gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone20 import write_live_water_unreal_smoke_suite


def _default_repo_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "TODO.md").exists():
            return candidate
    return Path.cwd()


def main(argv: list[str] | None = None) -> int:
    repo_root = _default_repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument(
        "--suite-json",
        type=Path,
        default=repo_root / "unreal/Content/RaftSim/Automation/live_water_smoke_suite.json",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=repo_root / "physics/reports/milestone20/live_water_unreal_smoke_suite.json",
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=repo_root / "physics/reports/milestone20/live_water_unreal_smoke_suite.md",
    )
    args = parser.parse_args(argv)

    generated = write_live_water_unreal_smoke_suite(
        repo_root=args.repo_root,
        suite_json=args.suite_json,
        report_json=args.report_json,
        report_md=args.report_md,
    )
    print(f"suite={args.suite_json}")
    print(f"report={args.report_json}")
    print(f"passed={generated.report['passed']}")
    print(f"decision={generated.report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
