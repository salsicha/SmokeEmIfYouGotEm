"""Generate a deterministic solver-neutral 2.5D scenario package."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..plotting import plot_scenario2_5d_field
from ..scenario2_5d import (
    FixtureScenario2_5DParameters,
    ProceduralScenario2_5DParameters,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
)

FIXTURE_CHOICES = (
    "flat_pool",
    "uniform_channel",
    "dam_break",
    "bed_step",
    "constriction",
    "wet_dry_shoreline",
    "sloping_manning_channel",
    "drop_ledge",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("fixture", "procedural"), default="fixture")
    parser.add_argument("--fixture", choices=FIXTURE_CHOICES, default="uniform_channel")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/scenarios2_5d"))
    parser.add_argument("--nx", type=int, default=64)
    parser.add_argument("--ny", type=int, default=32)
    parser.add_argument("--dx", type=float, default=1.0)
    parser.add_argument("--dy", type=float, default=1.0)
    parser.add_argument("--duration", type=float, default=6.0)
    parser.add_argument("--fixed-dt", type=float, default=1.0 / 60.0)
    parser.add_argument("--difficulty", type=float, default=0.45)
    parser.add_argument("--feature-count", type=int, default=None)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args(argv)

    if args.mode == "fixture":
        scenario = generate_fixture_scenario2_5d(
            FixtureScenario2_5DParameters(
                fixture=args.fixture,
                seed=args.seed,
                nx=args.nx,
                ny=args.ny,
                dx=args.dx,
                dy=args.dy,
                duration=args.duration,
                fixed_dt=args.fixed_dt,
            )
        )
    else:
        scenario = generate_procedural_scenario2_5d(
            ProceduralScenario2_5DParameters(
                seed=args.seed,
                nx=args.nx,
                ny=args.ny,
                dx=args.dx,
                dy=args.dy,
                duration=args.duration,
                fixed_dt=args.fixed_dt,
                difficulty=args.difficulty,
                feature_count=args.feature_count,
            )
        )

    output_dir = args.output_dir / scenario.metadata.scenario_id
    scenario.write_package(output_dir)
    validation = scenario.validate()
    (output_dir / "validation.txt").write_text("\n".join(validation.summary_lines()) + "\n", encoding="utf-8")

    if not args.no_plots:
        plot_scenario2_5d_field(scenario, field="bed", output_path=output_dir / "bed.png")
        plot_scenario2_5d_field(scenario, field="depth", output_path=output_dir / "depth.png")
        plot_scenario2_5d_field(scenario, field="speed", output_path=output_dir / "speed.png")

    print(f"scenario={output_dir / 'scenario.json'}")
    print(f"bed={output_dir / 'bed.npy'}")
    print(f"initial_state={output_dir / 'initial_state.npz'}")
    print(f"features={output_dir / 'features.json'}")
    print(f"probes={output_dir / 'probes.json'}")
    for line in validation.summary_lines():
        print(line)
    return 0 if validation.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
