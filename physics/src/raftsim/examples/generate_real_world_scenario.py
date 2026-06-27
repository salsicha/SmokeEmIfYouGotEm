"""Generate the Milestone 9 real-world river seed package."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..real_world import (
    PlayerSelection,
    default_player_selections,
    generate_real_world_scenario2_5d,
    south_fork_american_flow_bands,
    south_fork_american_section,
    write_real_world_seed_package,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/real_world"))
    parser.add_argument("--flow-band", choices=tuple(band.flow_band for band in south_fork_american_flow_bands()), default="median_runnable")
    parser.add_argument("--difficulty", choices=("beginner", "intermediate", "advanced", "expert"), default="intermediate")
    parser.add_argument("--duration", type=float, default=8.0)
    parser.add_argument("--nx", type=int, default=72)
    parser.add_argument("--ny", type=int, default=32)
    parser.add_argument("--write-full-package", action="store_true", help="Also write source catalog, source manifest, labels, and corridor metadata.")
    args = parser.parse_args(argv)

    section = south_fork_american_section()
    if args.write_full_package:
        data_dir = write_real_world_seed_package(args.output_dir)
        print(f"data_package={data_dir}")

    default_selection = next(selection for selection in default_player_selections() if selection.flow_band == args.flow_band)
    selection = PlayerSelection(
        region=default_selection.region,
        river_id=section.river_id,
        section_id=section.section_id,
        season=default_selection.season,
        flow_band=args.flow_band,
        difficulty=args.difficulty,
        raft_setup=default_selection.raft_setup,
    )
    scenario = generate_real_world_scenario2_5d(
        selection,
        nx=args.nx,
        ny=args.ny,
        duration=args.duration,
    )
    scenario_dir = scenario.write_package(args.output_dir / "scenario" / scenario.metadata.scenario_id)
    print(f"scenario={scenario_dir / 'scenario.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
