"""Verify reconstructed triangles and stage a matched normal-game delivery.

The prior playable files are retained byte-for-byte before replacement. Render
integration follows separately and must verify this exact geometry identity.
"""
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
from south_fork_geometry_source import load_registered_mesh
from audit_troublemaker_sparse_rock_returns import ROOT, SOURCE

NEW = ROOT/'tmp/troublemaker-sparse-rock-support-20260912'
RUN = ROOT/'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-sparse-rock-support-20260912'
DEST = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_flow'
BACKUP = ROOT/'tmp/troublemaker-playable-before-sparse-rock-20260912'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry_audit():
    manifest = json.loads((NEW/'manifest.json').read_text())
    mesh_path = NEW/'registered_mesh_source.npz'
    assert sha(mesh_path) == manifest['mesh_sha256']
    mesh, sampler = load_registered_mesh(mesh_path)
    original, old = load_registered_mesh(SOURCE/'registered_mesh_source.npz')
    changed = mesh['authority'] != original['authority']
    assert changed.sum() == 420
    for key in ('east_m', 'north_m', 'z_m', 'authority'):
        assert np.array_equal(mesh[key][~changed], original[key][~changed])
    assert np.all(original['authority'][changed] == 2)
    maximum = 0.
    for start in range(0, len(sampler.faces), 50000):
        vertices = sampler.xyz[sampler.faces[start:start+50000]]
        for weights in ([1/3]*3, [.07,.32,.61], [0,.5,.5]):
            p = np.einsum('tij,i->tj', vertices, weights)
            maximum = max(maximum, float(np.max(abs(sampler.sample(p[:,0], p[:,1])-p[:,2]))))
    assert maximum < 1e-7
    affected = np.any(changed.ravel()[sampler.faces], axis=1)
    affected |= np.any(sampler.faces != old.faces, axis=1)
    probes = np.concatenate((sampler.xyz[changed.ravel()], sampler.xyz[sampler.faces[affected]].mean(axis=1)))
    x, y = np.meshgrid(np.arange(-135, 136.), np.arange(-80, 81.))
    direction = np.array([-.93, .36756]); direction /= np.linalg.norm(direction)
    left = np.array([-direction[1], direction[0]])
    east, north = direction[0]*x+left[0]*y, direction[1]*x+left[1]*y
    bed = sampler.sample(east, north)
    delta = bed-old.sample(east, north)
    report = dict(source_geometry_sha256=manifest['mesh_sha256'], maximum_triangle_sampling_error_m=maximum,
        changed_vertices=int(changed.sum()), changed_hydraulic_cells=int((abs(delta) > 1e-7).sum()),
        hydraulic_bed_delta_range_m=[float(delta.min()), float(delta.max())],
        original_measured_ground_and_rock_unchanged=True, exact_changed_triangle_probes_cm=(probes*[100,-100,100]).tolist())
    (NEW/'sampling-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    return manifest, bed, report


def stage_delivery(geometry, bed, audit, run_dir, backup, flow_report, flux_report):
    """Stage an audited child revision, retaining the complete previous delivery."""
    source = run_dir/'engine_review'
    manifest = json.loads((source/'manifest.json').read_text())
    flow = json.loads(flow_report.read_text())
    flux = json.loads(flux_report.read_text())
    assert flow['mean_flow_screen_passed'] and flux['passed']
    assert flow['geometry_sha256'] == flux['source_geometry_sha256'] == geometry['mesh_sha256']
    assert manifest['review']['source_geometry_sha256'] == geometry['mesh_sha256']
    assert manifest['review']['source_bed_sampling'] == 'registered_triangles'
    assert all(f['passed'] for f in manifest['review']['saved_frame_sanity'])
    assert np.max(abs(bed-np.load(source/'median_runnable/bed.npy'))) < 1e-5
    old_delivery = json.loads((DEST/'delivery.json').read_text())
    assert old_delivery['source_geometry_sha256'] == geometry['parent_mesh_sha256']
    assert backup.resolve().is_relative_to(ROOT/'tmp') and not backup.exists()
    for name, digest in old_delivery['files'].items():
        assert sha(DEST/name) == digest
    backup.mkdir()
    shutil.copytree(DEST, backup/'playable_flow')
    files = {'manifest.json': source/'manifest.json', 'coordinate_map.json': DEST/'coordinate_map.json'}
    for band in manifest['bands']:
        for array in band['arrays'].values():
            assert sha(source/array['file']) == array['sha256']
            files[array['file']] = source/array['file']
    for name, path in files.items():
        if path != DEST/name:
            shutil.copy2(path, DEST/name)
    delivery = dict(old_delivery)
    delivery.update(source_fields=source.relative_to(ROOT).as_posix(), source_geometry_sha256=geometry['mesh_sha256'],
        files={name: sha(DEST/name) for name in files},
        parent_delivery_sha256=sha(backup/'playable_flow/delivery.json'),
        captured_coordinates_and_solver_arrays_unchanged=False,
        coordinate_map_unchanged=True, source_matched_flow_recooked=True)
    (DEST/'delivery.json').write_text(json.dumps(delivery, indent=2)+'\n')
    route_path = ROOT/'docs/reconstruction-review-2026-09-07/guided-route-playable.json'
    shutil.copy2(route_path, backup/'guided-route-playable.json')
    route = json.loads(route_path.read_text())
    route.update(source_geometry_sha256=geometry['mesh_sha256'], depth_sha256=manifest['bands'][0]['arrays']['h']['sha256'],
        parent_route_sha256=sha(backup/'guided-route-playable.json'),
        guidance_points_unchanged=True, revised_geometry_traversal_validated=False)
    route_path.write_text(json.dumps(route, indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k != 'exact_changed_triangle_probes_cm'}, indent=2))


def main():
    reviews = ROOT/'docs/reconstruction-review-2026-09-06'
    stage_delivery(*geometry_audit(), RUN, BACKUP,
        reviews/'troublemaker_survey_flow_1m-mixed-inlet-sparse-rock-support-20260912.json',
        reviews/'troublemaker_numerical_boundary_flux-sparse-rock-support-20260912.json')


if __name__ == '__main__':
    main()
