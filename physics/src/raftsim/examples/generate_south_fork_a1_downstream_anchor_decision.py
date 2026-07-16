"""Generate South Fork A1 downstream-anchor decision packet."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_downstream_anchor_decision import (
    build_south_fork_a1_downstream_anchor_decision_packet,
    write_south_fork_a1_downstream_anchor_decision_packet,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_paths = write_south_fork_a1_downstream_anchor_decision_packet(args.repo_root)
    packet = build_south_fork_a1_downstream_anchor_decision_packet(args.repo_root)
    print(f"written_count={len(output_paths)}")
    print(f"status={packet['status']}")
    print(f"option_count={len(packet['options'])}")
    print(f"station_delta_m={packet['candidate_window']['station_delta_m']}")


if __name__ == "__main__":
    main()
