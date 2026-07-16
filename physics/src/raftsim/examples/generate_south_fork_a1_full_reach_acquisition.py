"""Generate the South Fork A1 full-reach acquisition plan."""

from __future__ import annotations

from pathlib import Path

from raftsim.south_fork_a1_full_reach_acquisition import (
    build_south_fork_a1_full_reach_acquisition_plan,
    write_south_fork_a1_full_reach_acquisition_plan,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_south_fork_a1_full_reach_acquisition_plan(repo_root)
    payload = build_south_fork_a1_full_reach_acquisition_plan(repo_root)
    print(f"status={payload['status']}")
    print(f"source_pull_count={len(payload['source_pull_queue'])}")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
