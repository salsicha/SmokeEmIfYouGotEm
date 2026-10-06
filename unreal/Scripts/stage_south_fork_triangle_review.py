"""Reversible field-only staging in the existing, explicitly unaccepted review.

Do not import meshes, change production assets or replace previous evidence.
The unchanged terrain already uses these source triangles. Only the hydraulic
package, coordinate map and matching safe upstream start are switched.
"""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[2]
LEVEL='/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable'
LEVEL_FILE=Path('unreal/Content/RaftSim/Maps/Review/SouthForkSurveyPlayable.umap')
BEFORE_SHA='28a26ed62d95403d964a23dcef00382dbbb063415b3ca85f87df36362b07c6cb'
OLD_FIELDS='tmp/south-fork-survey-hydraulics/1m-mixed-inlet-enclosed-rock-gaps-continuation-20260907/engine_review'
NEW_FIELDS='tmp/south-fork-survey-hydraulics/1m-mixed-inlet-mesh-triangles-20260907/engine_review'
MESH='/Game/RaftSim/Environment/SouthForkSurveyGapCandidate20260907/SM_TroublemakerSurveyCandidate.SM_TroublemakerSurveyCandidate'
BACKUP=Path('tmp/project-cleanup/SouthForkSurveyPlayable-before-triangle-fields.umap')
REPORT=Path('docs/reconstruction-review-2026-09-07/triangle-engine-integration.json')
SOURCE=Path('unreal/SourceArt/RaftSim/SouthForkSurveyGapCandidate20260907/manifest.json')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_package(root=ROOT):
    if (root/BACKUP).exists() or (root/REPORT).exists():
        raise FileExistsError('Already staged or attempted: retain rollback and inspect before any retry')
    if sha(root/LEVEL_FILE)!=BEFORE_SHA:raise ValueError('Review map changed; do not overwrite later work')
    folder=root/NEW_FIELDS
    fields=json.loads((folder/'manifest.json').read_text())
    start=json.loads((folder/'engine_start.json').read_text())
    source=json.loads((root/SOURCE).read_text())
    geometry_path=root/source['source_geometry_manifest']
    geometry=json.loads(geometry_path.read_text())
    identity=source['source_geometry_sha256']
    if any(value!=identity for value in (fields['review']['source_geometry_sha256'],
        start['source_geometry_sha256'],geometry['shared_geometry_sha256'],sha(root/geometry['shared_geometry_path']))):
        raise ValueError('Source geometry identity mismatch')
    if (fields['review'].get('source_bed_sampling')!='render_triangles' or
        start.get('source_bed_sampling')!='render_triangles'):
        raise ValueError('Triangle sampling not recorded in both exports')
    if (start['cooked_fields_dir']!=NEW_FIELDS or
        start['coordinate_map_path']!=NEW_FIELDS+'/coordinate_map.json'):
        raise ValueError('Start references different fields/registration')
    if fields.get('production_promoted') is not False or fields.get('all_bands_passed') is not False:
        raise ValueError('This diagnostic must remain explicitly unaccepted')
    frames=fields['review']['saved_frame_sanity']
    if not frames or not all(frame['passed'] for frame in frames):raise ValueError('Unsafe saved history')
    for record in fields['bands'][0]['arrays'].values():
        if sha(folder/record['file'])!=record['sha256']:raise ValueError('Exported hydraulic array changed')
    if (sha(root/source['fbx'])!=source['fbx_sha256'] or
        sha(geometry_path.parent/'engine_mesh_source.npz')!=source['mesh_source_sha256']):
        raise ValueError('Mesh export source changed')
    return fields,start,source


def main():
    import unreal
    fields,start,source=validate_package()
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):raise RuntimeError('Cannot load review level')
    world=unreal.EditorLevelLibrary.get_editor_world()
    if world.get_path_name().split('.')[0]!=LEVEL:raise RuntimeError('Wrong world')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    def one(predicate):
        found=[a for a in actors if predicate(a)]
        if len(found)!=1:raise RuntimeError('Ambiguous review actor ownership')
        return found[0]
    ground=one(lambda a:isinstance(a,unreal.StaticMeshActor) and unreal.Name('RaftSimPhysicalGround') in a.tags)
    config=one(lambda a:a.get_class().get_name()=='RaftSimRiverWaterConfig')
    raft=one(lambda a:a.get_class().get_name()=='RaftSimRaftActor')
    if ground.static_mesh_component.static_mesh.get_path_name()!=MESH or config.get_editor_property('cooked_fields_dir')!=OLD_FIELDS:
        raise RuntimeError('Loaded map does not match expected preceding review')
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if ground.static_mesh_component.static_mesh.get_num_triangles(0)!=source['triangle_count']:
        raise RuntimeError('Terrain topology changed')
    probes=json.loads((ROOT/'docs/reconstruction-review-2026-09-07/interior-mesh-probes.json').read_text())
    results=[]
    for probe in probes['probes']:
        x,y=probe['position_cm'];z=probe['triangle_height_cm']
        hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,z+2000),
            unreal.Vector(x,y,z-2000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,False)
        values=hit.to_tuple() if hit is not None else None
        if values is None or not values[0] or abs(values[5].z-z)>.1:
            raise RuntimeError('Existing collision no longer matches interior source triangles')
        results.append({**probe,'height_error_cm':abs(values[5].z-z)})
    immutable=[ROOT/'unreal/Content/RaftSim/Environment/SouthForkSurveyGapCandidate20260907/SM_TroublemakerSurveyCandidate.uasset',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_SurfaceLitReview.uasset']
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in immutable}
    # All read-only checks precede mutation. Exclusive backup creation preserves
    # the only exact pre-change review if a later save fails.
    (ROOT/BACKUP).parent.mkdir(parents=True,exist_ok=True)
    with (ROOT/LEVEL_FILE).open('rb') as src,(ROOT/BACKUP).open('xb') as dst:shutil.copyfileobj(src,dst)
    if sha(ROOT/BACKUP)!=BEFORE_SHA:raise RuntimeError('Rollback copy differs')
    for name in ('cooked_fields_dir','coordinate_map_path','window_extent_m'):
        config.set_editor_property(name,start[name])
    location=unreal.Vector(*start['location_cm'])
    rotation=unreal.Rotator(pitch=0,yaw=start['yaw_degrees'],roll=0)
    for actor in [raft,*[a for a in actors if isinstance(a,unreal.PlayerStart)]]:
        actor.set_actor_location(location,False,False);actor.set_actor_rotation(rotation,False)
    if world.get_path_name().split('.')[0]!=LEVEL or not levels.save_current_level():raise RuntimeError('Review save failed')
    unchanged=all(sha(ROOT/p)==value for p,value in hashes.items())
    (ROOT/REPORT).write_text(json.dumps({'status':'triangle_fields_staged_not_accepted','level':LEVEL,
        'cooked_fields_dir':NEW_FIELDS,'previous_fields':OLD_FIELDS,'source_bed_sampling':'render_triangles',
        'source_geometry_sha256':source['source_geometry_sha256'],
        'fields_manifest_sha256':sha(ROOT/NEW_FIELDS/'manifest.json'),
        'backup':BACKUP.as_posix(),'backup_sha256':sha(ROOT/BACKUP),'saved_level_sha256':sha(ROOT/LEVEL_FILE),
        'unchanged_asset_hashes':hashes,'mesh_and_material_unchanged':unchanged,'collision_probes':results,
        'hydraulic_settling_accepted':False,'runtime_replay_validated':False,'natural_traversal_validated':False,
        'visual_acceptance':False,'production_promoted':False},indent=2),encoding='utf-8')
    if not unchanged:raise RuntimeError('Unexpected terrain/material change')
    unreal.log('Triangle-sampled fields staged in isolated review only; full hydraulic and visual acceptance remain separate')


if __name__=='__main__':
    import unreal
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
