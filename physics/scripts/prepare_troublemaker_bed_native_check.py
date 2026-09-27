"""Prepare exact ground-only native replacement checks against installed terrain.

This does not waive rock-union, runtime-bed, hydraulic or playable validation.
It compares to the installed ablated mesh, not its older pre-ablation ancestor.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from package_runtime_bundle import sha
from south_fork_terrain_revision import RegisteredTerrainRevision

ROOT = Path(__file__).resolve().parents[2]
GROUND = '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SourceMatched20260917/SM_SourceMatchedGround'


def delta_probes(original, revised, origin, datum):
    revision = RegisteredTerrainRevision(original, revised, origin, datum)
    old, new = revision.original, revision.revised
    changed = np.flatnonzero(np.any(old.xyz != new.xyz, axis=1))
    faces = np.flatnonzero(np.any(np.isin(new.faces, changed), axis=1))
    return dict(
        triangle_count=len(new.faces),
        terrain_vertex_changes_cm=[dict(source_vertex_index=int(i),
            before=(old.xyz[i]*100).tolist(), after=(new.xyz[i]*100).tolist()) for i in changed],
        changed_triangle_probe_count=len(faces),
        # Local Unreal mesh is east/north/up. Actor reflection maps north to -Y.
        ground_triangle_centroids_cm=(new.xyz[new.faces[faces]].mean(axis=1)*100).tolist(),
        changed_triangle_indices=faces.tolist())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline-mesh', type=Path, required=True)
    p.add_argument('--baseline-manifest', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--export', type=Path, required=True)
    p.add_argument('--installation', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp receipt required')
    deps = {}

    def add(path):
        path = path.resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('Project dependency required')
        deps[path.relative_to(ROOT).as_posix()] = sha(path)
        return path

    baseline = json.loads(add(args.baseline_manifest).read_text())
    candidate = json.loads(add(args.candidate/'manifest.json').read_text())
    export = json.loads(add(args.export/'manifest.json').read_text())
    installed = json.loads(add(args.installation).read_text())
    mesh_path = add(ROOT/candidate['mesh_path'])
    baseline_path = add(args.baseline_mesh)
    old_hash, new_hash = sha(baseline_path), sha(mesh_path)
    if (old_hash != baseline['mesh_sha256'] or new_hash != candidate['mesh_sha256'] or
            candidate['conveyance_revision']['parent_mesh_sha256'] != old_hash or
            candidate['conveyance_revision']['parent_manifest_sha256'] != sha(args.baseline_manifest)):
        raise ValueError('Immediate parent/candidate identity mismatch')
    if any(candidate[k] != baseline[k] for k in ('origin_utm_m', 'vertical_origin_navd88_m')):
        raise ValueError('Source frame changed')
    if (export['source_geometry_sha256'] != new_hash or
            export['source_bed_sampling'] != 'registered_triangles' or
            sha(add(ROOT/export['fbx'])) != export['fbx_sha256']):
        raise ValueError('Export differs from hydraulic mesh')
    row, = [r for r in installed['meshes'] if r['asset'] == GROUND]
    package = add(ROOT/'unreal/Content'/(GROUND[6:]+'.uasset'))
    if sha(package) != row['sha256']:
        raise ValueError('Installed baseline package changed')
    with np.load(baseline_path, allow_pickle=False) as a, np.load(mesh_path, allow_pickle=False) as b:
        probes = delta_probes({k:a[k] for k in a.files}, {k:b[k] for k in b.files},
                              baseline['origin_utm_m'], baseline['vertical_origin_navd88_m'])
    if probes['triangle_count'] != export['triangle_count'] or probes['triangle_count'] != row['native_source']['triangle_count']:
        raise ValueError('Source/native/export triangle counts differ')
    result = dict(schema='raftsim.troublemaker_bed_native_preflight.v1',
        baseline_asset=GROUND, baseline_package_sha256=row['sha256'],
        baseline_native_source=row['native_source'],
        candidate_asset='/Game/RaftSim/Environment/GeneratedLocalReview/TroublemakerConveyance20260927/SM_Ground',
        export_directory=args.export.resolve().relative_to(ROOT).as_posix(),
        candidate_mesh_sha256=new_hash, dependencies=deps, **probes,
        normal_map_integrated=False, rock_union_verified=False, hydraulic_validation_passed=False)
    with out.open('x', encoding='utf-8') as f:
        json.dump(result, f, separators=(',', ':'), allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(output=str(out), sha256=sha(out), triangles=probes['triangle_count'],
        changed_vertices=len(probes['terrain_vertex_changes_cm']), changed_triangles=probes['changed_triangle_probe_count'])))


if __name__ == '__main__':
    main()
