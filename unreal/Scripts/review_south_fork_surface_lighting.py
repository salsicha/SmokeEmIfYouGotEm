"""Opt-in single-carrier lighting experiment; never edit the shared material."""
from pathlib import Path
import json
import hashlib
import shutil
import unreal

ROOT=Path(__file__).resolve().parents[2]
LEVEL='/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable'
SOURCE='/Game/RaftSim/Materials/M_RaftSim_LiveRiverSurface'
TARGET='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_SurfaceLitReview'
REPORT=ROOT/'docs/reconstruction-review-2026-09-07/surface-lighting-setup.json'


def main():
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):raise RuntimeError('Cannot open isolated review level')
    world=unreal.EditorLevelLibrary.get_editor_world()
    if world.get_path_name().split('.')[0]!=LEVEL:raise RuntimeError('Wrong world; no changes made')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    configs=[a for a in actors if a.get_class().get_name()=='RaftSimRiverWaterConfig']
    surfaces=[a for a in actors if a.get_class().get_name()=='RaftSimWaterSurfaceActor']
    if len(configs)!=1 or len(surfaces)>1:raise RuntimeError('Ambiguous review water ownership')
    config=configs[0]
    if not config.get_editor_property('live_solver_owns_runtime_rendering') or config.get_editor_property('enable_live_solver_volume_core'):
        raise RuntimeError('Only the single visible carrier, without a second volume, is in scope')
    level_file=ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkSurveyPlayable.umap'
    backup=ROOT/'tmp/project-cleanup/SouthForkSurveyPlayable-before-surface-lighting.umap'
    if backup.exists() or unreal.EditorAssetLibrary.does_asset_exist(TARGET):
        raise RuntimeError('Experiment already exists; inspect it before replacing any state')
    backup.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(level_file,backup)
    source_file=ROOT/'unreal/Content/RaftSim/Materials/M_RaftSim_LiveRiverSurface.uasset'
    source_sha=hashlib.sha256(source_file.read_bytes()).hexdigest()
    material=unreal.EditorAssetLibrary.duplicate_asset(SOURCE,TARGET)
    if material is None:raise RuntimeError('Material duplication failed')
    previous=str(material.get_editor_property('translucency_lighting_mode'))
    material.set_editor_property('translucency_lighting_mode',unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    surface=surfaces[0] if surfaces else unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.load_class(None,'/Script/RaftSimRaft.RaftSimWaterSurfaceActor'),unreal.Vector())
    surface.set_actor_label('Single survey carrier - surface lighting experiment')
    surface.set_editor_property('water_material',material)
    if not levels.save_current_level():raise RuntimeError('Review level save failed')
    if hashlib.sha256(source_file.read_bytes()).hexdigest()!=source_sha:
        raise RuntimeError('Shared material changed unexpectedly')
    REPORT.write_text(json.dumps({'status':'isolated_lighting_experiment_not_visual_acceptance',
        'level':LEVEL,'material':TARGET,'previous_lighting_mode':previous,
        'lighting_mode':str(material.get_editor_property('translucency_lighting_mode')),
        'backup':backup.relative_to(ROOT).as_posix(),'shared_material_unchanged':True,
        'source_material_sha256':source_sha,'geometry_or_physics_modified':False,
        'production_scene_modified':False,'visual_acceptance':False},indent=2))
    unreal.log('Survey single-carrier lighting experiment saved; visual review still required')


if __name__=='__main__':main()
