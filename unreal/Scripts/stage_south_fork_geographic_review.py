"""Stage an ENU-to-Unreal orientation correction; never move source survey data."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
BASE='/Game/RaftSim/Maps/Review/SouthForkRegisteredRockPlayable'
LEVEL='/Game/RaftSim/Maps/Review/Geographic/SouthForkRegisteredRockPlayable'
BASE_FILE=ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkRegisteredRockPlayable.umap'
EXPECTED_BASE='81f31bec7ba8683e3a7479f17333419b6d32eeB277de5630f098d41fdf705ad7'.lower()
FIELDS=ROOT/'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907/engine_review'
OUTPUT=ROOT/'docs/reconstruction-review-2026-09-07/geographic-scene'
MAP=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/geographic_engine_review/coordinate_map.json'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists() or MAP.exists() or unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
        raise RuntimeError('Geographic review already attempted; preserve and inspect it')
    if sha(BASE_FILE)!=EXPECTED_BASE: raise RuntimeError('Registered baseline map changed')
    test=json.loads((ROOT/'docs/reconstruction-review-2026-09-07/engine-geographic-handedness-v3/index.json').read_text(encoding='utf-8-sig'))
    if test['failed'] or test['notRun'] or test['succeeded']!=1:
        raise RuntimeError('Actual geographic/current parity test has not passed')
    source=json.loads((FIELDS/'coordinate_map.json').read_text())
    source['world_y_sign']=-1
    source['source_coordinate_map_sha256']=sha(FIELDS/'coordinate_map.json')
    source['engine_axis_convention']='X=east, Y=south, Z=up; source points remain ENU'
    MAP.parent.mkdir(parents=True,exist_ok=True)
    MAP.write_text(json.dumps(source,indent=2)+'\n')
    OUTPUT.mkdir(parents=True)
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.new_level_from_template(LEVEL,BASE): raise RuntimeError('Review template creation failed')
    world=unreal.EditorLevelLibrary.get_editor_world()
    if world.get_path_name().split('.')[0]!=LEVEL: raise RuntimeError('Wrong world')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    def one(predicate):
        found=[a for a in actors if predicate(a)]
        if len(found)!=1: raise RuntimeError('Ambiguous geographic actor ownership')
        return found[0]
    ground=one(lambda a:isinstance(a,unreal.StaticMeshActor) and unreal.Name('RaftSimPhysicalGround') in a.tags)
    config=one(lambda a:a.get_class().get_name()=='RaftSimRiverWaterConfig')
    raft=one(lambda a:a.get_class().get_name()=='RaftSimRaftActor')
    if config.get_editor_property('cooked_fields_dir')!=FIELDS.relative_to(ROOT).as_posix():
        raise RuntimeError('Unexpected source hydraulics')
    if len([a for a in actors if isinstance(a,unreal.StaticMeshActor)])!=1:
        raise RuntimeError('Additional static geometry needs explicit geographic conversion')
    ground_rotation=ground.get_actor_rotation()
    if abs(ground_rotation.pitch)+abs(ground_rotation.yaw)+abs(ground_rotation.roll)>.0001:
        raise RuntimeError('Unexpected terrain rotation')
    scale=ground.get_actor_scale3d()
    if abs(scale.x-1)+abs(scale.y-1)+abs(scale.z-1)>.0001:
        raise RuntimeError('Unexpected terrain scale')
    ground.set_actor_scale3d(unreal.Vector(1,-1,1))
    changed=[]
    for actor in [ground,raft,*[a for a in actors if isinstance(a,unreal.PlayerStart)]]:
        old=actor.get_actor_location(); rot=actor.get_actor_rotation()
        actor.set_actor_location(unreal.Vector(old.x,-old.y,old.z),False,False)
        actor.set_actor_rotation(unreal.Rotator(pitch=rot.pitch,yaw=-rot.yaw,roll=-rot.roll),False)
        changed.append(dict(actor=actor.get_path_name(),old_cm=[old.x,old.y,old.z],new_cm=[old.x,-old.y,old.z]))
    config.set_editor_property('coordinate_map_path',MAP.relative_to(ROOT).as_posix())
    prior=json.loads((ROOT/'docs/reconstruction-review-2026-09-07/registered-rock-engine-integration.json').read_text())
    probes=[]
    for record in prior['collision_probes']:
        x,y,z=record['position_cm']; point=unreal.Vector(x,-y,z)
        hit=unreal.SystemLibrary.line_trace_single(world,point+unreal.Vector(0,0,1000),point-unreal.Vector(0,0,1000),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[a for a in actors if a!=ground],unreal.DrawDebugTrace.NONE,False)
        parts=hit.to_tuple() if hit is not None else None
        if parts is None or not parts[0]: raise RuntimeError('Mirrored terrain collision did not hit ground')
        impact=parts[5]; error=abs(impact.z-z)
        if error>.1: raise RuntimeError(f'Mirrored collision differs from source: {error} cm')
        probes.append(dict(position_cm=[x,-y,z],height_error_cm=error))
    if not levels.save_current_level(): raise RuntimeError('Geographic review save failed')
    if sha(BASE_FILE)!=EXPECTED_BASE: raise RuntimeError('Baseline changed during staging')
    report=dict(status='geographic_orientation_review_not_rapid_acceptance',level=LEVEL,
        coordinate_map_path=MAP.relative_to(ROOT).as_posix(),coordinate_map_sha256=sha(MAP),
        source_geometry_sha256=prior['source_geometry_sha256'],source_hydraulic_manifest_sha256=sha(FIELDS/'manifest.json'),
        baseline_map_unchanged=True,baseline_map_sha256=sha(BASE_FILE),
        captured_source_coordinates_unchanged=True,source_solver_arrays_unchanged=True,
        terrain_actor_scale=[1,-1,1],converted_actors=changed,collision_probes=probes,
        runtime_traversal_verified=False,visual_acceptance=False,production_promoted=False)
    (OUTPUT/'staging.json').write_text(json.dumps(report,indent=2)+'\n')
    unreal.log('Geographic scene staged with source-coincident reflected collision; full traversal remains unverified')


if __name__=='__main__':
    try: main()
    finally: unreal.SystemLibrary.quit_editor()
