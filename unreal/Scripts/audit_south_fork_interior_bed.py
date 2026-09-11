"""Read-only real-engine check of triangle and bilinear heights off vertices."""
from pathlib import Path
import json
import hashlib
import unreal
ROOT=Path(__file__).resolve().parents[2]
LEVEL='/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable'
MESH='/Game/RaftSim/Environment/SouthForkSurveyGapCandidate20260907/SM_TroublemakerSurveyCandidate.SM_TroublemakerSurveyCandidate'


def main():
    source=ROOT/'docs/reconstruction-review-2026-09-07/interior-mesh-probes.json'
    data=json.loads(source.read_text())
    report=ROOT/'docs/reconstruction-review-2026-09-07/engine-interior-mesh-audit.json'
    if report.exists():raise RuntimeError('Retain prior engine evidence')
    level_file=ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkSurveyPlayable.umap'
    before=hashlib.sha256(level_file.read_bytes()).hexdigest()
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):raise RuntimeError('Cannot load isolated review')
    world=unreal.EditorLevelLibrary.get_editor_world()
    if world.get_path_name().split('.')[0]!=LEVEL:raise RuntimeError('Wrong world')
    ground=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        if isinstance(a,unreal.StaticMeshActor) and unreal.Name('RaftSimPhysicalGround') in a.tags]
    if len(ground)!=1 or ground[0].static_mesh_component.static_mesh.get_path_name()!=MESH:
        raise RuntimeError('Unexpected ground mesh')
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    results=[]
    for probe in data['probes']:
        x,y=probe['position_cm'];z=probe['triangle_height_cm']
        hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,z+2000),
            unreal.Vector(x,y,z-2000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,False)
        values=hit.to_tuple() if hit is not None else None
        if values is None or not values[0]:
            results.append({**probe,'hit':False})
            continue
        height=values[5].z
        results.append({**probe,'hit':True,'actual_collision_height_cm':height,
            'triangle_error_cm':abs(height-z),'bilinear_error_cm':abs(height-probe['bilinear_height_cm'])})
    after=hashlib.sha256(level_file.read_bytes()).hexdigest()
    passed=all(r['hit'] for r in results) and max((r.get('triangle_error_cm',0) for r in results),default=1)<.1 and before==after
    report.write_text(json.dumps({'level':LEVEL,'mesh':MESH,'probe_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_geometry_sha256':data['source_geometry_sha256'],'probes':results,
        'ground_transform':str(ground[0].get_actor_transform()),
        'ground_collision_enabled':str(ground[0].static_mesh_component.get_collision_enabled()),
        'triangle_sampler_matches_engine_collision':passed,'map_unchanged':before==after,'level_sha256':after,
        'production_promoted':False},indent=2),encoding='utf-8')
    if not passed:raise RuntimeError('Triangle sampler differs from actual engine geometry')
    unreal.log('Interior source triangle sampling matches actual captured-mesh collision; no assets saved')


try:main()
finally:unreal.SystemLibrary.quit_editor()
