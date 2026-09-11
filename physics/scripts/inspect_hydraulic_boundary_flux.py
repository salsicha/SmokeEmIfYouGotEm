"""Inspect a saved state through the actual C++ MUSCL boundary flux path.

This runs no time steps and never edits the input scenario or saved frame.
The optional frame is validated against the exact scenario bed/grid before use.
Target-discharge metadata is reported separately from measured numerical flux.
"""
from pathlib import Path
import argparse
import json
import subprocess

import numpy as np

from audit_troublemaker_hydraulic_spinup import warm_start
from raftsim.scenario2_5d import read_scenario2_5d_package


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', type=Path, required=True)
    parser.add_argument('--solver', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frame', type=Path)
    parser.add_argument('--elapsed', type=float, default=0.)
    parser.add_argument('--prescribed-discharge', type=float)
    args = parser.parse_args()
    if not np.isfinite(args.elapsed) or args.elapsed < 0 or (args.elapsed and not args.frame):
        parser.error('--elapsed must be nonnegative and requires --frame')
    # Refuse reuse so one audit cannot overwrite another's evidence.
    args.output.mkdir(parents=True, exist_ok=False)
    scenario = read_scenario2_5d_package(args.scenario)
    if args.frame:
        scenario = warm_start(scenario, args.frame, args.elapsed)
    package = args.output / 'scenario'
    scenario.write_package(package)
    command = [str(args.solver.resolve()), '--scenario', str(package.resolve()),
               '--solver-mode', 'finite_volume', '--spatial-order', '2',
               '--boundary-mode', 'scenario', '--flux-scheme', 'hll',
               '--bed-slope-source-scale', '1', '--disable-fixture-calibrations',
               '--no-preserve-initial-mass', '--inspect-boundary-flux']
    if args.prescribed_discharge is not None:
        command.extend(['--experimental-west-discharge', str(args.prescribed_discharge)])
    run = subprocess.run(command, text=True, capture_output=True, check=True)
    flux = json.loads(run.stdout)
    west = next(b for b in scenario.boundaries if b.edge == 'west')
    if west.stage is None or west.velocity is None or west.depth is not None:
        raise ValueError('this report expects the stage-plus-velocity west boundary used by Troublemaker')
    boundary_depth = np.maximum(west.stage - scenario.bed[:, 0], 0.)
    boundary_depth = np.where(boundary_depth > 1e-6, boundary_depth, 0.)
    state = scenario.initial_state
    wet = state.depth[:, 0] > .1
    report = {
        'scope': 'instantaneous initial-state MUSCL face flux; no integration or production promotion',
        'command': command, 'source_scenario': str(args.scenario.resolve()),
        'source_frame': str(args.frame.resolve()) if args.frame else None,
        'elapsed_seconds': args.elapsed, 'numerical_face_flux': flux,
        'experimental_prescribed_discharge_m3s': args.prescribed_discharge,
        'target_discharge_metadata_m3s': west.metadata.get('target_discharge_m3s'),
        'west_ghost_state_discharge_m3s': float(np.sum(boundary_depth) * west.velocity[0] * scenario.grid.dy),
        'west_cell_center_discharge_m3s': float(np.sum(state.hu[:, 0]) * scenario.grid.dy),
        'west_stage_above_prescribed_p10_p50_p90_m':
            np.percentile(state.eta[wet, 0] - west.stage, [10, 50, 90]).tolist() if wet.any() else [],
        'volume_m3': float(state.depth.sum() * scenario.grid.dx * scenario.grid.dy),
        'provenance': scenario.metadata.provenance,
    }
    (args.output / 'boundary-flux-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('command', 'provenance')}, indent=2))


if __name__ == '__main__':
    main()
