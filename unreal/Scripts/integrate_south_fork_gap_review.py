"""Load matching gap-candidate terrain/collision/fields into the isolated review.

Preserve the existing lighting experiment and all production assets. Never pair
new hydraulic fields with the old visible/collision mesh, even temporarily on disk.
"""
from pathlib import Path
import hashlib
import json
import shutil
import unreal

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'unreal/SourceArt/RaftSim/SouthForkSurveyGapCandidate20260907'
FIELDS=ROOT/'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-enclosed-rock-gaps-continuation-20260907/engine_review'
DEST='/Game/RaftSim/Environment/SouthForkSurveyGapCandidate20260907'
NAME='SM_TroublemakerSurveyCandidate'
LEVEL='/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable'
REPORT=ROOT/'docs/reconstruction-review-2026-09-07/gap-engine-integration.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest=json.loads((SOURCE/'manifest.json').read_text())
    fields=json.loads((FIELDS/'manifest.json').read_text())
    start=json.loads((FIELDS/'engine_start.json').read_text())
    geometry=json.loads((ROOT/manifest['source_geometry_manifest']).read_text())
    expected=manifest['source_geometry_sha256']
    if any(s!=expected for s in (fields['review']['source_geometry_sha256'],start['source_geometry_sha256'],
                                geometry['shared_geometry_sha256'],sha(ROOT/geometry['shared_geometry_path']))):
        raise ValueError('Mesh, collision, geometry and fields must have the same source identity')
    mesh_source=(ROOT/manifest['source_geometry_manifest']).parent/'engine_mesh_source.npz'
    if sha(mesh_source)!=manifest['mesh_source_sha256'] or sha(ROOT/manifest['fbx'])!=manifest['fbx_sha256']:
        raise ValueError('Exported mesh no longer matches its recorded source')
    for record in fields['bands'][0]['arrays'].values():
        if sha(FIELDS/record['file'])!=record['sha256']:raise ValueError('Hydraulic array changed after export')
    if not all(f['passed'] for f in fields['review']['saved_frame_sanity']):raise ValueError('Unstable flow package')
    backup=ROOT/'tmp/project-cleanup/SouthForkSurveyPlayable-before-gap-integration.umap'
    if backup.exists() or unreal.EditorAssetLibrary.does_asset_exist(DEST+'/'+NAME):
        raise RuntimeError('Candidate already staged; inspect it instead of overwriting evidence')
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):raise RuntimeError('Cannot load isolated review level')
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
    old_mesh=ground.static_mesh_component.static_mesh.get_path_name()
    old_fields=config.get_editor_property('cooked_fields_dir')
    level_file=ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkSurveyPlayable.umap'
    backup.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(level_file,backup)
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
    if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError('Candidate mesh import failed')
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
    unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False)
    ground.static_mesh_component.set_static_mesh(mesh)
    ground.static_mesh_component.set_collision_profile_name('BlockAll')
    probes=[]
    for probe in manifest['collision_probes_cm']:
        x,y,z=probe['position_cm']
        hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,z+1000),unreal.Vector(x,y,z-1000),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,False)
        values=hit.to_tuple() if hit is not None else None
        if values is None or not values[0] or abs(values[5].z-z)>2:
            raise RuntimeError(f'Collision height differs from exported mesh at {probe}')
        probes.append({**probe,'height_error_cm':abs(values[5].z-z)})
    for name in ('cooked_fields_dir','coordinate_map_path','window_extent_m'):
        config.set_editor_property(name,start[name])
    location=unreal.Vector(*start['location_cm'])
    rotation=unreal.Rotator(pitch=0,yaw=start['yaw_degrees'],roll=0)
    raft.set_actor_location(location,False,False);raft.set_actor_rotation(rotation,False)
    for actor in actors:
        if isinstance(actor,unreal.PlayerStart):
            actor.set_actor_location(location,False,False);actor.set_actor_rotation(rotation,False)
    ground.set_actor_label('Captured geometry with enclosed-gap interpolation - candidate')
    if world.get_path_name().split('.')[0]!=LEVEL or not levels.save_current_level():raise RuntimeError('Review save failed')
    REPORT.write_text(json.dumps({'status':'matching_candidate_loaded_not_scene_acceptance',
        'level':LEVEL,'mesh':mesh.get_path_name(),'source_geometry_sha256':expected,
        'cooked_fields_dir':start['cooked_fields_dir'],'previous_mesh':old_mesh,'previous_fields':old_fields,
        'backup':backup.relative_to(ROOT).as_posix(),'backup_sha256':sha(backup),'saved_level_sha256':sha(level_file),
        'collision_probes':probes,'triangle_count':mesh.get_num_triangles(0),
        'surface_lighting_preserved':True,'underwater_geometry_measured':False,
        'runtime_replay_validated':False,'natural_traversal_validated':False,
        'visual_acceptance':False,'production_promoted':False},indent=2))
    unreal.log('Matching candidate render mesh, collision and hydraulic fields saved in isolated review')


if __name__=='__main__':main()
