"""Run a scripted top-down raft through a generated 2D rapid."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..plotting import plot_force_magnitudes, plot_river2d, plot_trajectory2d
from ..raft2d import Raft2DBackendName, Raft2DSimulation, default_forward_paddle_commands
from ..river2d import River2DParameters, generate_river_2d
from ..sim import SimulationConfig


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--duration", type=float, default=35.0)
    parser.add_argument("--backend", choices=("auto", "python", "chrono"), default="auto")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/rapid2d"))
    args = parser.parse_args(argv)

    output_dir = args.output_dir / f"seed_{args.seed}_{args.backend}"
    river = generate_river_2d(River2DParameters(seed=args.seed))
    sim = Raft2DSimulation(
        river,
        backend=args.backend,  # type: ignore[arg-type]
        sim_config=SimulationConfig(fixed_dt=1.0 / 60.0, seed=args.seed),
    )

    results = sim.run(args.duration, default_forward_paddle_commands())
    positions = [result.state.position for result in results]
    output_dir.mkdir(parents=True, exist_ok=True)
    river.write_json(output_dir / "river.json")
    sim.telemetry.write_force_csv(output_dir / "telemetry.csv")
    plot_river2d(river, output_path=output_dir / "river.png")
    plot_trajectory2d(positions, river=river, output_path=output_dir / "trajectory.png")
    plot_force_magnitudes(sim.telemetry.frames, output_path=output_dir / "forces.png")

    print(f"backend={sim.backend_name}")
    print(f"outcome={sim.outcome}")
    print(f"steps={len(results)}")
    print(f"telemetry={output_dir / 'telemetry.csv'}")
    print(f"trajectory={output_dir / 'trajectory.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
