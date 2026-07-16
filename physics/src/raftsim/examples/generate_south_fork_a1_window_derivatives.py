"""Generate South Fork A1 full-reach source-window review derivatives."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_window_derivatives import (
    build_south_fork_a1_window_derivative_manifest,
    write_south_fork_a1_window_derivatives,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_south_fork_a1_window_derivatives(args.repo_root)
    payload = build_south_fork_a1_window_derivative_manifest(args.repo_root)
    print(f"wrote={output_path}")
    print(f"status={payload['status']}")
    print(f"window_count={payload['summary']['window_count']}")
    print(f"derived_png_count={payload['summary']['derived_png_count']}")
    print(f"edge_report_count={payload['summary']['edge_report_count']}")


if __name__ == "__main__":
    main()
