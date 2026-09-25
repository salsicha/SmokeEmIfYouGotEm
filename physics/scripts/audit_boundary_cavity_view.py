"""Check whether local cavity hypotheses address the diagnosed view at all."""
import json
import sys
import numpy as np
from build_troublemaker_dem_rock_cap import ROOT
from south_fork_rock_union import sha
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from audit_terrain_camera_sources import resolve_ray


def main():
    evidence=ROOT/'docs/reconstruction-review-2026-09-07/independent-lidar-followup'
    construction_path=evidence/'boundary-ground-cavities.json'
    construction=json.loads(construction_path.read_text())
    ray_path=evidence.parent/'downstream-cap-provenance/source-rays.json'
    rays=json.loads(ray_path.read_text())
    ground_path=ROOT/rays['source_identities']['ground']['path']
    parent_path=ROOT/'tmp/troublemaker-constrained-wall-extension-v1-20260925/mixed_survey_rock_cap.npz'
    output=evidence/'boundary-cavity-view.json'
    if output.exists():raise ValueError('Fresh output required')
    if (sha(parent_path)!=construction['parent_sha256'] or sha(ground_path)!=rays['source_identities']['ground']['sha256']
        or sha(ROOT/rays['view_path'])!=rays['view_sha256'] or not rays['all_probes_match']):raise ValueError('Source/view changed')
    with np.load(ground_path) as g:
        sources={'ground':(np.column_stack([g[k].ravel() for k in ('east_m','north_m','z_m')]),g['triangles'])}
    def trace(path):
        with np.load(path) as cap:
            sources['cap']=(cap['solid_vertices_m'],cap['solid_triangles'])
            return [resolve_ray(p['engine'],sources,rays['translation_cm'],rays['reflection']) for p in rays['probes']]
    baseline=trace(parent_path);rows=[]
    for candidate in construction['independent_local_hypotheses']:
        if not candidate['passed']:continue
        path=ROOT/candidate['candidate_path']
        if sha(path)!=candidate['candidate_sha256']:raise ValueError('Candidate changed')
        after=trace(path);probes=[]
        for p,b,a in zip(rays['probes'],baseline,after):
            if b is None or a is None:raise ValueError('Missing retained ray hit')
            probes.append(dict(pixel=p['pixel'],displacement_m=float(np.linalg.norm(np.array(a['local_hit_m'])-b['local_hit_m'])),
                before_source=b['source'],after_source=a['source'],before_slope=b['slope_degrees'],after_slope=a['slope_degrees']))
        rows.append(dict(source_index=candidate['source_index'],sha256=sha(path),probes=probes,
            changed_rays=sum(p['displacement_m']>1e-7 for p in probes)))
    result=dict(construction_sha256=sha(construction_path),rays_sha256=sha(ray_path),candidates=rows,
        native_visibility_verified=False,playable_changed=False,
        limits='Eight retained source-space rays only, fixed earlier candidate ground; not a whole-image or native rendering proof.')
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([dict(source_index=r['source_index'],changed_rays=r['changed_rays']) for r in rows]))


if __name__=='__main__':main()
