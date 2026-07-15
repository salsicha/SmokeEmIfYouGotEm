"""Generate the review-only Batoka Sentinel centerline candidate."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.zambezi_sentinel_centerline import build_zambezi_sentinel_centerline_candidate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    manifest = build_zambezi_sentinel_centerline_candidate(args.repo_root)
    measurements = manifest["measurements"]
    print(
        "Zambezi Sentinel candidate: "
        f"{measurements['candidate_simplified_length_m']:.1f} m, "
        f"p95 shift {measurements['p95_absolute_lateral_shift_m']:.1f} m"
    )


if __name__ == "__main__":
    main()

