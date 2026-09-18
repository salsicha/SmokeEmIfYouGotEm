"""Replace inferred cells with connected ORIGINAL constriction-edge returns.

An isolated hypothesis, never automatic gameplay promotion. Existing captured
vertices are immutable. Optional connecting-flank reconstruction uses the
existing two-metre inference prior, never relabeling interpolation as captured.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from audit_captured_rock_selection_edges import connected_to_seed
from audit_constriction_source_support import lower_returns
from audit_troublemaker_sparse_rock_returns import inside_polygon
from prepare_troublemaker_control_ablation import sha
from register_captured_rock_vertices import oriented_quad_triangles
from south_fork_registered_mesh import RegisteredMeshSampler

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
SELECTION = ROOT/'docs/reconstruction-review-2026-09-07/constriction-selection-20260918.json'


def candidate_cells(authority, chosen, counts):
    """Four-connected sampled support; unknown holes are never filled."""
    if authority.shape != chosen.shape or authority.shape != counts.shape:
        raise ValueError('Matching source grids required')
    editable = np.isin(authority, [2, 5])
    supported = editable & (chosen >= 0) & (counts >= 2)
    seeds = authority == 3
    return connected_to_seed(supported | seeds, seeds) & supported


def recover(mesh, returns, selection):
    if selection['measured_outline'] or selection['measured_flanks'] or selection['source_xyz_may_be_moved'] or selection['source_classifications_may_be_changed']:
        raise ValueError('Only explicitly interpreted, immutable-source selection supported')
    origin = np.asarray(selection['origin_utm_and_vertical_datum_m'])
    xyz = np.column_stack([returns[k] for k in ('utm_easting_m', 'utm_northing_m', 'navd88_m')])-origin
    row = np.floor((mesh['nominal_north_axis_m'][0]+.25-xyz[:, 1])/.5).astype(int)
    col = np.floor((xyz[:, 0]-mesh['nominal_east_axis_m'][0]+.25)/.5).astype(int)
    rows, cols = mesh['authority'].shape
    eligible = (row >= 0) & (row < rows) & (col >= 0) & (col < cols)
    eligible &= inside_polygon(xyz[:, 0], xyz[:, 1], selection['interpreted_selection_polygon_m'])
    eligible &= np.isin(returns['classification'], [1, 2, 10]) & returns['within_survey_water']
    above = returns['height_above_flattened_surface_m']
    eligible &= (above > .3) & (above < 8)
    original_ids = np.flatnonzero(eligible)
    ids, counts = lower_returns(xyz[original_ids], row[original_ids]*cols+col[original_ids], original_ids)
    chosen = np.full((rows, cols), -1, dtype=np.int64)
    support = np.zeros((rows, cols), dtype=int)
    chosen[row[ids], col[ids]] = ids
    support[row[ids], col[ids]] = counts
    accepted = candidate_cells(mesh['authority'], chosen, support)
    if not accepted.any():
        raise ValueError('No source-connected additions in interpreted selection')
    new_ids = chosen[accepted]
    result = {key: value.copy() for key, value in mesh.items()}
    for axis, key in enumerate(('east_m', 'north_m', 'z_m')):
        result[key][accepted] = xyz[new_ids, axis]
    result['authority'][accepted] = 3
    return_ids = np.full((rows, cols), -1, dtype=np.int64)
    return_ids[mesh['authority'] == 3] = mesh['rock_source_return_index']
    return_ids[accepted] = new_ids
    result['rock_source_return_index'] = return_ids[result['authority'] == 3]
    new_faces, _ = oriented_quad_triangles(result['east_m'], result['north_m'])
    # Preserve the parent's partition everywhere without newly moved XY.
    affected = np.any(accepted.ravel()[mesh['triangles']], axis=1)
    half = len(affected)//2
    affected_quad = affected[:half] | affected[half:]
    affected = np.r_[affected_quad, affected_quad]
    result['triangles'][affected] = new_faces[affected]
    RegisteredMeshSampler(result)  # Reject folded/unsupported partitions.
    for key in ('east_m', 'north_m', 'z_m', 'authority', 'source_surface_m'):
        if not np.array_equal(result[key][~accepted], mesh[key][~accepted]):
            raise ValueError('Protected prior geometry changed: '+key)
    if not np.array_equal(result['triangles'][~affected], mesh['triangles'][~affected]):
        raise ValueError('Unrelated triangle connectivity changed')
    return result, accepted, new_ids, support[accepted]


def reconstruct_added_flanks(mesh, added, baseline):
    from scipy.spatial import cKDTree
    from reconstruct_troublemaker_rock_flanks import extend_fixed_surface
    xyz = np.column_stack([mesh[k].ravel() for k in ('east_m', 'north_m', 'z_m')])
    if added.shape != mesh['authority'].shape or baseline.shape != added.shape or not added.any():
        raise ValueError('Matching new-source mask and original bed prior required')
    distance, _ = cKDTree(xyz[added.ravel(), :2]).query(xyz[:, :2])
    editable = np.isin(mesh['authority'].ravel(), [2, 5]) & (distance <= 2.)
    xyz[editable, 2] = baseline.ravel()[editable]
    height, stats = extend_fixed_surface(xyz, mesh['triangles'], editable)
    result = {k: v.copy() for k, v in mesh.items()}
    result['z_m'].ravel()[editable] = height[editable]
    modified = editable & (result['z_m'].ravel() != mesh['z_m'].ravel())
    result['authority'].ravel()[modified] = 5
    for key in ('east_m', 'north_m', 'z_m', 'authority'):
        assert np.array_equal(result[key].ravel()[~editable], mesh[key].ravel()[~editable])
    return result, dict(support_band_prior_m=2., inferred_changed_vertices=int(modified.sum()),
                        maximum_distance_from_new_capture_m=float(distance[modified].max()) if modified.any() else 0.,
                        sampled_support_added=False, **stats)


def main(output, reconstruct_flanks=False):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp candidate required')
    selection = json.loads(SELECTION.read_text())
    parent_path = BASE/'full_reach/source_matched_20260917/registered_mesh_source.npz'
    returns_path = BASE/'troublemaker/classified_lidar_returns.npz'
    paths = [parent_path, returns_path, BASE/'sources/troublemaker_naip.png', BASE/'sources/troublemaker_naip_export.json']
    expected = [selection[k] for k in ('source_mesh_sha256', 'original_returns_sha256', 'source_naip_sha256', 'source_naip_export_sha256')]
    if any(sha(p) != digest for p, digest in zip(paths, expected)):
        raise ValueError('Reviewed source identity changed')
    with np.load(parent_path, allow_pickle=False) as archive:
        mesh = {key: archive[key] for key in archive.files}
    with np.load(returns_path, allow_pickle=False) as archive:
        returns = {key: archive[key] for key in archive.files}
    result, accepted, ids, counts = recover(mesh, returns, selection)
    flank_report = None
    if reconstruct_flanks:
        from prepare_troublemaker_control_ablation import original_prior_surfaces
        prior = BASE/'troublemaker/geometry_candidate/engine_mesh_source.npz'
        if sha(prior) != '3b87db1736c81d6d0c44aae79d53c9aab52c57283ef8cbdbee3dae3a5fc568a7':
            raise ValueError('Original prior identity changed')
        with np.load(prior, allow_pickle=False) as archive:
            original = {k: archive[k] for k in archive.files}
        baseline, controlled = original_prior_surfaces(original)
        assert np.array_equal(controlled[original['authority'] == 2], original['z_m'][original['authority'] == 2])
        result, flank_report = reconstruct_added_flanks(result, accepted, baseline)
        RegisteredMeshSampler(result)
    output.mkdir()
    path = output/'registered_mesh_source.npz'
    np.savez_compressed(path, **result)
    with np.load(path, allow_pickle=False) as saved:
        if any(not np.array_equal(saved[k], v) for k, v in result.items()):
            raise ValueError('Saved candidate differs')
    report = dict(schema='raftsim.constriction_source_candidate.v1',
                  mesh_path=str(path.relative_to(ROOT)), mesh_sha256=sha(path),
                  parent_mesh_sha256=sha(parent_path), selection_path=str(SELECTION.relative_to(ROOT)), selection_sha256=sha(SELECTION),
                  original_returns_sha256=sha(returns_path), added_source_vertices=int(accepted.sum()),
                  original_captured_xyz_preserved=True, unrelated_vertices_and_triangles_preserved=True,
                  changed_triangles=int(np.any(result['triangles'] != mesh['triangles'], axis=1).sum()),
                  source_ids=ids.tolist(), support_counts=counts.tolist(),
                  height_delta_range_m=[float((result['z_m']-mesh['z_m'])[accepted].min()), float((result['z_m']-mesh['z_m'])[accepted].max())],
                  additional_flank_interpolation=flank_report, missing_cells_reclassified_as_captured=False,
                  source_z_storage='Existing float32 ground height precision; original double-precision returns retained by source ID.',
                  requires_fresh_hydraulics=True, evolved_old_bed_state_transfer_allowed=False,
                  game_integrated=False, production_promoted=False, visual_or_physical_accepted=False)
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('source_ids', 'support_counts')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reconstruct-flanks', action='store_true')
    args = parser.parse_args()
    main(args.output, args.reconstruct_flanks)
