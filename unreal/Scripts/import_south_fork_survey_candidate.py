"""Import a separate geographically registered review level. Never overwrite production."""
from pathlib import Path
import json
import hashlib
import importlib.util
import unreal

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'unreal/SourceArt/RaftSim/SouthForkSurveyCandidate'
DEST='/Game/RaftSim/Environment/SouthForkSurveyCandidate'
NAME='SM_TroublemakerSurveyCandidate'
LEVEL='/Game/RaftSim/Maps/Review/SouthForkSurveyCandidate'
OUT=ROOT/'docs/reconstruction-review-2026-09-06/engine'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'status':'import_started','production_scene_modified':False}
    try:
        manifest=json.loads((SOURCE/'manifest.json').read_text())
        path=ROOT/manifest['fbx']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['fbx_sha256']:
            raise ValueError('Candidate FBX source hash mismatch')
        options=unreal.FbxImportUI()
        options.automated_import_should_detect_type=False
        options.import_mesh=True; options.import_as_skeletal=False
        options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
        options.original_import_type=unreal.FBXImportType.FBXIT_STATIC_MESH
        options.import_materials=False; options.import_textures=False; options.import_animations=False
        options.static_mesh_import_data.combine_meshes=True
        options.static_mesh_import_data.convert_scene_unit=True
        options.static_mesh_import_data.generate_lightmap_u_vs=False
        options.static_mesh_import_data.auto_generate_collision=False
        task=unreal.AssetImportTask()
        task.filename=str(path); task.destination_path=DEST; task.destination_name=NAME
        task.automated=True; task.replace_existing=True; task.save=False
        task.replace_existing_settings=True
        task.factory=unreal.FbxFactory(); task.options=options
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        mesh=unreal.load_asset(DEST+'/'+NAME)
        if not isinstance(mesh,unreal.StaticMesh): raise RuntimeError('Candidate mesh import failed')
        bounds=mesh.get_bounding_box()
        actual=[[bounds.min.x,bounds.min.y,bounds.min.z],[bounds.max.x,bounds.max.y,bounds.max.z]]
        report['bounds_cm']=actual
        if max(abs(actual[i][j]-manifest['expected_unreal_bounds_cm'][i][j]) for i in range(2) for j in range(3))>2:
            raise RuntimeError('Imported geographic axes or centimetre scale do not match source')
        body=mesh.get_editor_property('body_setup')
        body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        subsystem=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        subsystem.enable_section_collision(mesh,True,0,0)
        settings=subsystem.get_nanite_settings(mesh)
        settings.enabled=True
        # Collision uses full source triangles; do not use a simplified hull
        # that could bridge the channel or miss recovered exposed rock.
        settings.fallback_target=unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
        settings.fallback_percent_triangles=1.
        settings.fallback_relative_error=0.
        subsystem.set_nanite_settings(mesh,settings)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        if mesh.get_num_triangles(0)!=manifest['triangle_count']:
            raise RuntimeError('Collision fallback no longer matches captured geometry triangles')
        material=unreal.load_asset('/Engine/EngineMaterials/WorldGridMaterial')
        mesh.set_material(0,material)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False)
        levelsub=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
            if not levelsub.load_level(LEVEL): raise RuntimeError('Cannot load geometry review level')
            review_world=unreal.EditorLevelLibrary.get_editor_world()
            if review_world.get_path_name().split('.')[0]!=LEVEL: raise RuntimeError('Wrong geometry review world')
            for existing in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
                if existing.get_class().get_name() not in ('WorldSettings','Brush'):
                    unreal.EditorLevelLibrary.destroy_actor(existing)
        elif not levelsub.new_level(LEVEL):
            raise RuntimeError('Cannot create geometry review level')
        if unreal.EditorLevelLibrary.get_editor_world().get_path_name().split('.')[0]!=LEVEL:
            raise RuntimeError('Refusing to modify a non-review world')
        actor=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector())
        actor.set_actor_label('Captured Troublemaker - shared render and collision geometry')
        actor.tags = [unreal.Name('RaftSimPhysicalGround')]
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.static_mesh_component.set_collision_profile_name('BlockAll')
        light=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,30000),unreal.Rotator(-40,-35,0))
        light.light_component.set_editor_property('intensity',75000.)
        light.light_component.set_editor_property('cast_shadows',True)
        sky=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight,unreal.Vector())
        sky.light_component.set_editor_property('intensity',.4)
        spec=importlib.util.spec_from_file_location('capture_helpers',Path(__file__).with_name('capture_cc0_production_roster.py'))
        helpers=importlib.util.module_from_spec(spec); spec.loader.exec_module(helpers)
        helpers.OUTPUT_ROOT=OUT
        world=unreal.EditorLevelLibrary.get_editor_world()
        capture=helpers.spawn(unreal.SceneCapture2D,unreal.Vector())
        comp=capture.capture_component2d
        comp.set_editor_property('capture_source',unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        comp.set_editor_property('capture_every_frame',False)
        exposure=comp.get_editor_property('post_process_settings')
        exposure.set_editor_property('override_auto_exposure_method',True)
        exposure.set_editor_property('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL)
        exposure.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True)
        exposure.set_editor_property('auto_exposure_apply_physical_camera_exposure',True)
        exposure.set_editor_property('override_camera_iso',True)
        exposure.set_editor_property('camera_iso',100.)
        exposure.set_editor_property('override_camera_shutter_speed',True)
        exposure.set_editor_property('camera_shutter_speed',125.)
        exposure.set_editor_property('override_depth_of_field_fstop',True)
        exposure.set_editor_property('depth_of_field_fstop',8.)
        comp.set_editor_property('post_process_settings',exposure)
        target=unreal.RenderingLibrary.create_render_target2d(world,1536,1024,unreal.TextureRenderTargetFormat.RTF_RGBA8,
            unreal.LinearColor(.08,.1,.13,1),False)
        comp.set_editor_property('texture_target',target)
        for command in ('r.Nanite 0','r.PostProcessAAQuality 2','r.ScreenPercentage 100'):
            unreal.SystemLibrary.execute_console_command(world,command)
        images={}
        for label,loc,aim in [('overhead',unreal.Vector(0,0,30000),unreal.Vector(0,0,600)),
            ('upstream',unreal.Vector(14000,-8000,6000),unreal.Vector(-1500,1000,700)),
            ('downstream',unreal.Vector(-14000,9000,6000),unreal.Vector(0,0,700))]:
            capture.set_actor_location(loc,False,False); capture.set_actor_rotation(helpers.look_at(loc,aim),False)
            comp.set_editor_property('fov_angle',58.)
            images[label]=str(helpers.export_capture(world,comp,target,label))
        if world.get_path_name().split('.')[0]!=LEVEL: raise RuntimeError('Refusing to save a non-review world')
        if not levelsub.save_current_level(): raise RuntimeError('Geometry review save failed')
        report.update(status='candidate_geometry_imported_not_playable_acceptance',level=LEVEL,
            mesh=mesh.get_path_name(),images=images,collision_complexity=str(subsystem.get_collision_complexity(mesh)),
            source_geometry_sha256=manifest['source_geometry_sha256'],
            collision_triangle_count=mesh.get_num_triangles(0),water_animation_validated=False,
            raft_collision_validated=False,production_promoted=False)
    except Exception as error:
        report.update(status='failed',error=str(error)); raise
    finally:
        (OUT/'import_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':main()
