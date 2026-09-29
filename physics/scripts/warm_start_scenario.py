"""Seed a curvilinear scenario package with a previous cook's last frame (numpy only).

    warm_start_scenario.py <scenario_root> <run>

Rewrites <scenario_root>/scenario/initial_state.npz from the run's last frame, so a
cook on a locally changed bed (observed rapid features) starts from settled water
instead of the builder's still-water guess. The frame must be on the same grid.
The surface is kept; depth is re-derived against the new bed (cells now above
the surface become dry) and momentum is scaled to the new depth.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from audit_observed_rapids import last_frame
from export_hance_evidence_runtime import read_frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scenario_root', type=Path)
    ap.add_argument('run', type=Path)
    args = ap.parse_args()
    pkg = args.scenario_root / 'scenario'
    sc = json.loads((pkg / 'scenario.json').read_text())
    ny, nx = sc['grid']['ny'], sc['grid']['nx']
    bed = np.load(pkg / 'bed.npy').astype(np.float64)
    if (args.run / 'manifest.json').exists() and json.loads((args.run / 'manifest.json').read_text()).get('schema') == \
            'raftsim.cooked_flow_fields.v1':
        # a committed export's cooked_flow_fields folder (its single band) on the same grid
        cm = json.loads((args.run / 'manifest.json').read_text()); (band,) = cm['bands']
        A = {k: np.load(args.run / band['arrays'][k]['file']).astype(np.float64) for k in ('bed', 'h', 'u', 'v')}
        assert A['h'].shape == (ny, nx), 'cooked fields are on another grid'
        f = dict(h=A['h'], eta=A['bed'] + A['h'], u=A['u'], v=A['v'])
        src = str(args.run)
    else:
        f = read_frame(last_frame(args.run), ny, nx)
        src = str(last_frame(args.run))
    state = dict(np.load(pkg / 'initial_state.npz'))
    wet0 = f['h'] > 1e-6
    eta = np.where(wet0, f['eta'], bed)
    h = np.maximum(eta - bed, 0.0)
    wet = h > 1e-6
    u = np.where(wet, f['u'], 0.0); v = np.where(wet, f['v'], 0.0)
    for key, val in (('depth', h), ('eta', np.where(wet, eta, bed)), ('u', u), ('v', v), ('hu', h * u), ('hv', h * v)):
        state[key] = np.asarray(val, dtype=state[key].dtype)
    state['wet'] = wet
    np.savez(pkg / 'initial_state.npz', **state)
    print(json.dumps(dict(seeded_from=src, wet_cells=int(wet.sum()), newly_dry=int((wet0 & ~wet).sum()))))


if __name__ == '__main__':
    main()
