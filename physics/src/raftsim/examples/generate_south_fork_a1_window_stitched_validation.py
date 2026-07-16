"""Generate South Fork A1 full-reach stitched source-window validation report."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_window_stitched_validation import (
    build_south_fork_a1_window_stitched_validation_report,
    write_south_fork_a1_window_stitched_validation_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_south_fork_a1_window_stitched_validation_report(args.repo_root)
    payload = build_south_fork_a1_window_stitched_validation_report(args.repo_root)
    print(f"wrote={output_path}")
    print(f"status={payload['status']}")
    print(f"window_count={payload['summary']['window_count']}")
    print(f"seam_count={payload['summary']['seam_count']}")
    print(
        "can_generate_stitched_validation_derivatives="
        f"{payload['summary']['can_generate_stitched_validation_derivatives']}"
    )


if __name__ == "__main__":
    main()
