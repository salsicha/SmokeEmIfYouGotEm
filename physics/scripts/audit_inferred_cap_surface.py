"""Reject unsupported claims about a fitted cap using retained player-view rays.

This is a source-space audit, not a new native capture or collision test.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from build_troublemaker_dem_rock_cap import ROOT
from compare_last_return_cap import stats
from south_fork_rock_union import sha


def compare(old, new, probes):
    for original, fitted in (
        ('vertices_m', 'original_source_vertices_m'),
        ('triangles', 'triangles'),
        ('original_return_index', 'original_return_index'),
        ('original_classification', 'original_classification'),
        ('boundary_edges', 'boundary_edges'),
        ('solid_triangles', 'solid_triangles'),
        ('solid_face_kind', 'solid_face_kind'),
    ):
        if not np.array_equal(old[original], new[fitted]):
            raise ValueError('Original source/topology changed: ' + original)
    before, after = old['vertices_m'], new['surface_vertices_m']
    if not np.array_equal(before[:, :2], after[:, :2]):
        raise ValueError('Footprint moved')
    changed = np.flatnonzero(np.any(before != after, axis=1))
    expected_authority = np.zeros(len(before), np.uint8)
    expected_authority[changed] = 1
    if not np.array_equal(expected_authority, new['vertex_authority']):
        raise ValueError('Fitted authority does not match changed XYZ')
    if not np.array_equal(before[new['protected_vertices']], after[new['protected_vertices']]):
        raise ValueError('Protected vertices changed')
    retained = []
    for probe in probes:
        hit = probe['source_hit']
        if hit['source'] != 'cap':
            continue
        face = hit['source_triangle']
        indices = old['solid_triangles'][face]
        if not np.array_equal(indices, hit['source_vertices']):
            raise ValueError('Retained ray does not identify this source triangle')
        same = np.array_equal(old['solid_vertices_m'][indices], new['solid_vertices_m'][indices])
        retained.append(dict(pixel=probe['pixel'], source_triangle=face,
            exact_triangle_xyz_unchanged=bool(same)))
    if not retained:
        raise ValueError('No retained cap rays')
    return dict(changed_vertex_ids=changed.tolist(),
        source_archive_and_topology_exact=True, footprint_exact=True,
        authority_matches_changes=True, retained_target_triangles=retained,
        all_retained_target_triangles_unchanged=all(r['exact_triangle_xyz_unchanged'] for r in retained),
        original=stats(old)[0],
        inferred=stats(dict(vertices_m=after, triangles=new['triangles']))[0])


def run(parent, candidate, rays_path, output):
    if output.exists():
        raise ValueError('Fresh report required')
    baseline = json.loads(parent.read_text())
    interpretation = json.loads(candidate.read_text())
    rays = json.loads(rays_path.read_text())
    if interpretation['schema'] != 'raftsim.interpreted_cap_interior_surface.v1':
        raise ValueError('Explicit interpreted surface required')
    old_path, new_path = ROOT / baseline['cap_path'], ROOT / interpretation['surface_path']
    identities = (
        (parent, interpretation['parent_cap_manifest_sha256']),
        (old_path, baseline['cap_sha256']),
        (old_path, rays['source_identities']['cap']['sha256']),
        (new_path, interpretation['surface_sha256']),
        (ROOT / rays['view_path'], rays['view_sha256']),
    )
    if not rays['all_probes_match'] or any(sha(path) != digest for path, digest in identities):
        raise ValueError('Source/view identity changed or retained native audit failed')
    with np.load(old_path, allow_pickle=False) as data:
        old = {k: data[k] for k in data.files}
    with np.load(new_path, allow_pickle=False) as data:
        new = {k: data[k] for k in data.files}
    report = dict(schema='raftsim.inferred_cap_surface_audit.v1',
        parent_manifest_sha256=sha(parent), candidate_manifest_sha256=sha(candidate),
        retained_rays_sha256=sha(rays_path), retained_view_sha256=rays['view_sha256'],
        **compare(old, new, rays['probes']),
        normal_play_changed=False, new_native_capture=False, hydraulics_recooked=False,
        visual_or_physical_accepted=False,
        limits='Unchanged target triangles disqualify an outlier fit as a repair for the diagnosed spikes. Lower steep area alone is not acceptance. Any other silhouette/occlusion change requires fresh engine review.')
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('parent', 'candidate', 'rays', 'output'):
        parser.add_argument('--' + flag, required=True, type=Path)
    args = parser.parse_args()
    run(args.parent, args.candidate, args.rays, args.output)
