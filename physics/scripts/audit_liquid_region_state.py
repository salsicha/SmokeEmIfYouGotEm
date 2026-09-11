"""Independently reassemble emitted region files against the parent water.

Byte hashes establish input identity; direct indexed comparisons establish no
lost/duplicated/moved seeds, changed momentum, or new internal inlet sources.
This does not verify a GPU handoff, pressure continuity or runtime conservation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def audit(parent, directory):
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = json.loads((directory/'manifest.json').read_text())
    for name, digest in manifest['parent_files_sha256'].items():
        if sha(parent/name) != digest:
            raise ValueError('Parent changed: '+name)
    window = json.loads((parent/'manifest.json').read_text())
    source = json.loads((parent/'native_source_profile.json').read_text())
    initial = json.loads((parent/'hydraulic_initial_state.json').read_text())
    domain = source['domain']
    spacing = np.asarray(domain['cell_size_m'])
    parent_bounds = np.asarray(domain['native_face_bounds_m'])
    seed_positions = np.asarray(initial['positions_world_cm'])
    seed_velocity = np.asarray(initial['velocities_world_cm_per_s'])
    source_positions = np.asarray(source['positions_world_offset_cm'])+window['local_origin_engine_cm']
    source_velocity = np.asarray(source['velocities_world_cm_per_s'])
    source_weights = np.asarray(source['weights_m3_per_s'])
    seen_seed = np.zeros(len(seed_positions), dtype=int)
    seen_source = np.zeros(len(source_positions), dtype=int)
    seen_cells = np.zeros(domain['physical_cells'][1::-1], dtype=int)
    bundles = []
    inflow = 0.
    for record in manifest['region_files']:
        path = directory/record['file']
        if sha(path) != record['sha256']:
            raise ValueError('Region changed: '+record['file'])
        b = json.loads(path.read_text()); bundles.append(b)
        seed_ids = np.asarray(b['seed_parent_ids'], dtype=int)
        source_ids = np.asarray(b['source_parent_ids'], dtype=int)
        for ids, seen in ((seed_ids, seen_seed), (source_ids, seen_source)):
            if np.any(ids < 0) or np.any(ids >= len(seen)):
                raise ValueError('Invalid parent identity')
            np.add.at(seen, ids, 1)
        for actual, expected in ((b['positions_canonical_cm'], seed_positions[seed_ids]),
                                 (b['velocities_canonical_cm_per_s'], seed_velocity[seed_ids]),
                                 (b['source_positions_canonical_cm'], source_positions[source_ids]),
                                 (b['source_velocities_canonical_cm_per_s'], source_velocity[source_ids])):
            if not np.array_equal(np.asarray(actual).reshape(-1, 3), expected):
                raise ValueError('Water position or momentum changed')
        if not np.array_equal(b['source_weights_m3_per_s'], source_weights[source_ids]):
            raise ValueError('Inlet weights changed')
        if b['internal_source_emission'] or b['canonical_frame'] != 'parent-ENU-centimetres':
            raise ValueError('Internal inlet or inconsistent canonical frame')
        (x0, y0), (x1, y1) = b['cell_bounds_xy']
        if not (0 <= x0 < x1 <= seen_cells.shape[1] and 0 <= y0 < y1 <= seen_cells.shape[0]):
            raise ValueError('Region cell range outside parent')
        seen_cells[y0:y1, x0:x1] += 1
        bounds = parent_bounds[0]+np.array([[x0, y0], [x1, y1]])*spacing[:2]
        if not np.array_equal(bounds, b['bounds_station_lateral_m']):
            raise ValueError('Cell bounds and geographic bounds disagree')
        axes = np.asarray([b['axis_x_canonical'], b['axis_y_canonical']])
        center = bounds.mean(axis=0)@axes*100
        if not np.allclose(b['origin_canonical_cm'], [*center, window['local_origin_engine_cm'][2]], atol=1e-9, rtol=0):
            raise ValueError('Region origin changed datum or translation')
        # Check each retained point belongs to its declared half-open physical
        # domain, independently of the partitioner's classification function.
        for values in (seed_positions[seed_ids], source_positions[source_ids]):
            sl = values[:, :2]@axes.T/100
            inside = (sl >= bounds[0]) & ((sl < bounds[1]) | ((bounds[1] == parent_bounds[1]) & (sl == bounds[1])))
            if not np.all(inside):
                raise ValueError('Water assigned to the wrong region')
        if len(seed_ids) > 163840 or np.prod(b['computational_cells'])*8 > 2000000:
            raise ValueError('Existing regional capacity exceeded')
        volume = domain['nominal_particle_volume_m3']
        if b['nominal_particle_volume_m3'] != volume:
            raise ValueError('Regional particle volume changed')
        q = float(source_weights[source_ids].sum())
        if q != b['external_inflow_m3_per_s'] or q/volume != b['external_spawn_particles_per_second']:
            raise ValueError('Inlet rate/volume inconsistent')
        inflow += q
    if not (np.all(seen_seed == 1) and np.all(seen_source == 1) and np.all(seen_cells == 1)):
        raise ValueError('Lost or duplicated water/site/cell ownership')
    expected_pairs = set()
    for lower in bundles:
        for upper in bundles:
            a0, a1 = np.asarray(lower['cell_bounds_xy']); b0, b1 = np.asarray(upper['cell_bounds_xy'])
            for axis in range(2):
                if a1[axis] == b0[axis] and a0[1-axis] == b0[1-axis] and a1[1-axis] == b1[1-axis]:
                    expected_pairs.add((lower['id'], upper['id'], axis, int(a1[axis]), int(a0[1-axis]), int(a1[1-axis])))
    actual_pairs = []
    for face in manifest['interfaces']:
        if face['native_source_emission'] or face['coupling'] != 'shared-pressure-velocity-and-particle-transfer':
            raise ValueError('Internal face incorrectly forced by native reservoir')
        actual_pairs.append((face['lower_region'], face['upper_region'], face['axis'], face['parent_face_index'], *face['tangential_cell_range']))
    if set(actual_pairs) != expected_pairs or len(actual_pairs) != len(expected_pairs):
        raise ValueError('Missing, duplicated or mismatched shared interface')
    if not np.isclose(inflow, source['total_inflow_m3_per_s'], atol=1e-9, rtol=0):
        raise ValueError('Changed total river inflow')
    return dict(prepared_ownership_passed=True, regions=len(bundles), shared_interfaces=len(expected_pairs),
        seeds_verified_once=len(seen_seed), source_sites_verified_once=len(seen_source),
        physical_cells_xy_verified_once=int(seen_cells.size), canonical_positions_and_velocities_exact=True,
        external_inflow_m3_per_s=inflow, nominal_particle_volume_m3=domain['nominal_particle_volume_m3'],
        represented_nominal_volume_m3=len(seen_seed)*domain['nominal_particle_volume_m3'],
        aggregate_render_voxels_including_halos=sum(int(np.prod(b['computational_cells'])*8) for b in bundles),
        manifest_sha256=sha(directory/'manifest.json'), runtime_exchange_verified=False,
        pressure_and_surface_continuity_verified=False, performance_or_visual_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parent', type=Path); parser.add_argument('regions', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Keep previous evidence')
    result = audit(args.parent, args.regions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))
