"""Track fixed diagnosed source faces through a reindexed mixed-survey cap.

Exact directed triangle retention is not new visibility or native collision.
"""
import json
from pathlib import Path
import numpy as np
from south_fork_rock_union import sha

ROOT=Path(__file__).resolve().parents[2]


def triangle_key(points):
    rows=tuple(tuple(float(x) for x in p) for p in points)
    if len(rows)!=3 or any(len(p)!=3 for p in rows) or not np.isfinite(rows).all():
        raise ValueError('Finite triangle required')
    return min(rows,rows[1:]+rows[:1],rows[2:]+rows[:2])


def main():
    rays_path=ROOT/'docs/reconstruction-review-2026-09-07/downstream-cap-provenance/source-rays.json'
    manifest_path=ROOT/'tmp/troublemaker-mixed-support-candidate-20260925/rock_cap_manifest-v2.json'
    output=ROOT/'tmp/mixed-cap-fixed-view-targets-20260925.json'
    assert not output.exists()
    rays=json.loads(rays_path.read_text());manifest=json.loads(manifest_path.read_text())
    old_path=ROOT/rays['source_identities']['cap']['path'];new_path=ROOT/manifest['cap_path']
    assert rays['all_probes_match']
    assert sha(old_path)==rays['source_identities']['cap']['sha256']
    assert sha(new_path)==manifest['cap_sha256']
    assert sha(ROOT/rays['view_path'])==rays['view_sha256']
    rows=[]
    with np.load(old_path) as old,np.load(new_path) as new:
        lookup={triangle_key(new['solid_vertices_m'][f]):i for i,f in enumerate(new['solid_triangles'])}
        for probe in rays['probes']:
            hit=probe.get('source_hit')
            if not hit or hit['source']!='cap':continue
            face=hit['source_triangle'];indices=old['solid_triangles'][face]
            assert np.array_equal(indices,hit['source_vertices'])
            match=lookup.get(triangle_key(old['solid_vertices_m'][indices]))
            rows.append(dict(pixel=probe['pixel'],old_face=face,candidate_face=match,
                face_kind=int(old['solid_face_kind'][face]),exact_directed_triangle_retained=match is not None))
    assert rows
    report=dict(source_rays_sha256=sha(rays_path),source_view_sha256=rays['view_sha256'],
        parent_cap_sha256=sha(old_path),candidate_cap_sha256=sha(new_path),targets=rows,
        retained_count=sum(r['exact_directed_triangle_retained'] for r in rows),
        new_visibility_verified=False,spike_repair_accepted=False,playable_integrated=False)
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
