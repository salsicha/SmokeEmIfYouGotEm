"""Generate the Milestone 20 accepted report-set lock."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone20 import write_report_set_lock


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
        default=Path("reports/milestone20/report_set_lock.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("reports/milestone20/report_set_lock.md"),
    )
    args = parser.parse_args(argv)

    lock = write_report_set_lock(
        repo_root=args.repo_root,
        output_json=args.output_json,
        output_md=args.output_md,
    )
    print(f"report={args.output_json}")
    print(f"markdown={args.output_md}")
    print(f"lock_hash={lock.report['lock']['lock_hash']}")
    print(f"passed={lock.report['passed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
