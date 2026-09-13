"""Restore locally corroborated captured returns, never smooth measured anchors.

Previously rejected one-return cells inside photo-reviewed rock search areas
may be retained when two existing rock neighbours corroborate their elevation.
This does not certify unclassified LiDAR as ground or invent submerged sides.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_troublemaker_sparse_rock_returns import ROOT, SOURCE, BASE, load_candidates
from audit_captured_rock_selection_edges import cliff_audit
from register_captured_rock_vertices import oriented_quad_triangles
from south_fork_registered_mesh import RegisteredMeshSampler


def corroborated_cells(authority, height, candidate_height, candidates):
    """One non-recursive pass; inferred/new points cannot corroborate others."""
    if not (authority.shape == height.shape == candidate_height.shape == candidates.shape):
        raise ValueError('Matching source grids required')
    rock = authority == 3
    count = np.zeros(height.shape, np.uint8)
    minimum = np.full(height.shape, np.inf)
    maximum = np.full(height.shape, -np.inf)
    padded = np.pad(np.where(rock, height, np.nan), 1, constant_values=np.nan)
    rows, cols = height.shape
    for dr in range(3):
        for dc in range(3):
            if dr == dc == 1:
                continue
            neighbour = padded[dr:dr+rows, dc:dc+cols]
            finite = np.isfinite(neighbour)
            count += finite
            minimum = np.minimum(minimum, np.where(finite, neighbour, np.inf))
            maximum = np.maximum(maximum, np.where(finite, neighbour, -np.inf))
    return candidates & (authority == 2) & (count >= 2) & np.isfinite(candidate_height) & (candidate_height >= minimum-1) & (candidate_height <= maximum+1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output.exists():
        raise ValueError('Fresh output inside the project required')
    parent, mesh, points, chosen, counts, candidates = load_candidates(.3)
    original = {key: mesh[key].copy() for key in ('east_m', 'north_m', 'z_m', 'authority')}
    candidate_height = np.where(chosen >= 0, points['navd88_m'][chosen]-parent['vertical_origin_navd88_m'], np.nan)
    accepted = corroborated_cells(mesh['authority'], mesh['z_m'], candidate_height, candidates)
    indices = chosen[accepted]
    mesh['east_m'][accepted] = points['utm_easting_m'][indices]-parent['origin_utm_m'][0]
    mesh['north_m'][accepted] = points['utm_northing_m'][indices]-parent['origin_utm_m'][1]
    mesh['z_m'][accepted] = candidate_height[accepted]
    mesh['authority'][accepted] = 3
    source_index = np.full(mesh['authority'].shape, -1, np.int64)
    source_index[original['authority'] == 3] = mesh['rock_source_return_index']
    source_index[accepted] = indices
    mesh['rock_source_return_index'] = source_index[mesh['authority'] == 3]
    mesh['triangles'], stats = oriented_quad_triangles(mesh['east_m'], mesh['north_m'])
    sampler = RegisteredMeshSampler(mesh)
    assert all(np.array_equal(mesh[k][~accepted], original[k][~accepted]) for k in original)
    error = float(np.max(abs(sampler.sample(mesh['east_m'], mesh['north_m'])-mesh['z_m'])))
    assert error < 1e-7
    regions = json.loads((BASE/'rock_review_regions.json').read_text())['regions']
    with np.load(SOURCE/'registered_mesh_source.npz') as old:
        before = cliff_audit(old, regions)
    after = cliff_audit(mesh, regions)
    # The geometric effect must be demonstrated, not assumed from point count.
    assert after['steep_connecting_face_area_m2'] < before['steep_connecting_face_area_m2']
    output.mkdir(parents=True)
    target = output/'registered_mesh_source.npz'
    np.savez_compressed(target, **mesh)
    report = dict(parent)
    shifts = np.hypot(mesh['east_m']-mesh['nominal_east_axis_m'], mesh['north_m']-mesh['nominal_north_axis_m'][:,None])
    report.update(mesh_path=target.relative_to(ROOT).as_posix(), mesh_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        parent_mesh_path=(SOURCE/'registered_mesh_source.npz').relative_to(ROOT).as_posix(), parent_mesh_sha256=parent['mesh_sha256'],
        original_return_count=int(len(mesh['rock_source_return_index'])),
        max_rock_xy_registration_correction_m=float(shifts[mesh['authority'] == 3].max()),
        mean_rock_xy_registration_correction_m=float(shifts[mesh['authority'] == 3].mean()),
        all_recorded_heights_unchanged=True, non_rock_vertices_unchanged=False,
        original_measured_ground_and_rock_xyz_unchanged=True,
        recovery_method='Exact lower-envelope returns inside existing photo-reviewed search polygons, >0.3m above water; >=2 original rock cells in the eight-neighbour nominal 0.5m lattice and height within 1m of their range; no recursive propagation.',
        recovered_cells=int(accepted.sum()), recovered_single_return_cells=int((accepted & (counts == 1)).sum()),
        recovered_return_index=indices.tolist(), source_return_classification='Unclassified returns remain interpreted rock candidates, not certified ground.',
        maximum_vertex_sampling_error_m=error, before_cliff_audit=before, after_cliff_audit=after,
        **stats)
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'recovered_return_index'}, indent=2))


if __name__ == '__main__':
    main()
