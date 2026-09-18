"""Independently verify candidate source preservation and exact mesh sampling."""
import argparse
import json
from pathlib import Path

import numpy as np
from prepare_troublemaker_control_ablation import sha
from south_fork_registered_mesh import RegisteredMeshSampler

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'


def run(candidate, output, view_path=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    if output.exists():
        raise ValueError('Fresh output required')
    manifest = json.loads((candidate/'manifest.json').read_text())
    paths = dict(parent=BASE/'full_reach/source_matched_20260917/registered_mesh_source.npz',
                 candidate=candidate/'registered_mesh_source.npz',
                 returns=BASE/'troublemaker/classified_lidar_returns.npz')
    expected = [manifest[k] for k in ('parent_mesh_sha256', 'mesh_sha256', 'original_returns_sha256')]
    if any(sha(p) != digest for p, digest in zip(paths.values(), expected)):
        raise ValueError('Source identity changed')
    packed = {}
    for name, path in paths.items():
        with np.load(path, allow_pickle=False) as archive:
            packed[name] = {k: archive[k] for k in archive.files}
    old, new, returns = [packed[k] for k in paths]
    changed = (new['authority'] == 3) & (old['authority'] != 3)
    assert changed.any() and np.all(np.isin(old['authority'][changed], [2, 5]))
    modified_flanks = (new['z_m'] != old['z_m']) & ~changed
    assert not np.any(modified_flanks & ~np.isin(old['authority'], [2, 5]))
    assert np.all(new['authority'][modified_flanks] == 5)
    if modified_flanks.any():
        from scipy.spatial import cKDTree
        added_xy = np.column_stack([new[k][changed] for k in ('east_m', 'north_m')])
        flank_xy = np.column_stack([new[k][modified_flanks] for k in ('east_m', 'north_m')])
        distance, _ = cKDTree(added_xy).query(flank_xy)
        assert np.all(distance <= 2.)
    for key in ('east_m', 'north_m', 'z_m', 'source_surface_m'):
        editable = changed | (modified_flanks if key == 'z_m' else False)
        assert np.array_equal(new[key][~editable], old[key][~editable]), key
    source_grid = np.full(changed.shape, -1, dtype=int)
    source_grid[new['authority'] == 3] = new['rock_source_return_index']
    np.testing.assert_array_equal(source_grid[old['authority'] == 3], old['rock_source_return_index'])
    ids = source_grid[changed]
    np.testing.assert_array_equal(ids, manifest['source_ids'])
    origin = np.array([683805.1336302214, 4296673.447587562, 220.])
    points = np.column_stack([returns[k] for k in ('utm_easting_m', 'utm_northing_m', 'navd88_m')])-origin
    for j, key in enumerate(('east_m', 'north_m', 'z_m')):
        np.testing.assert_array_equal(new[key][changed], points[ids, j].astype(new[key].dtype))
    sampler = RegisteredMeshSampler(new)
    vertex_error = float(np.max(abs(sampler.sample(new['east_m'], new['north_m'])-new['z_m'])))
    face_error = 0.
    for start in range(0, len(sampler.faces), 50000):
        triangles = sampler.xyz[sampler.faces[start:start+50000]]
        for weights in ([1/3]*3, [.07, .32, .61], [0., .5, .5]):
            p = np.einsum('tij,i->tj', triangles, weights)
            face_error = max(face_error, float(np.max(abs(sampler.sample(p[:, 0], p[:, 1])-p[:, 2]))))
    assert max(vertex_error, face_error) <= 1e-7
    old_sampler = RegisteredMeshSampler(old)
    pose = None
    if view_path is not None:
        view = json.loads(view_path.read_text(encoding='utf-8-sig'))
        if view.get('schema') != 'raftsim.carrier_view.v1' or not view.get('terrain_ray_probes'):
            raise ValueError('Recorded terrain-ray view required')
        origin_cm = np.array([r['ray_origin_cm'] for r in view['terrain_ray_probes']])
        p = (origin_cm-[-543186.6369777592, -360044.75875617936, 0.])*[.01, -.01, .01]
        old_clearance = p[:, 2]-old_sampler.sample(p[:, 0], p[:, 1])
        new_clearance = p[:, 2]-sampler.sample(p[:, 0], p[:, 1])
        pose = dict(view_path=str(view_path), view_sha256=sha(view_path),
                    scope='Recorded near-plane ray origins, not hull collision or traversal.',
                    local_ray_origins_m=p.tolist(), installed_clearance_m=old_clearance.tolist(),
                    candidate_clearance_m=new_clearance.tolist(),
                    all_recorded_near_plane_origins_above_candidate=bool(np.all(new_clearance >= 0.)))
    region = (sampler.xyz[sampler.faces, :2].mean(axis=1) >= [0., -13.]).all(axis=1)
    region &= (sampler.xyz[sampler.faces, :2].mean(axis=1) <= [25., 5.]).all(axis=1)
    def steep_area(source):
        triangles = source.xyz[source.faces[region]]
        normal = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
        length = np.linalg.norm(normal, axis=1)
        return float((length/2)[abs(normal[:, 2]) < length*.5].sum())
    # Plot identical XY profiles, not unrelated moving-camera images.
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout='constrained')
    north = np.linspace(-13., 5., 1000)
    for ax, east in zip(axes, [6., 18.]):
        close = (abs(points[:, 0]-east) < .25) & (points[:, 1] >= -13) & (points[:, 1] <= 5)
        close &= np.isin(returns['classification'], [1, 2, 10])
        ax.scatter(points[close, 1], points[close, 2], s=10, color='black', alpha=.5, label='Original returns within +/-0.25m')
        ax.plot(north, old_sampler.sample(np.full_like(north, east), north), label='Installed source')
        ax.plot(north, sampler.sample(np.full_like(north, east), north), label='Isolated source candidate')
        ax.set(xlabel='North of source origin (m)', ylabel='Height above datum (m)', title=f'Section at east={east:g}m', ylim=(3, 13))
        ax.legend(fontsize=8)
    fig.suptitle('Original returns are not surveyed rock labels; unsampled connecting faces remain inferred')
    output.mkdir(parents=True)
    fig.savefig(output/'sections.png', dpi=150)
    plt.close(fig)
    classes, counts = np.unique(returns['classification'][ids], return_counts=True)
    report = dict(schema='raftsim.constriction_source_candidate_audit.v1',
                  parent_sha256=sha(paths['parent']), candidate_sha256=sha(paths['candidate']),
                  all_original_captured_xyz_preserved=True, additional_return_coordinates_verified=True,
                  additional_return_classifications={str(int(k)): int(v) for k, v in zip(classes, counts)},
                  inferred_changed_vertices=int(modified_flanks.sum()),
                  vertices=len(sampler.xyz), triangles=len(sampler.faces),
                  maximum_vertex_sampling_error_m=vertex_error, maximum_triangle_sampling_error_m=face_error,
                  sampling_tolerance_m=1e-7, sampling_passed=True,
                  steep_area_scope_centroid_bounds_m=[[0., -13.], [25., 5.]],
                  installed_steeper_than_60_degree_area_m2=steep_area(old_sampler),
                  candidate_steeper_than_60_degree_area_m2=steep_area(sampler),
                  recorded_pose_clearance=pose,
                  visual_accepted=False, hydraulic_accepted=False, engine_integrated=False,
                  limits='Source-coordinate and sampling checks only. Sharp inferred boundary faces remain; original classifications are unchanged, not certified as rock.')
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--view', type=Path)
    args = parser.parse_args()
    run(args.candidate, args.output, args.view)
