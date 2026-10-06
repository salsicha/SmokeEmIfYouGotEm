"""Read-only distinguish canopy registration from editor collision readiness."""
import json
from pathlib import Path
import unreal
ROOT = Path(__file__).resolve().parents[2]
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/RaftSim/Maps/L_SouthFork_Troublemaker')
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
ground = next(a for a in actors if unreal.Name('RaftSimPhysicalGround') in a.tags)
component = ground.static_mesh_component
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
canopy = json.loads((ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_canopy.json').read_text())
prior = json.loads((ROOT/'docs/reconstruction-review-2026-09-07/geographic-scene/staging.json').read_text())
points = [i['location_cm'] for i in canopy['instances'][:4]]+[i['position_cm'] for i in prior['collision_probes'][:4]]
hits = []
for x,y,z in points:
    record = {'source_cm':[x,y,z]}
    for key,from_z,to_z in [('short',z+100,z-100),('long',z+10000,z-10000),('up',z-10000,z+10000)]:
        hit = unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,from_z),unreal.Vector(x,y,to_z),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[a for a in actors if a != ground],unreal.DrawDebugTrace.NONE,False)
        record[key] = str(hit.to_tuple() if hit else None)
    hits.append(record)
record = {'collision_enabled':str(component.get_collision_enabled()),'profile':str(component.get_collision_profile_name()),
          'actor_collision':ground.get_actor_enable_collision(), 'mesh':component.static_mesh.get_path_name(),
          'body':str(component.static_mesh.get_editor_property('body_setup')), 'hits':hits}
output=ROOT/'unreal/Saved/RaftSimValidation/troublemaker-canopy-ground-diagnosis-20260912.json'
output.write_text(json.dumps(record,indent=2)+'\n')
unreal.log(str(record))
