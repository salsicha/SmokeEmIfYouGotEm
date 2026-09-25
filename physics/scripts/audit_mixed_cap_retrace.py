"""Retrace retained camera rays against a candidate; not new engine visibility."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'unreal/Scripts'))
from audit_terrain_camera_sources import resolve_ray, sha


def run(output):
    if output.exists():
        raise ValueError('Fresh output required')
    ray_path = ROOT / 'docs/reconstruction-review-2026-09-07/downstream-cap-provenance/source-rays.json'
    manifest_path = ROOT / 'tmp/troublemaker-mixed-support-candidate-20260925/rock_cap_manifest-v2.json'
    rays = json.loads(ray_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    ground_path = ROOT / rays['source_identities']['ground']['path']
    old_path = ROOT / rays['source_identities']['cap']['path']
    new_path = ROOT / manifest['cap_path']
    identities = [(ground_path, rays['source_identities']['ground']['sha256']),
                  (old_path, rays['source_identities']['cap']['sha256']),
                  (new_path, manifest['cap_sha256']),
                  (ROOT / rays['view_path'], rays['view_sha256'])]
    if not rays['all_probes_match'] or any(sha(p) != h for p, h in identities):
        raise ValueError('Retained source/view identity mismatch')
    with np.load(ground_path) as ground, np.load(old_path) as old, np.load(new_path) as new:
        sources = {'ground': (np.column_stack([ground[k].ravel() for k in ('east_m', 'north_m', 'z_m')]), ground['triangles'])}
        rows = []
        for probe in rays['probes']:
            original = probe.get('source_hit')
            if not original or original['source'] != 'cap':
                continue
            sources['cap'] = (old['solid_vertices_m'], old['solid_triangles'])
            before = resolve_ray(probe['engine'], sources, rays['translation_cm'], rays['reflection'])
            if before is None or before['source'] != 'cap' or before['source_triangle'] != original['source_triangle'] or not np.allclose(before['world_hit_cm'], original['world_hit_cm'], atol=1e-7, rtol=0):
                raise ValueError('Original source ray did not reproduce')
            sources['cap'] = (new['solid_vertices_m'], new['solid_triangles'])
            after = resolve_ray(probe['engine'], sources, rays['translation_cm'], rays['reflection'])
            rows.append(dict(pixel=probe['pixel'], before=before, after=after,
                hit_displacement_m=float(np.linalg.norm(np.array(after['local_hit_m'])-before['local_hit_m'])) if after else None))
    if not rows:
        raise ValueError('No diagnosed cap rays')
    if any(sha(p) != h for p, h in identities):
        raise ValueError('Source changed during audit')
    report = dict(schema='raftsim.mixed_cap_retrace.v1', source_rays_sha256=sha(ray_path),
        candidate_manifest_sha256=sha(manifest_path), identities={str(p.relative_to(ROOT)): h for p,h in identities},
        probes=rows, native_collision_verified=False, gpu_visibility_verified=False,
        playable_changed=False, repair_accepted=False,
        limits='Same retained candidate-ground geometry on both sides. This isolates cap changes in source space; it is not a normal-map or fresh native visibility test.')
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps([dict(pixel=r['pixel'], displacement_m=r['hit_displacement_m'], old_slope=r['before']['slope_degrees'], new_slope=r['after']['slope_degrees'] if r['after'] else None) for r in rows], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
