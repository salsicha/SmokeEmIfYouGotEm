"""Generate the South Fork A1 full-reach corridor window manifest."""

from __future__ import annotations

from pathlib import Path

from raftsim.south_fork_a1_corridor_windows import (
    build_south_fork_a1_full_reach_corridor_window_manifest,
    write_south_fork_a1_full_reach_corridor_window_manifest,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_south_fork_a1_full_reach_corridor_window_manifest(repo_root)
    payload = build_south_fork_a1_full_reach_corridor_window_manifest(repo_root)
    summary = payload["coverage_summary"]
    print(f"status={payload['status']}")
    print(f"window_count={summary['window_count']}")
    print(f"named_rapid_count={summary['named_rapid_count']}")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
