"""Generate named-rapid editor markers and simulator review-run definitions."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.named_rapid_registry import write_named_rapid_review_assets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    marker_path, geometry_path, run_path = write_named_rapid_review_assets(args.repo_root.resolve())
    print(marker_path)
    print(geometry_path)
    print(run_path)


if __name__ == "__main__":
    main()
