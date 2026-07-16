"""Generate the South Fork A1 full-reach flow-window review."""

from __future__ import annotations

from pathlib import Path

from raftsim.south_fork_a1_flow_window_review import (
    build_south_fork_a1_full_reach_flow_window_review,
    write_south_fork_a1_full_reach_flow_window_review,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_south_fork_a1_full_reach_flow_window_review(repo_root)
    payload = build_south_fork_a1_full_reach_flow_window_review(repo_root)
    multiyear = payload["evidence_windows"]["multiyear_context"]["summary"]
    print(f"status={payload['status']}")
    print(f"flow_band_count={len(payload['reviewed_flow_bands'])}")
    print(f"multiyear_days_peak_ge_3000_cfs={multiyear['days_peak_ge_3000_cfs']}")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
