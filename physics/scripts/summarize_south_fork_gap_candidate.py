"""Record the bounded gap-repair experiment, without claiming scene acceptance."""
from pathlib import Path
import json
import hashlib

ROOT=Path(__file__).resolve().parents[2]
LABEL='enclosed-rock-gaps-continuation-20260907'


def main():
    work=ROOT/f'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-{LABEL}'
    old=ROOT/'docs/reconstruction-review-2026-09-06'
    new=ROOT/'docs/reconstruction-review-2026-09-07'
    def read(path):return json.loads(path.read_text())
    geometry=read(ROOT/'tmp/south-fork-rock-gap-candidate-20260907/manifest.json')
    registration=read(work/'registration.json')
    fields=read(work/'engine_review/manifest.json')
    flow=read(old/f'troublemaker_survey_flow_1m-mixed-inlet-{LABEL}.json')
    flux=read(old/f'troublemaker_numerical_boundary_flux-{LABEL}.json')
    sha=geometry['shared_geometry_sha256']
    if any(actual!=sha for actual in [registration['geometry_sha256'],
        fields['review']['source_geometry_sha256'],flow['geometry_sha256'],flux['source_geometry_sha256']]):
        raise ValueError('Diagnostic evidence belongs to different geometries')
    if hashlib.sha256((ROOT/geometry['shared_geometry_path']).read_bytes()).hexdigest()!=sha:
        raise ValueError('Candidate geometry has changed since cooking')
    integration_path=new/'gap-engine-integration.json'
    integration=read(integration_path) if integration_path.exists() else None
    level_path=ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkSurveyPlayable.umap'
    integrated=bool(integration and integration['source_geometry_sha256']==sha
        and hashlib.sha256(level_path.read_bytes()).hexdigest()==integration['saved_level_sha256'])
    report={'status':'diagnostic_mean_flow_screen_passed_not_scene_acceptance',
        'geometry_sha256':sha,'parent_geometry_sha256':geometry['parent_geometry_sha256'],
        'repair':geometry['small_gap_interpolation'],
        'simulation_lineage_seconds':{'initial_cook':200,'continuation':400,'total':600},
        'geometry_manifest':'tmp/south-fork-rock-gap-candidate-20260907/manifest.json',
        'mean_flow':flow,'numerical_face_flux':flux,
        'all_saved_continuation_frames_sane':all(f['passed'] for f in fields['review']['saved_frame_sanity']),
        'saved_continuation_frame_count':len(fields['review']['saved_frame_sanity']),
        'maximum_saved_depth_m':max(f['maximum_depth_m'] for f in fields['review']['saved_frame_sanity']),
        'maximum_saved_speed_mps':max(f['maximum_speed_mps'] for f in fields['review']['saved_frame_sanity']),
        'engine_package_exported':str((work/'engine_review').relative_to(ROOT)),
        'engine_package_loaded':integrated,'replacement_mesh_imported':integrated,
        'engine_integration_evidence':str(integration_path.relative_to(ROOT)) if integrated else None,
        'spatial_convergence_validated':False,'underwater_bed_measured':False,
        'visual_acceptance':False,'whole_rapid_traversal_accepted':False,'production_promoted':False}
    (new/'rock-gap-candidate.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('mean_flow','numerical_face_flux')},indent=2))


if __name__=='__main__':main()
