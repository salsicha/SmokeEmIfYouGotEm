"""Remove only the original uncalibrated shelf/plunge from an isolated mesh.

This is a causal geometry comparison, NOT calibrated replacement bathymetry.
Captured vertices, registered XY, topology and inferred rock flanks are fixed.
The output must receive a fresh hydraulic solve and shared render/collision
integration; an evolved state on the old bed is not a valid candidate state.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def original_prior_surfaces(original, datum=220., cell=.5):
    """Reproduce the original builder, including NAVD88 float32 quantization."""
    from scipy.ndimage import distance_transform_edt
    wet = original['authority'] != 1
    clearance = distance_transform_edt(wet)*cell
    depth = np.where(wet, 2.4*(1-np.exp(-clearance/4.)), 0).astype(np.float32)
    surface = original['source_surface_m']+np.float32(datum)
    baseline = surface-depth
    dx, dy = original['east_m']+9., original['north_m']-1.
    along, across = -.93*dx+.36756*dy, -.36756*dx-.93*dy
    shelf = np.exp(-((along+2.)/2.)**4)*np.exp(-(across/7.)**6)
    plunge = np.exp(-((along-5.)/4.)**2)*np.exp(-(across/7.)**4)
    controlled = baseline+shelf*np.maximum(depth-.7, 0)-.7*plunge
    return baseline-np.float32(datum), controlled.astype(np.float32)-np.float32(datum)


def ablate(mesh, original, baseline, controlled):
    """Fail closed unless each edited vertex is the unchanged original prior."""
    shape = mesh['z_m'].shape
    for data in (mesh, original):
        for key in ('east_m', 'north_m', 'z_m', 'source_surface_m', 'authority'):
            if data[key].shape != shape or not np.isfinite(data[key]).all():
                raise ValueError('Matching finite source arrays required')
    if (baseline.shape != shape or controlled.shape != shape
            or not np.isfinite(baseline).all() or not np.isfinite(controlled).all()):
        raise ValueError('Matching finite prior surfaces required')
    original_editable = original['authority'] == 2
    if not np.array_equal(controlled[original_editable], original['z_m'][original_editable]):
        raise ValueError('Analytic reconstruction does not reproduce the original prior exactly')
    editable = mesh['authority'] == 2
    if not np.all(original_editable[editable]):
        raise ValueError('Current inferred vertex was not an original prior vertex')
    for key in ('east_m', 'north_m', 'z_m', 'source_surface_m'):
        if not np.array_equal(mesh[key][editable], original[key][editable]):
            raise ValueError('Current prior no longer equals original source: '+key)
    result = {k: v.copy() for k, v in mesh.items()}
    result['z_m'][editable] = baseline[editable]
    changed = result['z_m'] != mesh['z_m']
    if np.any(changed & ~editable):
        raise AssertionError('Protected source changed')
    return result, changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp candidate required')
    parent_path = args.parent_manifest.resolve()
    parent = json.loads(parent_path.read_text())
    if parent['schema'] != 'raftsim.captured_rock_xy_mesh_candidate.v1':
        raise ValueError('Registered source mesh required')
    mesh_path = (ROOT/parent['mesh_path']).resolve()
    if not mesh_path.is_relative_to(ROOT) or sha(mesh_path) != parent['mesh_sha256']:
        raise ValueError('Registered parent changed')
    prior_manifest = BASE/'troublemaker/geometry_candidate/manifest.json'
    original_path = prior_manifest.parent/'engine_mesh_source.npz'
    prior = json.loads(prior_manifest.read_text())
    if (prior['cell_m'] != .5 or prior['vertical_origin_navd88_m'] != 220.
            or prior['origin_utm_m'] != parent['origin_utm_m']
            or prior['inferred_hole_control']['center_local_east_north_m'] != [-9., 1.]
            or prior['inferred_hole_control']['shelf_depth_prior_m'] != .7
            or prior['inferred_hole_control']['plunge_extra_depth_prior_m'] != .7):
        raise ValueError('Unsupported original hypothesis or coordinate frame')
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in
              (parent_path, mesh_path, prior_manifest, original_path, Path(__file__))}
    with np.load(mesh_path, allow_pickle=False) as data:
        mesh = {k: data[k].copy() for k in data.files}
    with np.load(original_path, allow_pickle=False) as data:
        original = {k: data[k].copy() for k in data.files}
    baseline, controlled = original_prior_surfaces(original)
    result, changed = ablate(mesh, original, baseline, controlled)
    if not changed.any():
        raise ValueError('No analytic control remains to compare')
    from south_fork_registered_mesh import RegisteredMeshSampler
    RegisteredMeshSampler(result)  # Also verifies original winding/registration.
    if any(sha(ROOT/p) != digest for p, digest in inputs.items()):
        raise ValueError('Candidate input changed during preparation')
    output.mkdir()
    path = output/'registered_mesh_source.npz'
    np.savez_compressed(path, **result)
    with np.load(path, allow_pickle=False) as saved:
        if saved.files != list(result) or any(not np.array_equal(saved[k], v) for k, v in result.items()):
            raise ValueError('Saved candidate differs from verified geometry')
    delta = result['z_m'][changed].astype(float)-mesh['z_m'][changed]
    report = copy.deepcopy(parent)
    report.update(mesh_path=path.relative_to(ROOT).as_posix(), mesh_sha256=sha(path),
        parent_mesh_path=mesh_path.relative_to(ROOT).as_posix(), parent_mesh_sha256=sha(mesh_path),
        status='isolated_control_ablation_requires_fresh_hydraulics_and_shared_engine_geometry',
        control_ablation=dict(changed_vertices=int(changed.sum()), authority_code=2,
            height_change_range_m=[float(delta.min()), float(delta.max())],
            exact_original_prior_reproduced=True, registered_xy_and_topology_unchanged=True,
            all_non_prior_vertices_unchanged=True, inferred_flanks_unchanged=True,
            source_sha256=inputs),
        submerged_bed_authority='Uncalibrated shore-distance depth prior WITHOUT the original shelf/plunge. Causal comparison only; not measured or calibrated bathymetry.',
        hydraulic_validation_passed=False, game_integrated=False, production_promoted=False,
        evolved_old_bed_state_transfer_permitted=False)
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['control_ablation'], indent=2))


if __name__ == '__main__':
    main()
