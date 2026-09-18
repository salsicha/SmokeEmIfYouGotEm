"""Trace actual game terrain rays to immutable reconstruction source triangles.

This identifies source authority, not GPU visibility, rock classification,
survey accuracy, or permission to change geometry. Engine face indices are
reported but never assumed to share the archived source triangle ordering.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_carrier_camera_rays import nearest_triangle

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
ARCHIVE = BASE/'full_reach/source_matched_20260917'
TRANSLATION_CM = np.array([-543186.6369777592, -360044.75875617936, 0.])
REFLECTION = np.array([1., -1., 1.])
ORIGIN = np.array([683805.1336302214, 4296673.447587562, 220.])
IDENTITIES = {
    'ground': (ARCHIVE/'registered_mesh_source.npz',
               '8edf8a7fbfb675a22ac6736db600a3300f018f1c9037b1c0674bc1c376cfcca7'),
    'cap': (ARCHIVE/'original_return_rock_cap.npz',
            '78f77b67c64dc98094522ad2a8362edd0bfeab422816c90dc668e2cc5dd2baeb'),
    'returns': (BASE/'troublemaker/classified_lidar_returns.npz',
                '7f0a5d903a3914c830916390820cbf99260d7cb2f2cf667c57f2a1faa1c47cfe'),
}
ACTORS = {'ground': 'StaticMeshActor_UAID_04421A89ABE5ED0003_2136936984',
          'cap': 'StaticMeshActor_UAID_04421A89ABE5930203_1558143815'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def resolve_ray(record, sources, translation_cm, reflection):
    """Find the closest source triangle across BOTH physical solids in metres."""
    origin = np.asarray(record['ray_origin_cm'], float)
    direction = np.asarray(record['ray_direction'], float)
    translation_cm, reflection = np.asarray(translation_cm), np.asarray(reflection)
    if any(a.shape != (3,) or not np.isfinite(a).all()
           for a in (origin, direction, translation_cm, reflection)):
        raise ValueError('Finite three-dimensional transform and ray required')
    if not np.all(np.isin(reflection, [-1., 1.])) or not np.isclose(
            np.linalg.norm(direction), 1., rtol=0, atol=1e-8):
        raise ValueError('Unit ray and unit-axis reflection required')
    local_origin = (origin-translation_cm)*reflection*.01
    local_direction = direction*reflection
    hits = []
    for name, (xyz, faces) in sources.items():
        hit = nearest_triangle(local_origin, local_direction, xyz[faces])
        if hit is not None and hit[1] <= 1000.:
            index, distance, weights = hit
            point = weights @ xyz[faces[index]]
            hits.append((distance, name, index, point, weights))
    if not hits:
        return None
    distance, name, index, point, weights = min(hits, key=lambda h: h[0])
    xyz, faces = sources[name]
    triangle = xyz[faces[index]]
    normal = np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0])
    normal /= np.linalg.norm(normal)
    world_cm = point*reflection*100+translation_cm
    return dict(source=name, source_triangle=index, source_vertices=faces[index].tolist(),
                source_xyz_m=triangle.tolist(), local_hit_m=point.tolist(),
                world_hit_cm=world_cm.tolist(), distance_m=distance,
                barycentric=weights.tolist(),
                slope_degrees=float(np.degrees(np.arccos(np.clip(abs(normal[2]), 0, 1)))))


def source_identities(ground_source=None, ground_sha256=None):
    identities = dict(IDENTITIES)
    if (ground_source is None) != (ground_sha256 is None):
        raise ValueError('Candidate ground path and immutable SHA256 must be paired')
    if ground_source is not None:
        path = Path(ground_source).resolve()
        if not path.is_relative_to(ROOT/'tmp') or len(ground_sha256) != 64 or any(
                c not in '0123456789abcdef' for c in ground_sha256):
            raise ValueError('Project-local candidate and lowercase SHA256 required')
        identities['ground'] = (path, ground_sha256)
    if any(sha(path) != expected for path, expected in identities.values()):
        raise ValueError('Archived or candidate source identity changed')
    return identities


def run(view_path, output, ground_source=None, ground_sha256=None):
    if output.exists():
        raise ValueError('Fresh output required; preserve previous evidence')
    view = json.loads(view_path.read_text(encoding='utf-8-sig'))
    if view.get('schema') != 'raftsim.carrier_view.v1':
        raise ValueError('Actual carrier-view terrain rays required')
    paths = source_identities(ground_source, ground_sha256)
    identities = {name: dict(path=str(path.relative_to(ROOT)), sha256=expected)
                  for name, (path, expected) in paths.items()}
    data = {}
    for name, (path, _) in paths.items():
        with np.load(path, allow_pickle=False) as archive:
            data[name] = {key: archive[key] for key in archive.files}
    ground, cap, returns = (data[name] for name in ('ground', 'cap', 'returns'))
    ground_xyz = np.column_stack([ground[k].ravel() for k in ('east_m', 'north_m', 'z_m')])
    sources = {'ground': (ground_xyz, ground['triangles']),
               'cap': (cap['solid_vertices_m'], cap['solid_triangles'])}
    authority = ground['authority'].ravel()
    return_ids = np.full(len(ground_xyz), -1, dtype=int)
    return_ids[authority == 3] = ground['rock_source_return_index']
    points = np.column_stack([returns[k] for k in ('utm_easting_m', 'utm_northing_m', 'navd88_m')])-ORIGIN
    rows = []
    for record in view['terrain_ray_probes']:
        hit = resolve_ray(record, sources, TRANSLATION_CM, REFLECTION)
        row = dict(pixel=record['pixel'], engine=record, source_hit=hit, matches=False)
        if hit is not None and record['hit']:
            error = float(np.linalg.norm(np.array(hit['world_hit_cm'])-record['ground_world_cm']))
            row.update(collision_error_cm=error,
                       matches=error <= .1 and record['actor'].endswith('.'+ACTORS[hit['source']]))
            ids = np.array(hit['source_vertices'])
            if hit['source'] == 'ground':
                hit['vertex_authority'] = authority[ids].tolist()
                hit['original_return_indices'] = return_ids[ids].tolist()
                captured = ids[authority[ids] == 3]
                hit['captured_xy_max_error_m'] = float(np.max(abs(
                    ground_xyz[captured, :2]-points[return_ids[captured], :2]))) if len(captured) else None
                # The existing registered ground stores height in float32;
                # retain that documented precision, not a new equality gate.
                hit['captured_z_max_error_m'] = float(np.max(abs(
                    ground_xyz[captured, 2]-points[return_ids[captured], 2]))) if len(captured) else None
            else:
                hit['solid_face_kind'] = int(cap['solid_face_kind'][hit['source_triangle']])
        elif hit is None and record['hit'] is False:
            row['matches'] = True
        rows.append(row)
    report = dict(schema='raftsim.terrain_camera_source_audit.v1',
                  view_path=str(view_path), view_sha256=sha(view_path),
                  game_frame=view['game_frame'], world_seconds=view['world_seconds'],
                  source_identities=identities, translation_cm=TRANSLATION_CM.tolist(),
                  reflection=REFLECTION.tolist(), collision_tolerance_cm=.1,
                  all_probes_match=bool(rows) and all(row['matches'] for row in rows),
                  probes=rows, geometry_modified=False, visual_or_physical_accepted=False,
                  limits='Game-thread complex terrain rays, not GPU visibility; source authority is not classification certainty. No source triangle order assumed from engine face indices.')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(all_probes_match=report['all_probes_match'], probes=[
        dict(pixel=r['pixel'], source=r['source_hit']['source'] if r['source_hit'] else None,
             authority=r['source_hit'].get('vertex_authority') if r['source_hit'] else None,
             error_cm=r.get('collision_error_cm')) for r in rows]), indent=2))
    if not report['all_probes_match']:
        raise ValueError('Source/collision mismatch retained in report')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('view', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ground-source', type=Path)
    parser.add_argument('--ground-sha256')
    args = parser.parse_args()
    run(args.view, args.output, args.ground_source, args.ground_sha256)
