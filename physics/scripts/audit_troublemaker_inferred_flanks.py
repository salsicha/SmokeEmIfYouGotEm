"""Verify the proposed shared flank geometry before any playable replacement."""
import hashlib
import json
from pathlib import Path
import numpy as np
from south_fork_geometry_source import load_registered_mesh
from reconstruct_troublemaker_rock_flanks import ROOT, PARENT

NEW = ROOT/'tmp/troublemaker-inferred-rock-flanks-20260912'


def main():
    manifest = json.loads((NEW/'manifest.json').read_text())
    path = NEW/'registered_mesh_source.npz'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['mesh_sha256']
    old, before = load_registered_mesh(PARENT/'registered_mesh_source.npz')
    mesh, after = load_registered_mesh(path)
    changed = mesh['authority'] != old['authority']
    assert changed.sum() == manifest['flank_reconstruction']['changed_vertices']
    assert np.all(old['authority'][changed] == 2) and np.all(mesh['authority'][changed] == 5)
    assert np.array_equal(mesh['triangles'], old['triangles'])
    for key in ('east_m', 'north_m'):
        assert np.array_equal(mesh[key], old[key])
    assert np.array_equal(mesh['z_m'][~changed], old['z_m'][~changed])
    assert np.all(mesh['z_m'][changed] >= old['z_m'][changed])
    maximum = 0.
    for start in range(0, len(after.faces), 50000):
        vertices = after.xyz[after.faces[start:start+50000]]
        for weights in ([1/3]*3, [.07,.32,.61], [0,.5,.5]):
            p = np.einsum('tij,i->tj', vertices, weights)
            maximum = max(maximum, float(np.max(abs(after.sample(p[:,0], p[:,1])-p[:,2]))))
    assert maximum < 1e-7
    affected = np.any(changed.ravel()[after.faces], axis=1)

    def face_statistics(sampler):
        p = sampler.xyz[sampler.faces[affected]]
        cross = np.cross(p[:,1]-p[:,0], p[:,2]-p[:,0])
        magnitude = np.linalg.norm(cross, axis=1)
        steep = abs(cross[:,2]) < .5*magnitude
        return dict(steeper_than_60_degree_faces=int(steep.sum()),
            steep_area_m2=float(magnitude[steep].sum()*.5),
            total_area_m2=float(magnitude.sum()*.5))

    probes = np.concatenate((after.xyz[changed.ravel()], after.xyz[after.faces[affected]].mean(axis=1)))
    s, l = np.meshgrid(np.arange(-135,136.), np.arange(-80,81.))
    direction = np.array([-.93,.36756]); direction /= np.linalg.norm(direction)
    left = np.array([-direction[1],direction[0]])
    east, north = direction[0]*s+left[0]*l, direction[1]*s+left[1]*l
    delta = after.sample(east,north)-before.sample(east,north)
    report = dict(source_geometry_sha256=manifest['mesh_sha256'],
        parent_geometry_sha256=manifest['parent_mesh_sha256'],
        maximum_triangle_sampling_error_m=maximum,
        changed_vertices=int(changed.sum()), changed_face_count=int(affected.sum()),
        changed_hydraulic_cells=int((abs(delta)>1e-7).sum()),
        hydraulic_bed_delta_range_m=[float(delta.min()),float(delta.max())],
        before_affected_faces=face_statistics(before), after_affected_faces=face_statistics(after),
        original_measured_ground_and_rock_unchanged=True,
        registered_xy_and_topology_unchanged=True,
        inferred_band_prior_m=manifest['flank_reconstruction']['support_band_prior_m'],
        exact_changed_triangle_probes_cm=(probes*[100,-100,100]).tolist())
    (NEW/'sampling-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'exact_changed_triangle_probes_cm'}, indent=2))
    return manifest, after.sample(east,north), report


if __name__ == '__main__':
    main()
