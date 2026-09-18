"""Exact native source hash and collision targets for the isolated candidate."""
import argparse
import json
from pathlib import Path

import numpy as np
from prepare_troublemaker_control_ablation import sha
from source_native_triangle_hash import triangle_hash
from south_fork_terrain_revision import load_revision

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'


def prepare(revision_path, export_dir, output):
    if output.exists() or not output.resolve().is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh local native proof required')
    cap = json.loads((BASE/'full_reach/source_matched_20260917/rock_cap_manifest.json').read_text())
    origin = cap['origin_utm_and_vertical_datum_m']
    revision = load_revision(revision_path, ROOT, ROOT/cap['source_mesh_path'], origin[:2], origin[2])
    with np.load(BASE/'full_reach/source_matched_20260917/registered_mesh_source.npz', allow_pickle=False) as data:
        old = np.column_stack([data[k].ravel() for k in ('east_m', 'north_m', 'z_m')])
        old_faces = data['triangles']
    new, faces = revision.revised.xyz, revision.revised.faces
    old_hash = triangle_hash(old*100, old_faces)
    # Reproduce an already observed native provider identity independently.
    if old_hash != 'f0d39b640592c1b2cbccf89c1ed07f01587f377de5b5d0db0bab9b254cf888c5':
        raise ValueError('Independent hash does not reproduce installed source')
    export_path = export_dir/'manifest.json'
    export = json.loads(export_path.read_text())
    if (export['source_geometry_sha256'] != revision.identity['revised_geometry_sha256']
            or export['triangle_count'] != len(faces) or sha(ROOT/export['fbx']) != export['fbx_sha256']):
        raise ValueError('Export and verified hydraulic source differ')
    changed = np.any(old != new, axis=1)
    affected = np.any(changed[faces], axis=1) | np.any(changed[old_faces], axis=1) | np.any(faces != old_faces, axis=1)
    points = [('changed_source_vertex', int(i), new[i]) for i in np.flatnonzero(changed)]
    points += [('affected_triangle_centroid', int(i), new[faces[i]].mean(axis=0)) for i in np.flatnonzero(affected)]
    report = dict(schema='raftsim.constriction_native_geometry.v1', revision=revision.identity,
                  export_directory=export_dir.relative_to(ROOT).as_posix(), export_manifest_sha256=sha(export_path),
                  expected_native_source_sha256=triangle_hash(new*100, faces),
                  installed_native_source_sha256=old_hash, triangle_count=len(faces),
                  changed_vertices_from_installed=int(changed.sum()), affected_triangles_from_installed=int(affected.sum()),
                  native_collision_tolerance_cm=.1,
                  probes=[dict(kind=k, source_index=i, world_position_cm=(p*[100, -100, 100]).tolist()) for k, i, p in points],
                  asset='/Game/RaftSim/Environment/GeneratedLocalReview/ConstrictionSource20260918/SM_SourceGround',
                  installed_asset='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SourceMatched20260917/SM_SourceMatchedGround',
                  game_integrated=False, physical_union_and_flow_verified=False)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('revision', 'probes')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('revision', type=Path)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.revision.resolve(), args.export.resolve(), args.output)
