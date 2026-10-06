"""Extend the unbiased discharge-depth inference into the registered rapid.

Candidate only: change authority-2 underwater vertices, never captured ground,
rock returns, inferred rock flanks, XY or topology. The source surface is
hydroflattened, not bathymetry; its flight-time discharge is unknown. Do not use
the simulation-fitted bias or claim settling. A fresh coupled solve and shared
render/collision import are required before playable promotion.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def revise(mesh, station, clearance, design, blend_m=30.0):
    """Apply the same strip-conveyance normal depth, with a seam-preserving taper."""
    shape = mesh['z_m'].shape
    if len(shape) != 2 or min(shape) < 2 or not np.isfinite(blend_m) or blend_m <= 0:
        raise ValueError('Finite positive seam taper and a two-dimensional mesh required')
    for key in ('east_m', 'north_m', 'source_surface_m', 'authority'):
        if mesh[key].shape != shape or not np.isfinite(mesh[key]).all():
            raise ValueError('Matching finite source arrays required')
    if (station.shape != shape or clearance.shape != shape or
            not all(np.isfinite(a).all() for a in (station, clearance, mesh['z_m'])) or
            np.any(clearance < 0)):
        raise ValueError('Finite stations, bed and nonnegative clearance required')
    names = ('station_center_m', 'normal_depth_m', 'pool_weight', 'bank_shape_length_m')
    d = {k: np.asarray(design[k], dtype=float) for k in names}
    axis = d['station_center_m']
    if (axis.ndim != 1 or len(axis) < 2 or np.any(np.diff(axis) <= 0) or
            any(a.shape != axis.shape or not np.isfinite(a).all() for a in d.values()) or
            np.any(d['normal_depth_m'] <= 0) or np.any(d['bank_shape_length_m'] <= 0) or
            np.any((d['pool_weight'] < 0) | (d['pool_weight'] > 1))):
        raise ValueError('Valid ordered conveyance design required')
    editable = mesh['authority'] == 2
    if not np.isin(mesh['authority'], (1, 2, 3, 4, 5)).all():
        raise ValueError('Unknown geometry authority')
    if np.any((station[editable] < axis[0]) | (station[editable] > axis[-1])):
        raise ValueError('No station extrapolation outside the design')
    normal = np.interp(station, axis, d['normal_depth_m'])
    pool = np.interp(station, axis, d['pool_weight'])
    length = np.interp(station, axis, d['bank_shape_length_m'])
    # Same explicitly inferred pool prior as the full-reach design; no fitted
    # centreline depth/bias, lower clip or photographic calibration is imported.
    central = np.maximum(normal, normal + (2.2 - normal) * pool)
    depth = central * np.clip(clearance / length, 0, 1)
    east, north = mesh['east_m'], mesh['north_m']
    margin = np.minimum.reduce((east-east.min(), east.max()-east,
                                north-north.min(), north.max()-north))
    t = np.clip(margin / blend_m, 0, 1)
    weight = t*t*(3-2*t)
    target = mesh['source_surface_m'] - depth
    if np.any(mesh['z_m'][editable] > mesh['source_surface_m'][editable] + 1e-5):
        raise ValueError('Editable bed is above its source surface')
    result = {k: v.copy() for k, v in mesh.items()}
    z = result['z_m']
    z[editable] = (mesh['z_m'][editable] + weight[editable] *
                   (target[editable] - mesh['z_m'][editable]))
    if not np.array_equal(z[~editable], mesh['z_m'][~editable]):
        raise AssertionError('Protected geometry changed')
    return result, weight, depth


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mesh', type=Path, required=True)
    p.add_argument('--mesh-manifest', type=Path, required=True)
    p.add_argument('--bed-design', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp output required')
    parent = json.loads(args.mesh_manifest.read_text())
    bed = json.loads((args.bed_design/'manifest.json').read_text())
    design_path = ROOT/bed['outputs']['design']['path']
    route_path = ROOT/bed['inputs']['route']['path']
    if (sha(args.mesh) != parent['mesh_sha256'] or
            sha(design_path) != bed['outputs']['design']['sha256'] or
            sha(route_path) != bed['inputs']['route']['sha256']):
        raise ValueError('Source or design hash mismatch')
    if (parent['vertical_origin_navd88_m'] != 220 or
            bed['parameters']['pool_depth_m'] != 2.2):
        raise ValueError('Unsupported datum or pool prior')
    with np.load(args.mesh, allow_pickle=False) as data:
        mesh = {k: data[k].copy() for k in data.files}
    from scipy.ndimage import distance_transform_edt
    from prepare_south_fork_discharge_bed_cook import nearest_route
    from south_fork_registered_mesh import RegisteredMeshSampler
    RegisteredMeshSampler(mesh)
    dx = np.diff(mesh['nominal_east_axis_m'])
    dy = -np.diff(mesh['nominal_north_axis_m'])
    if not np.allclose(dx, .5) or not np.allclose(dy, .5):
        raise ValueError('Expected half-metre registered source lattice')
    route = json.loads(route_path.read_text())
    points = np.asarray(route['points'])
    origin_delta = np.asarray(parent['origin_utm_m']) - route['origin_utm_m']
    xy = np.column_stack((mesh['east_m'].ravel(), mesh['north_m'].ravel())) + origin_delta
    station = points[nearest_route(xy, points[:, 1:3]), 0].reshape(mesh['z_m'].shape)
    # Match the original half-metre source's shore-distance convention. This
    # does not classify unmeasured submerged rock or invent additional rocks.
    clearance = distance_transform_edt(mesh['authority'] != 1)*.5
    result, weight, depth = revise(mesh, station, clearance, json.loads(design_path.read_text()))
    RegisteredMeshSampler(result)
    changed = result['z_m'] != mesh['z_m']
    if not changed.any():
        raise ValueError('No inferred bed vertices changed')
    delta = result['z_m'] - mesh['z_m']
    report = dict(parent)
    report.update(mesh_path=(out/'registered_mesh_source.npz').relative_to(ROOT).as_posix(),
        status='inferred_conveyance_candidate_requires_fresh_flow_and_shared_scene',
        hydraulic_validation_passed=False, game_integrated=False, production_promoted=False,
        all_recorded_heights_unchanged=False, non_rock_vertices_unchanged=False,
        evolved_old_bed_state_transfer_permitted=False,
        submerged_bed_authority='Unbiased strip-conveyance depth plus inferred pool prior; NOT measured bathymetry')
    report['conveyance_revision'] = dict(
        parent_mesh_sha256=sha(args.mesh), parent_manifest_sha256=sha(args.mesh_manifest),
        design_sha256=sha(design_path), bed_manifest_sha256=sha(args.bed_design/'manifest.json'),
        route_sha256=sha(route_path), script_sha256=sha(Path(__file__)),
        authored_discharge_m3s=bed['parameters']['discharge_m3s'],
        flight_time_discharge_known=False, simulated_bias_used=False,
        editable_authority=2, seam_taper_m=30., protected_geometry_unchanged=True,
        xy_topology_and_source_surface_unchanged=True, changed_vertices=int(changed.sum()),
        delta_z_m_min_median_max=np.percentile(delta[changed], [0, 50, 100]).tolist(),
        settling_accepted=False, measured_bathymetry=False)
    out.mkdir()
    np.savez_compressed(out/'registered_mesh_source.npz', **result)
    report['mesh_sha256'] = sha(out/'registered_mesh_source.npz')
    (out/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['conveyance_revision'], indent=2))


if __name__ == '__main__':
    main()
