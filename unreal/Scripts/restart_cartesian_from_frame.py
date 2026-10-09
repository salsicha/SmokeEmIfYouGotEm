"""Restart a Cartesian cook package from one of its saved native frames.

Copies every tile package unchanged except initial_state.npz, which takes
the frame's exact depth and velocity, and records the frame's solver clock
as initial_time_seconds. Physics, bed, boundaries and timestep are unchanged.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(package, frame, output, inlet_scale=1.0):
    """inlet_scale multiplies every discharge-profile ghost velocity, so each
    inlet carries exactly that multiple of its discharge (depths unchanged).
    Used only to spin up a filling river faster; restart again at 1.0 to
    settle under the real budget."""
    package, frame, output = (Path(p).resolve() for p in (package, frame, output))
    if not inlet_scale > 0:
        raise ValueError('Positive inlet scale required')
    if output.exists():
        raise ValueError('Fresh output directory required')
    manifest = json.loads((package / 'manifest.json').read_text())
    complete = json.loads((frame / 'complete.json').read_text())
    fields = {name: np.load(frame / (name + '.npy')) for name in 'huv'}
    cells = manifest['grid']['tile_cells']
    if any(a.shape != (len(manifest['packages']) * cells, cells) for a in fields.values()):
        raise ValueError('Frame does not match the package tiles')
    output.mkdir(parents=True)
    inputs = []
    for ordinal, name in enumerate(manifest['packages']):
        source, target = package / name, output / name
        target.mkdir()
        for item in ('bed.npy', 'features.json', 'probes.json'):
            # Unchanged inputs are hard-linked (these tools only ever write
            # fresh directories, never edit a file in place); copy otherwise.
            try:
                os.link(source / item, target / item)
            except OSError:
                (target / item).write_bytes((source / item).read_bytes())
        scenario = json.loads((source / 'scenario.json').read_text())
        for boundary in scenario['boundaries']:
            if boundary.get('kind') == 'discharge_profile':
                boundary['ghost_cells'] = [[b, h, u * inlet_scale, v * inlet_scale] for b, h, u, v in boundary['ghost_cells']]
        (target / 'scenario.json').write_text(json.dumps(scenario, indent=2, allow_nan=False) + '\n')
        rows = slice(ordinal * cells, (ordinal + 1) * cells)
        h, u, v = (fields[c][rows] for c in 'huv')
        bed = np.load(source / 'bed.npy')
        np.savez_compressed(target / 'initial_state.npz', depth=h, eta=bed + h, u=u, v=v, hu=h * u, hv=h * v, wet=h > 1e-6)
        inputs.append(dict(name=name, files={f: sha(target / f) for f in
                                             ('scenario.json', 'bed.npy', 'initial_state.npz', 'features.json', 'probes.json')}))
    report = dict(manifest)
    report.update(inputs=inputs, initial_time_seconds=complete['time_seconds'],
                  restart=dict(source_manifest_sha256=sha(package / 'manifest.json'), frame=str(frame),
                               frame_step=complete['step'], frame_h_sha256=sha(frame / 'h.npy'), inlet_scale=inlet_scale))
    if inlet_scale != 1.0 and 'inlet_budget' in report:
        report['inlet_budget'] = {name: dict(row, target_m3s=row['target_m3s'] * inlet_scale,
                                             profile_normal_discharge_m3s=row['profile_normal_discharge_m3s'] * inlet_scale,
                                             spin_up_scale=inlet_scale)
                                  for name, row in report['inlet_budget'].items()}
        report['combined_inlet_discharge_m3s'] = report.get('combined_inlet_discharge_m3s', 0) * inlet_scale
    (output / 'manifest.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(tiles=len(inputs), initial_time_seconds=complete['time_seconds'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--frame', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--inlet-scale', type=float, default=1.0)
    args = parser.parse_args()
    build(args.package, args.frame, args.out, args.inlet_scale)
