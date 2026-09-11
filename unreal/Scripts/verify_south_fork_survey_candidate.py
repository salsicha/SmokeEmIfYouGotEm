"""Probe actual engine collision and bracket deterministic geometry-review light."""
from pathlib import Path
import json
import importlib.util
import unreal

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/reconstruction-review-2026-09-06/engine'
spec=importlib.util.spec_from_file_location('capture_helpers',Path(__file__).with_name('capture_cc0_production_roster.py'))
helpers=importlib.util.module_from_spec(spec); spec.loader.exec_module(helpers)
helpers.OUTPUT_ROOT=OUT


def main():
    manifest=json.loads((ROOT/'unreal/SourceArt/RaftSim/SouthForkSurveyCandidate/manifest.json').read_text())
    report={'status':'checking','production_promoted':False,'water_animation_validated':False}
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/RaftSim/Maps/Review/SouthForkSurveyCandidate')
        world=unreal.EditorLevelLibrary.get_editor_world()
        actors=unreal.EditorLevelLibrary.get_all_level_actors()
        light=next(a for a in actors if isinstance(a,unreal.DirectionalLight))
        terrain=next(a for a in actors if isinstance(a,unreal.StaticMeshActor))
        terrain.static_mesh_component.set_collision_profile_name('BlockAll')
        probes=[]
        for probe in manifest['collision_probes_cm']:
            x,y,z=probe['position_cm']
            hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,z+1000),unreal.Vector(x,y,z-1000),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,False)
            if hit is None: raise RuntimeError(f'Captured geometry collision missing at {probe}')
            # HitResult's native break function is exposed as StructBase.to_tuple.
            values=hit.to_tuple()
            blocking,point=values[0],values[5]
            error=abs(point.z-z)
            probes.append({**probe,'blocking':blocking,'impact_cm':[point.x,point.y,point.z],'height_error_cm':error})
            if not blocking or error>2.: raise RuntimeError(f'Collision/terrain mismatch: {probes[-1]}')
        report['collision_probes']=probes
        capture=helpers.spawn(unreal.SceneCapture2D,unreal.Vector(14000,-8000,6000))
        capture.set_actor_rotation(helpers.look_at(capture.get_actor_location(),unreal.Vector(-1500,1000,700)),False)
        comp=capture.capture_component2d
        comp.set_editor_property('capture_source',unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        comp.set_editor_property('capture_every_frame',False)
        comp.set_editor_property('post_process_blend_weight',1.)
        settings=comp.get_editor_property('post_process_settings')
        for key,value in {'override_auto_exposure_method':True,'auto_exposure_method':unreal.AutoExposureMethod.AEM_MANUAL,
            'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,
            'override_auto_exposure_bias':True,'auto_exposure_bias':0.,'override_bloom_intensity':True,'bloom_intensity':0.}.items():
            settings.set_editor_property(key,value)
        comp.set_editor_property('post_process_settings',settings)
        target=unreal.RenderingLibrary.create_render_target2d(world,1536,1024,unreal.TextureRenderTargetFormat.RTF_RGBA8,
            unreal.LinearColor(.03,.03,.03,1),False)
        comp.set_editor_property('texture_target',target)
        for command in ('r.Nanite 0','r.UsePreExposure 0','r.EyeAdaptationQuality 0','r.BloomQuality 0','r.PostProcessAAQuality 2'):
            unreal.SystemLibrary.execute_console_command(world,command)
        report['review_light_brackets']={}
        for intensity in (3.,30.,300.,3000.):
            light.light_component.set_intensity(intensity)
            report['review_light_brackets'][str(intensity)]=str(helpers.export_capture(world,comp,target,f'geometry_light_{intensity:g}'))
        report.update(status='collision_samples_passed_geometry_review_only',source_geometry_sha256=manifest['source_geometry_sha256'],
            raft_collision_validated=False)
    except Exception as error:
        report.update(status='failed',error=str(error)); raise
    finally:
        (OUT/'collision_and_capture_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':main()
