"""Generate South Fork A1 full-reach window source-pull requests."""

from __future__ import annotations

from pathlib import Path

from raftsim.south_fork_a1_window_source_pulls import (
    build_south_fork_a1_window_source_pull_plan,
    write_south_fork_a1_window_source_pull_plan,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_south_fork_a1_window_source_pull_plan(repo_root)
    payload = build_south_fork_a1_window_source_pull_plan(repo_root)
    summary = payload["coverage_summary"]
    print(f"status={payload['status']}")
    print(f"window_count={summary['window_count']}")
    print(f"planned_request_count={summary['planned_request_count']}")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
