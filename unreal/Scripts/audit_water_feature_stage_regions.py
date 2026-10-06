"""Locate local-step level-set changes without replaying or changing the solver.

Partition fixed-field integrals into intervals touching outermost grid centers
and all remaining intervals. This is not a conserved-mass or mesh audit.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from audit_water_feature_stage_volumes import sha256
from water_feature_cell_volume import reconstructed_volume


def partitions(shape):
    indices = np.indices(tuple(n+1 for n in shape))
    outer_half = np.zeros(indices.shape[1:], bool)
    touches_outer = np.zeros_like(outer_half)
    for axis, size in enumerate(shape):
        outer_half |= (indices[axis] == 0) | (indices[axis] == size)
        touches_outer |= (indices[axis] <= 1) | (indices[axis] >= size-1)
    return dict(outer_half_cells=outer_half,
                outer_center_adjacent_full_intervals=touches_outer & ~outer_half,
                interior_intervals=~touches_outer)


def changes(before, after, solid=None):
    changed = before != after
    indices = np.argwhere(changed)
    outer = np.zeros_like(changed)
    for axis in range(3):
        sl = [slice(None)]*3
        for index in (0, before.shape[axis]-1):
            sl[axis] = index
            outer[tuple(sl)] = True
    result = dict(changed_centers=int(changed.sum()),
                changed_non_outermost_centers=int(np.sum(changed & ~outer)),
                index_bounds=[indices.min(axis=0).tolist(), indices.max(axis=0).tolist()] if len(indices) else None,
                sign_gained_centers=int(np.sum((before >= 0) & (after < 0))),
                sign_lost_centers=int(np.sum((before < 0) & (after >= 0))))
    if solid is not None:
        result['outside_solid_sign_gained_centers'] = int(np.sum((before >= 0) & (after < 0) & (solid >= 0)))
        result['outside_solid_sign_lost_centers'] = int(np.sum((before < 0) & (after >= 0) & (solid >= 0)))
    return result


def audit(path, subdivisions):
    probe = json.loads(path.read_text())
    if not (probe['complete'] and probe['original_vdb_unchanged']
            and probe['extra_extrapolation_checkpoints']
            and probe['resumed_primary_matches_native_count_positions_and_velocities']):
        raise ValueError('Need completed eight-checkpoint native probe')
    original = path.parent/'cache'/'data'/f"fluid_data_{probe['frame']:04d}.vdb"
    if sha256(original) != probe['original_vdb_sha256']:
        raise ValueError('Original VDB changed')
    solid_path = Path(probe['solid_file'])
    solid_hash = sha256(solid_path)
    solid = np.load(solid_path, allow_pickle=False)
    groups = partitions(solid.shape)
    if not np.all(sum(mask.astype(int) for mask in groups.values()) == 1):
        raise ValueError('Region masks must partition all intervals')
    rows, previous_phi, previous_contributions = [], None, None
    for source_row in probe['rows']:
        if 'interface_file' not in source_row:
            continue
        phi_path = Path(source_row['interface_file'])
        if sha256(phi_path) != source_row['interface_sha256']:
            raise ValueError('Interface snapshot changed')
        phi = np.load(phi_path, allow_pickle=False)
        result = reconstructed_volume(phi, solid, probe['engine_cell_size_m'], subdivisions,
                                      return_interval_volumes=True)
        contributions = result.pop('interval_volumes_m3')
        row = dict(stage=source_row['stage'], interface_sha256=source_row['interface_sha256'],
                   volume=result, regions={name: float(contributions[mask].sum()) for name, mask in groups.items()})
        if previous_phi is not None:
            row['center_changes'] = changes(previous_phi, phi, solid)
            delta = contributions-previous_contributions
            row['regional_delta_m3'] = {name: dict(net=float(delta[mask].sum()),
                    positive=float(np.maximum(delta[mask], 0).sum()),
                    negative=float(np.minimum(delta[mask], 0).sum())) for name, mask in groups.items()}
        rows.append(row)
        previous_phi, previous_contributions = phi, contributions
        print('REGIONAL_STAGE', json.dumps(row), flush=True)
    if len(rows) != 8:
        raise ValueError('Expected eight checkpoints')
    if sha256(original) != probe['original_vdb_sha256'] or sha256(solid_path) != solid_hash:
        raise ValueError('Original changed during audit')
    return dict(complete=True, accepted=False, scope=__doc__, probe_sha256=sha256(path),
                solid_sha256=solid_hash, original_vdb_sha256=probe['original_vdb_sha256'],
                originals_unchanged=True, subdivisions=subdivisions, rows=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--subdivisions', type=int, choices=(8, 16, 32), default=16)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = audit(args.probe, args.subdivisions)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print('REGIONAL_AUDIT_COMPLETE', args.output, flush=True)


if __name__ == '__main__':
    main()
