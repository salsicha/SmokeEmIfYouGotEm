"""Validate the full captured-XY candidate before any engine replacement."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tmp/south-fork-geospatial-deps'))
import numpy as np
from south_fork_geometry_source import geometry_identity, load_registered_mesh
from south_fork_mesh_sampling import grid_triangles, sample_triangles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, path, sha, registered = geometry_identity(args.geometry_dir/'manifest.json', ROOT)
    if not registered: raise ValueError('Registered mesh required')
    data, sampler = load_registered_mesh(path)
    parent = ROOT/source['parent_mesh_path']
    if hashlib.sha256(parent.read_bytes()).hexdigest() != source['parent_mesh_sha256']:
        raise ValueError('Parent mesh changed')
    with np.load(parent) as packed:
        old = {k: packed[k].copy() for k in packed.files}
    nonrock = old['authority'] != 3
    assert np.array_equal(data['authority'], old['authority'])
    assert np.array_equal(data['z_m'], old['z_m'])
    for k in ('east_m','north_m','z_m'):
        assert np.array_equal(data[k][nonrock], old[k][nonrock])
    vertex_error = float(np.max(abs(sampler.sample(data['east_m'],data['north_m'])-data['z_m'])))
    max_face_error = 0.
    # Every triangle, not just a few easy planar fixtures; use asymmetric
    # barycentric points as well as centroids and shared edges.
    for start in range(0,len(sampler.faces),50000):
        xyz = sampler.xyz[sampler.faces[start:start+50000]]
        for weights in ([1/3]*3,[.07,.32,.61],[0,.5,.5]):
            points = np.einsum('tij,i->tj',xyz,weights)
            error = np.max(abs(sampler.sample(points[:,0],points[:,1])-points[:,2]))
            max_face_error = max(max_face_error,float(error))
    if max(vertex_error,max_face_error) > 1e-7:
        raise ValueError('Exact triangle interpolation failed')
    # Fixed 1m hydraulic cell centres, with the existing rigid rotation.
    x,y = np.meshgrid(np.arange(-135,136.),np.arange(-80,81.))
    direction = np.array([-.93,.36756]);direction /= np.linalg.norm(direction)
    left = np.array([-direction[1],direction[0]])
    east,north = direction[0]*x+left[0]*y,direction[1]*x+left[1]*y
    new_bed = sampler.sample(east,north)
    old_bed = sample_triangles(old['z_m'],(old['north_m'][0,0]-north)/.5,(east-old['east_m'][0,0])/.5)
    delta = new_bed-old_bed
    changed_faces=np.flatnonzero(np.any(sampler.faces != grid_triangles(*data['z_m'].shape),axis=1))
    probe_xyz=sampler.xyz[sampler.faces[changed_faces]].mean(axis=1)
    report = dict(schema='raftsim.registered_mesh_sampling_audit.v1',source_mesh_sha256=sha,
        vertices=len(sampler.xyz),triangles=len(sampler.faces),
        maximum_vertex_sampling_error_m=vertex_error,maximum_triangle_sampling_error_m=max_face_error,
        all_recorded_heights_unchanged=True,all_non_rock_vertices_unchanged=True,
        changed_triangle_count=int(len(changed_faces)),
        changed_diagonal_interior_collision_probes_cm=(probe_xyz*100).tolist(),
        hydraulic_bed_change_1m=dict(changed_cell_count=int(np.count_nonzero(abs(delta)>1e-7)),
            minimum_m=float(delta.min()),maximum_m=float(delta.max()),
            p95_absolute_m=float(np.percentile(abs(delta),95))),
        sampling_passed=True,hydraulic_validation_passed=False,engine_integrated=False,
        visual_acceptance=False,production_promoted=False)
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__': main()
