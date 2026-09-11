"""Exact clipped collision surface and conservative boundary handoff for 3D water.

The top comes from the registered South Fork candidate, not new measurements.
Side walls and a bottom seal exist only to make a signed-distance solid outside
the fluid window. This package is not a new hydraulic solve or rapid identity.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def positive_xy(value, label):
    result = np.asarray(value, dtype=float)
    if result.ndim == 0:
        result = np.repeat(result, 2)
    if result.shape != (2,) or not np.isfinite(result).all() or (result <= 0).any():
        raise ValueError(f'{label} requires positive finite X/Y extents')
    return result


def write_collision_probes(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    source = directory/'collision_solid.npz'
    if sha(source) != manifest['solid_sha256']:
        raise ValueError('Changed solid')
    data = np.load(source)
    triangles = data['triangles'][:int(data['top_triangle_count'])]
    probes = data['vertices_local_m'][triangles].mean(axis=1)*100
    with (directory/'collision_probes.json').open('x') as stream:
        json.dump({'solid_sha256': manifest['solid_sha256'],
                   'top_triangle_centroids_local_cm': probes.tolist()}, stream)


def clip_triangle(triangle, half_size):
    """Clip without smoothing/retriangulating the source surface itself."""
    half_size = positive_xy(half_size, 'Collision patch')
    polygon = [np.asarray(p, dtype=float) for p in triangle]
    for axis, sign in ((0, 1), (0, -1), (1, 1), (1, -1)):
        clipped = []
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            da, db = half_size[axis] - sign*a[axis], half_size[axis] - sign*b[axis]
            if da >= 0:
                clipped.append(a)
            if (da >= 0) != (db >= 0):
                clipped.append(a + da/(da-db)*(b-a))
        polygon = clipped
        if len(polygon) < 3:
            return []
    return [np.array([polygon[0], polygon[i], polygon[i+1]])
            for i in range(1, len(polygon)-1)]


def closed_patch(vertices, faces, half_size, bottom_z):
    half_size = positive_xy(half_size, 'Collision patch')
    points, top, source_faces = [], [], []
    indices = {}
    def add(point):
        # Deduplicate shared-edge interpolation roundoff, never snap to a grid.
        key = tuple(np.round(point, 9))
        if key not in indices:
            indices[key] = len(points)
            points.append(point)
        return indices[key]
    triangles = vertices[faces]
    relevant = np.all(triangles[:, :, :2].max(axis=1) >= -half_size, axis=1)
    relevant &= np.all(triangles[:, :, :2].min(axis=1) <= half_size, axis=1)
    for source_index in np.flatnonzero(relevant):
        for triangle in clip_triangle(triangles[source_index], half_size):
            if np.linalg.norm(np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0])) < 1e-10:
                continue
            face = [add(p) for p in triangle]
            if len(set(face)) != 3:
                continue
            top.append(face)
            source_faces.append(int(source_index))
    if not top or bottom_z >= min(p[2] for p in points):
        raise ValueError('Need a top surface and a strictly lower sealing bottom')
    counts = Counter(tuple(sorted((a, b))) for f in top for a, b in zip(f, f[1:]+f[:1]))
    if max(counts.values()) > 2:
        raise ValueError('Non-manifold source patch')
    boundary = [(a, b) for f in top for a, b in zip(f, f[1:]+f[:1])
                if counts[tuple(sorted((a, b)))] == 1]
    if not boundary:
        raise ValueError('Missing patch boundary')
    for a, b in boundary:
        if not any(abs(points[a][axis]-sign*half_size[axis]) < 1e-8 and
                   abs(points[b][axis]-sign*half_size[axis]) < 1e-8
                   for axis in (0, 1) for sign in (-1, 1)):
            raise ValueError('Source coverage has a hole or ends inside the patch')
    top_count = len(top)
    closed = list(top)
    bottom = {}
    for a, b in boundary:
        for index in (a, b):
            if index not in bottom:
                p = np.array(points[index], copy=True)
                p[2] = bottom_z
                bottom[index] = add(p)
        aa, bb = bottom[a], bottom[b]
        closed.extend(([a, aa, bb], [a, bb, b]))
    centre = add(np.array([0., 0., bottom_z]))
    for a, b in boundary:
        closed.append([centre, bottom[b], bottom[a]])
    counts = Counter(tuple(sorted((a, b))) for f in closed for a, b in zip(f, f[1:]+f[:1]))
    directions = Counter((a, b) for f in closed for a, b in zip(f, f[1:]+f[:1]))
    if set(counts.values()) != {2} or any(directions[(b, a)] != n for (a, b), n in directions.items()):
        raise ValueError('Sealed collision solid is not a consistently wound manifold')
    return np.array(points), np.array(closed, dtype=np.int32), top_count, np.array(source_faces, dtype=np.int32)


def bilinear(array, x, y, grid):
    col = (np.asarray(x)-grid['origin_x_m'])/grid['dx_m']
    row = (np.asarray(y)-grid['origin_y_m'])/grid['dy_m']
    i, j = np.floor(col).astype(int), np.floor(row).astype(int)
    if np.any(i < 0) or np.any(j < 0) or np.any(i+1 >= array.shape[1]) or np.any(j+1 >= array.shape[0]):
        raise ValueError('Coupling query outside source field; no clamp fallback')
    a, b = col-i, row-j
    return ((1-b)*((1-a)*array[j, i]+a*array[j, i+1]) +
            b*((1-a)*array[j+1, i]+a*array[j+1, i+1]))


def boundary_profiles(fields, grid, centre, size, interval, sampler, downstream, left):
    size = positive_xy(size, 'Fluid domain')
    centre = np.asarray(centre, dtype=float)
    if centre.shape != (2,) or not np.isfinite(centre).all():
        raise ValueError('Finite station/lateral centre required')
    interval=positive_xy(interval,'Boundary interval')
    counts = np.rint(size/interval).astype(int)
    if (counts < 1).any() or not np.allclose(counts*interval, size, rtol=0, atol=1e-9):
        raise ValueError('Whole boundary cells required')
    h, u, v, bed = (fields[k] for k in ('h', 'u', 'v', 'bed'))
    profiles = []
    for name, normal in (('upstream', (-1, 0)), ('downstream', (1, 0)),
                         ('river_right', (0, -1)), ('river_left', (0, 1))):
        normal = np.array(normal)
        tangent_axis = 1 if normal[0] else 0
        count = counts[tangent_axis]
        face_interval=interval[tangent_axis]
        along = (np.arange(count)+.5)*face_interval-size[tangent_axis]/2
        local = (np.column_stack((np.full(count, normal[0]*size[0]/2), along)) if normal[0]
                 else np.column_stack((along, np.full(count, normal[1]*size[1]/2))))
        sl = local + centre
        stage = bilinear(bed+h, sl[:, 0], sl[:, 1], grid)
        source_depth = bilinear(h, sl[:, 0], sl[:, 1], grid)
        # Interpolate momentum, not velocity, to retain the coarse field's
        # normal discharge. Fine bed samples do not create a new solved flow.
        momentum = np.column_stack([bilinear(h*u, sl[:, 0], sl[:, 1], grid),
                                    bilinear(h*v, sl[:, 0], sl[:, 1], grid)])
        en = sl[:, :1]*downstream + sl[:, 1:]*left
        exact_bed = sampler.sample(en[:, 0], en[:, 1])
        depth = np.maximum(stage-exact_bed, 0)
        flux = momentum @ normal * face_interval
        conflicts = (depth < .02) & (np.abs(flux) > 1e-4)
        rows = []
        for i in range(count):
            rows.append({'station_lateral_m': sl[i].tolist(), 'east_north_m': en[i].tolist(),
                         'bed_relative_datum_m': float(exact_bed[i]),
                         'stage_relative_datum_m': float(stage[i]),
                         'source_depth_m': float(source_depth[i]), 'resolved_depth_m': float(depth[i]),
                         'momentum_m2_per_s': momentum[i].tolist(),
                         'outward_discharge_m3_per_s': float(flux[i]),
                         'dry_flux_conflict': bool(conflicts[i])})
        profiles.append({'face': name, 'outward_normal_station_lateral': normal.tolist(),
                         'sample_width_m': float(face_interval),
                         'inflow_m3_per_s': float(-np.minimum(flux, 0).sum()),
                         'outflow_m3_per_s': float(np.maximum(flux, 0).sum()),
                         'dry_flux_conflicts': int(conflicts.sum()), 'samples': rows})
    return profiles


def apply_native_boundary_flux(profiles, audit, expected_bounds):
    """Use native face discharge, apportioned only to its own wet subfaces."""
    from build_south_fork_liquid_grid_boundary import remap_wet_flux
    if len(profiles)!=4:
        raise ValueError('Exactly four complete boundary profiles required')
    if not audit.get('passed') or not np.allclose(audit['local_station_lateral_face_bounds_m'],expected_bounds,rtol=0,atol=1e-9):
        raise ValueError('Native flux audit must match the complete requested domain')
    for profile, face in zip(profiles,('west','east','south','north')):
        rows=profile['samples'];interval=profile['sample_width_m']
        areas=np.array([r['resolved_depth_m'] for r in rows])*interval
        native=np.asarray(audit['face_discharge_m3_per_s'][face],dtype=float)
        # Zero tolerance: a nonzero native flux with no overlapping wet support
        # is an unresolved coupling problem, never permission to create water.
        inward=remap_wet_flux(native,areas)
        if abs(inward.sum()-native.sum())>1e-10:
            raise ValueError('Native-to-wet-subface remap changed total discharge')
        for row,q in zip(rows,inward):
            row['interpolated_outward_discharge_m3_per_s']=row['outward_discharge_m3_per_s']
            row['interpolated_dry_flux_conflict']=row['dry_flux_conflict']
            row['outward_discharge_m3_per_s']=float(-q)
            row['dry_flux_conflict']=bool(row['resolved_depth_m']<.02 and abs(q)>1e-4)
        profile.update(flux_authority='Native finite-volume face flux; wet overlap remap, no calibrated discharge claim',
            inflow_m3_per_s=float(np.maximum(inward,0).sum()),
            outflow_m3_per_s=float(-np.minimum(inward,0).sum()),
            dry_flux_conflicts=sum(r['dry_flux_conflict'] for r in rows),
            native_face_count=len(native),native_remap_error_m3_per_s=float(abs(inward.sum()-native.sum())))


def build(geometry_dir, hydraulic_dir, output, *, fluid_size=20., centre=(0.,0.), patch_margin=2., native_flux_audit=None):
    fluid_size = positive_xy(fluid_size, 'Fluid domain')
    centre = np.asarray(centre, dtype=float)
    if centre.shape != (2,) or not np.isfinite(centre).all():
        raise ValueError('Finite station/lateral centre required')
    if not np.isfinite(patch_margin) or patch_margin <= 0:
        raise ValueError('Positive collision margin required')
    from south_fork_registered_mesh import RegisteredMeshSampler
    geometry = json.loads((geometry_dir/'manifest.json').read_text())
    source_path = ROOT/geometry['mesh_path']
    if sha(source_path) != geometry['mesh_sha256']:
        raise ValueError('Source geometry changed')
    flow = json.loads((hydraulic_dir/'manifest.json').read_text())
    if flow['review']['source_geometry_sha256'] != geometry['mesh_sha256']:
        raise ValueError('Geometry and hydraulic identities disagree')
    coordinate = json.loads((hydraulic_dir/'coordinate_map.json').read_text())
    registration = json.loads((hydraulic_dir.parent/'registration.json').read_text())
    downstream, left = (np.array(registration[k]) for k in ('downstream_unit', 'left_unit'))
    rotation = np.column_stack((downstream, left))
    if not np.allclose(rotation.T@rotation, np.eye(2), atol=1e-9) or np.linalg.det(rotation) < 0:
        raise ValueError('Rigid right-handed source frame required')
    if coordinate['vertical_datum_m'] != geometry['vertical_origin_navd88_m']:
        raise ValueError('Vertical datum mismatch')
    mesh = np.load(source_path)
    sampler = RegisteredMeshSampler(mesh)
    world = sampler.xyz
    local = np.column_stack((world[:, :2]@rotation-centre, world[:, 2]))
    # Centre/extent select source coverage, never relocate captured terrain.
    # Local station is Cartesian, not independently surveyed river chainage.
    patch_half = fluid_size/2+patch_margin
    nearby = (np.abs(local[:, :2]) < patch_half+.5).all(axis=1)
    if not nearby.any():
        raise ValueError('Requested domain has no captured mesh support')
    floor = float(np.floor(local[nearby, 2].min())-.5)
    points, triangles, top_count, source_faces = closed_patch(local, sampler.faces, patch_half, floor-1)
    fields = {}
    for name, record in flow['bands'][0]['arrays'].items():
        path = hydraulic_dir/record['file']
        if sha(path) != record['sha256']:
            raise ValueError(f'Changed hydraulic array {name}')
        fields[name] = np.load(path)
    profiles = boundary_profiles(fields, flow['grid'], centre, fluid_size, .5,
                                 sampler, downstream, left)
    if native_flux_audit is not None:
        audit=json.loads(Path(native_flux_audit).read_text())
        if sha(Path(native_flux_audit).parent/'native_faces.npz')!=audit['faces_sha256']:
            raise ValueError('Native face-flux bytes changed since their conservation audit')
        if audit['source_geometry_sha256']!=geometry['mesh_sha256'] or audit['source_hydraulic_manifest_sha256']!=sha(hydraulic_dir/'manifest.json'):
            raise ValueError('Native flux provenance disagrees with source geometry/hydraulics')
        apply_native_boundary_flux(profiles,audit,np.stack((centre-fluid_size/2,centre+fluid_size/2)))
    # Independently compare every top triangle's centroid to the exact source
    # sampler; no resampled raster may silently replace the captured topology.
    centroids = points[triangles[:top_count]].mean(axis=1)
    en = (centroids[:, :2]+centre)@rotation.T
    errors = np.abs(sampler.sample(en[:, 0], en[:, 1])-centroids[:, 2])
    if errors.max() > 1e-7:
        raise ValueError('Clipped top differs from source triangle surface')
    output.mkdir(parents=True, exist_ok=False)
    points[:, 2] -= floor
    np.savez_compressed(output/'collision_solid.npz', vertices_local_m=points,
                        triangles=triangles, top_triangle_count=np.array(top_count),
                        top_source_face_indices=source_faces)
    report = {'schema': 'raftsim.south_fork_liquid_window.v1',
              'source_geometry_sha256': geometry['mesh_sha256'],
              'source_geometry_manifest': str((geometry_dir/'manifest.json').relative_to(ROOT)),
              'source_hydraulic_manifest_sha256': sha(hydraulic_dir/'manifest.json'),
              'source_hydraulic_directory': str(hydraulic_dir.relative_to(ROOT)),
              'solid_sha256': sha(output/'collision_solid.npz'),
              'local_origin_engine_cm': [*(centre@rotation.T*100).tolist(), floor*100],
              'local_to_engine_yaw_degrees': float(np.degrees(np.arctan2(downstream[1], downstream[0]))),
              'fluid_domain_local_bounds_m': [[*(-fluid_size/2).tolist(), 0.], [*(fluid_size/2).tolist(), 8.]],
              'terrain_patch_half_extent_m': float(patch_half[0]) if patch_half[0]==patch_half[1] else patch_half.tolist(),
              'physical_extent_xy_m': fluid_size.tolist(),
              'centre_station_lateral_m': centre.tolist(),
              'top_triangles': top_count, 'closed_triangles': len(triangles),
              'top_source_max_error_m': float(errors.max()),
              'captured_rock_returns_in_patch': int(((mesh['authority'].ravel() == 3) &
                  (np.abs(local[:, :2]) < patch_half).all(axis=1)).sum()),
              'captured_rock_returns_in_physical_domain': int(((mesh['authority'].ravel() == 3) &
                  (np.abs(local[:, :2]) <= fluid_size/2).all(axis=1)).sum()),
              'original_topology_preserved_between_clipped_edges': True,
              'side_and_bottom_authority': 'Artificial signed-distance closure outside the fluid domain; not surveyed',
              'submerged_bed_authority': geometry['submerged_bed_authority'],
              'registered_rapid_identity_verified': False,
              'boundary_profiles': profiles,
              'total_inflow_m3_per_s': sum(p['inflow_m3_per_s'] for p in profiles),
              'total_outflow_m3_per_s': sum(p['outflow_m3_per_s'] for p in profiles),
              'dry_flux_conflicts': sum(p['dry_flux_conflicts'] for p in profiles),
              'boundary_handoff_ready': not any(p['dry_flux_conflicts'] for p in profiles),
              'engine_collision_verified': False, 'engine_fluid_coupled': False,
              'production_promoted': False}
    if native_flux_audit is not None:
        report['native_flux_audit_sha256']=sha(Path(native_flux_audit))
        report['native_flux_audit_path']=str(Path(native_flux_audit).resolve().relative_to(ROOT))
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--geometry-dir', type=Path, required=True)
    parser.add_argument('--hydraulic-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fluid-size', type=float, nargs=2, default=(20.,20.), metavar=('LENGTH','WIDTH'))
    parser.add_argument('--centre', type=float, nargs=2, default=(0.,0.), metavar=('STATION','LATERAL'))
    parser.add_argument('--patch-margin', type=float, default=2.)
    parser.add_argument('--native-flux-audit',type=Path)
    args = parser.parse_args()
    result = build(args.geometry_dir.resolve(), args.hydraulic_dir.resolve(), args.output.resolve(),
                   fluid_size=args.fluid_size, centre=args.centre, patch_margin=args.patch_margin,
                   native_flux_audit=args.native_flux_audit)
    print(json.dumps({k: v for k, v in result.items() if k != 'boundary_profiles'}, indent=2))
