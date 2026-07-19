"""Generate and solve the complete South Fork named-rapid hydraulic matrix."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_full_hydraulics import (
    build_south_fork_full_hydraulics_manifest,
    write_south_fork_full_hydraulics,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--solver", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()

    output = write_south_fork_full_hydraulics(
        args.repo_root, args.solver, args.work_dir
    )
    manifest = build_south_fork_full_hydraulics_manifest(args.repo_root)
    print(f"wrote={output}")
    print(f"status={manifest['status']}")
    print(f"rapid_count={manifest['matrix']['rapid_count']}")
    print(f"combination_count={manifest['matrix']['combination_count']}")
    print(f"passed={manifest['matrix']['passed_combination_count']}")


if __name__ == "__main__":
    main()
