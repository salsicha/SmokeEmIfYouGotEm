"""Refine preserved local-step interfaces without replaying or altering a solver.

These are integrals of fixed trilinear fields, not conserved particle mass.
Midpoint refinement differences are not rigorous uncertainty bounds.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from water_feature_cell_volume import reconstructed_volume


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def audit(probe_path, subdivisions):
    probe = json.loads(probe_path.read_text())
    if not (probe['complete'] and probe['original_vdb_unchanged']
            and probe['resumed_primary_matches_native_count_positions_and_velocities']):
        raise ValueError('Require a completed, independently validated native probe')
    original = probe_path.parent/'cache'/'data'/f"fluid_data_{probe['frame']:04d}.vdb"
    if sha256(original) != probe['original_vdb_sha256']:
        raise ValueError('Original VDB changed since probe')
    solid_path = Path(probe['solid_file'])
    solid_hash = sha256(solid_path)
    solid = np.load(solid_path, allow_pickle=False)
    rows = []
    for row in probe['rows']:
        if 'interface_file' not in row:
            continue
        path = Path(row['interface_file'])
        if sha256(path) != row['interface_sha256']:
            raise ValueError(f'Interface hash mismatch: {path}')
        phi = np.load(path, allow_pickle=False)
        values = {str(n): reconstructed_volume(phi, solid, probe['engine_cell_size_m'], n)
                  for n in subdivisions}
        result = dict(stage=row['stage'], interface_sha256=row['interface_sha256'],
                      sign_volume_m3=row['outside_solid_sign_volume_m3'], refinements=values)
        if '8' in values:
            if abs(values['8']['volume_m3']-row['partial_cell_volume_m3']) > 1e-12:
                raise ValueError('Independent n8 readback disagrees with native probe')
        if rows:
            result['delta_from_previous_m3'] = {str(n): values[str(n)]['volume_m3']-
                rows[-1]['refinements'][str(n)]['volume_m3'] for n in subdivisions}
        rows.append(result)
        print('REFINED_STAGE', row['stage'], {n: values[str(n)]['volume_m3'] for n in subdivisions}, flush=True)
    expected_count = 8 if probe.get('extra_extrapolation_checkpoints') else 6
    if len(rows) != expected_count:
        raise ValueError(f'Expected {expected_count} saved interface stages, found {len(rows)}')
    if sha256(solid_path) != solid_hash or sha256(original) != probe['original_vdb_sha256']:
        raise ValueError('Input changed during audit')
    return dict(complete=True, accepted=False, scope=__doc__, probe_file=str(probe_path),
                probe_sha256=sha256(probe_path), solid_sha256=solid_hash,
                original_vdb_sha256=probe['original_vdb_sha256'], originals_unchanged=True,
                rows=rows, net_local_step_delta_m3={str(n): rows[-1]['refinements'][str(n)]['volume_m3']-
                    rows[0]['refinements'][str(n)]['volume_m3'] for n in subdivisions})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--subdivisions', type=int, nargs='+', default=[8, 16, 32])
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = audit(args.probe, args.subdivisions)
    # Exclusive creation prevents accidentally overwriting prior evidence.
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print('STAGE_REFINEMENT_COMPLETE', args.output, flush=True)


if __name__ == '__main__':
    main()
