"""Stage matched registered-XY geometry and flow in a NEW review map only."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'unreal/SourceArt/RaftSim/SouthForkRockRegisteredCandidate20260907'
FIELDS=ROOT/'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907/engine_review'
DEST='/Game/RaftSim/Environment/SouthForkRockRegisteredCandidate20260907'
NAME='SM_TroublemakerSurveyCandidate'
BASE_LEVEL='/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable'
LEVEL='/Game/RaftSim/Maps/Review/SouthForkRegisteredRockPlayable'
BASE_FILE=ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkSurveyPlayable.umap'
# Exact original map identity, independent from the hydraulic manifest hash.
BASE_SHA='2c53df655cd7fa83a232f40f951c4babcdc34adbd3fb7aafda8db270b64969bd'
REPORT=ROOT/'docs/reconstruction-review-2026-09-07/registered-rock-engine-integration.json'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if REPORT.exists() or unreal.EditorAssetLibrary.does_asset_exist(LEVEL) or unreal.EditorAssetLibrary.does_asset_exist(DEST+'/'+NAME):
        raise RuntimeError('Candidate already attempted; inspect retained evidence before retrying')
    if sha(BASE_FILE)!=BASE_SHA:raise ValueError('Baseline map changed')
    manifest=json.loads((SOURCE/'manifest.json').read_text())
    fields=json.loads((FIELDS/'manifest.json').read_text())
    start=json.loads((FIELDS/'engine_start.json').read_text())
    geometry=json.loads((ROOT/manifest['source_geometry_manifest']).read_text())
    audit=json.loads((ROOT/'docs/reconstruction-review-2026-09-07/rock-xy-mesh-audit.json').read_text())
    expected=manifest['source_geometry_sha256']
    if geometry.get('schema')!='raftsim.captured_rock_xy_mesh_candidate.v1':raise ValueError('Wrong geometry schema')
    if any(s!=expected for s in (fields['review']['source_geometry_sha256'],start['source_geometry_sha256'],
        geometry['mesh_sha256'],sha(ROOT/geometry['mesh_path']),manifest['mesh_source_sha256'],audit['source_mesh_sha256'])):
        raise ValueError('Render, collision, hydraulic and audited mesh identities disagree')
    if any(record.get(key)!='registered_triangles' for record,key in (
        (manifest,'source_bed_sampling'),(fields['review'],'source_bed_sampling'),(start,'source_bed_sampling'))):
        raise ValueError('Registered mesh sampling not explicit throughout package')
    if sha(ROOT/manifest['fbx'])!=manifest['fbx_sha256']:raise ValueError('FBX changed')
    if not audit['sampling_passed']:raise ValueError('Sampling audit failed')
    history=fields['review']['saved_frame_sanity']
    if not history or not all(frame['passed'] for frame in history):raise ValueError('Unsafe hydraulic history')
    for array in fields['bands'][0]['arrays'].values():
        if sha(FIELDS/array['file'])!=array['sha256']:raise ValueError('Hydraulic array changed')
    if (start['cooked_fields_dir']!=FIELDS.relative_to(ROOT).as_posix() or
        start['coordinate_map_path']!=(FIELDS/'coordinate_map.json').relative_to(ROOT).as_posix()):
        raise ValueError('Start refers to another package')
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    # Generic asset duplication leaves a standalone UWorld rooted and crashes
    # UE's old-world GC check on load. Use the level subsystem's template path.
    if not levels.new_level_from_template(LEVEL,BASE_LEVEL):raise RuntimeError('Cannot create new review map from template')
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
    options=unreal.FbxImportUI()
    options.automated_import_should_detect_type=False
    options.import_mesh=True;options.import_as_skeletal=False
    options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.original_import_type=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials=False;options.import_textures=False;options.import_animations=False
    options.static_mesh_import_data.combine_meshes=True
    options.static_mesh_import_data.convert_scene_unit=True
    options.static_mesh_import_data.generate_lightmap_u_vs=False
    options.static_mesh_import_data.auto_generate_collision=False
    task=unreal.AssetImportTask()
    task.filename=str(ROOT/manifest['fbx']);task.destination_path=DEST;task.destination_name=NAME
    task.automated=True;task.replace_existing=False;task.save=False
    task.factory=unreal.FbxFactory();task.options=options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh=unreal.load_asset(DEST+'/'+NAME)
    if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError('Mesh import failed')
    bounds=mesh.get_bounding_box()
    actual=[[bounds.min.x,bounds.min.y,bounds.min.z],[bounds.max.x,bounds.max.y,bounds.max.z]]
    if max(abs(actual[i][j]-manifest['expected_unreal_bounds_cm'][i][j]) for i in range(2) for j in range(3))>2:
        raise RuntimeError('Imported geographic axes or scale disagree')
    mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    subsystem=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    subsystem.enable_section_collision(mesh,True,0,0)
    settings=subsystem.get_nanite_settings(mesh);settings.enabled=True
    settings.fallback_target=unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
    settings.fallback_percent_triangles=1.;settings.fallback_relative_error=0.
    subsystem.set_nanite_settings(mesh,settings)
    mesh.set_material(0,ground.static_mesh_component.static_mesh.get_material(0))
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if mesh.get_num_triangles(0)!=manifest['triangle_count']:raise RuntimeError('Collision triangles simplified')
    if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False):raise RuntimeError('Mesh save failed')
    ground.static_mesh_component.set_static_mesh(mesh)
    ground.static_mesh_component.set_collision_profile_name('BlockAll')
    probes=[]
    positions=[p['position_cm'] for p in manifest['collision_probes_cm']]+audit['changed_diagonal_interior_collision_probes_cm']
    for x,y,z in positions:
        hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,z+1000),unreal.Vector(x,y,z-1000),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,False)
        values=hit.to_tuple() if hit is not None else None
        if values is None or not values[0] or abs(values[5].z-z)>.1:
            raise RuntimeError(f'Collision differs from exact source triangle at {(x,y,z)}')
        probes.append({'position_cm':[x,y,z],'height_error_cm':abs(values[5].z-z)})
    for name in ('cooked_fields_dir','coordinate_map_path','window_extent_m'):
        config.set_editor_property(name,start[name])
    location=unreal.Vector(*start['location_cm'])
    rotation=unreal.Rotator(pitch=0,yaw=start['yaw_degrees'],roll=0)
    for actor in [raft,*[a for a in actors if isinstance(a,unreal.PlayerStart)]]:
        actor.set_actor_location(location,False,False);actor.set_actor_rotation(rotation,False)
    ground.set_actor_label('Captured rock XY and heights - inferred bed and connecting faces')
    if world.get_path_name().split('.')[0]!=LEVEL or not levels.save_current_level():raise RuntimeError('Review save failed')
    if sha(BASE_FILE)!=BASE_SHA:raise RuntimeError('Baseline was unexpectedly modified')
    REPORT.write_text(json.dumps({'status':'separate_registered_rock_candidate_staged_not_accepted',
        'level':LEVEL,'mesh':mesh.get_path_name(),'source_geometry_sha256':expected,
        'fields_manifest_sha256':sha(FIELDS/'manifest.json'),'cooked_fields_dir':start['cooked_fields_dir'],
        'baseline_map_unchanged':True,'baseline_map_sha256':BASE_SHA,'collision_probes':probes,
        'triangle_count':mesh.get_num_triangles(0),'surface_lighting_preserved':True,
        'underwater_geometry_measured':False,'runtime_replay_validated':False,
        'natural_traversal_validated':False,'visual_acceptance':False,'production_promoted':False},indent=2),encoding='utf-8')
    unreal.log('Separate registered-rock candidate staged; original map unchanged')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
