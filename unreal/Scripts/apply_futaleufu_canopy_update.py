"""Apply the native-grounded source-registration repair to L_Terminator only.

Requires explicit command flag and fresh output directory. Preserves the three
existing component assets/settings and every unrelated actor/instance. Backs up
the original map before any mutation, saves, reloads, verifies all transforms,
and probes native root collision again. No terrain, water, raft or crew edits.
Rendered and packaged performance acceptance are separate required checks.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from inspect_futaleufu_canopy import ROOT, LEVEL, sha, xyz

PLAN=ROOT/'tmp/futaleufu-canopy-grounding-native-v1/grounding.json'
PLAN_SHA='d1203f8dcdbc857d9c65af73a4d98fd2b1001c94a65e19a16a52f020eb8dfeb9'
MAP=ROOT/'unreal/Content/RaftSim/Maps/L_Terminator.umap'
MAP_SHA='d52f78659fa50d9a8fc930bae477400192e41cfd4ba12148067b5e0c4fb9a882'


def numbers(transform):
    q=transform.rotation
    return [*xyz(transform.translation),*xyz(transform.scale3d),q.x,q.y,q.z,q.w]


def snapshot(actors,targets):
    import unreal
    result=[]
    for actor in actors.get_all_level_actors():
        row=dict(name=actor.get_name(),type=actor.get_class().get_path_name(),
                 transform=numbers(actor.get_actor_transform()),tags=sorted(str(t) for t in actor.tags),components=[])
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            item=dict(name=component.get_name(),mesh=component.static_mesh.get_path_name() if component.static_mesh else None,
                      transform=numbers(component.get_world_transform()),collision=str(component.get_collision_enabled()),
                      materials=[component.get_material(i).get_path_name() if component.get_material(i) else None
                                 for i in range(component.get_num_materials())])
            if isinstance(component,unreal.InstancedStaticMeshComponent) and component.get_name() not in targets:
                digest=hashlib.sha256()
                item['count']=component.get_instance_count()
                for index in range(item['count']):
                    digest.update(struct.pack('<10d',*numbers(component.get_instance_transform(index,True))))
                item['instances_sha256']=digest.hexdigest()
            row['components'].append(item)
        row['components'].sort(key=lambda c:c['name']);result.append(row)
    result.sort(key=lambda a:a['name'])
    return result


def components(actors,plan):
    import unreal
    result={}
    for key,row in plan['components'].items():
        actor=next(a for a in actors.get_all_level_actors() if a.get_name()==row['actor'])
        component=next(c for c in actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
                       if c.get_name()==row['component'])
        if component.static_mesh.get_path_name()!=row['mesh'] or component.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION:
            raise RuntimeError('Canopy component asset/collision changed')
        materials=[component.get_material(i).get_path_name() if component.get_material(i) else None
                   for i in range(component.get_num_materials())]
        if materials!=row['materials']:raise RuntimeError('Canopy materials changed')
        result[key]=(actor,component)
    return result


def verify(actors,plan):
    maximum=0.;count=0
    for key,(_,component) in components(actors,plan).items():
        expected=plan['components'][key]['transforms']
        if component.get_instance_count()!=len(expected):raise RuntimeError('Saved instance count mismatch')
        for index,row in enumerate(expected):
            t=component.get_instance_transform(index,True)
            error=max(abs(a-b) for a,b in zip([*xyz(t.translation),*xyz(t.scale3d)],
                                             [*row['location_cm'],*row['scale']]))
            q=t.rotation
            if abs(q.x)>1e-6 or abs(q.y)>1e-6:raise RuntimeError('Unexpected canopy tilt')
            yaw=math.degrees(math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)))
            yaw_error=abs((yaw-row['yaw_degrees']+180)%360-180)
            if not math.isfinite(error+yaw_error) or error>.1 or yaw_error>.001:
                raise RuntimeError('Saved instance transform mismatch: '+str((key,index,error,yaw_error)))
            maximum=max(maximum,error);count+=1
    return dict(verified_instances=count,maximum_transform_error_cm=maximum)


def main():
    import unreal
    if 'RaftSimApplyFutaleufuCanopy' not in unreal.SystemLibrary.get_command_line():
        raise RuntimeError('Explicit apply flag required')
    output=(ROOT/os.environ['RAFTSIM_CANOPY_APPLY_DIR']).resolve();output.relative_to(ROOT/'tmp')
    backup=output/'L_Terminator.before.umap';report=output/'integration.json'
    if backup.exists() or report.exists():raise RuntimeError('Fresh integration required')
    if sha(PLAN)!=PLAN_SHA or sha(MAP)!=MAP_SHA:raise RuntimeError('Plan or saved map changed')
    plan=json.loads(PLAN.read_text())
    if not plan['all_roots_grounded'] or plan['traced']!=55344 or plan['map_sha256']!=MAP_SHA:
        raise RuntimeError('Native grounding proof incomplete')
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):raise RuntimeError('Map load failed')
    if unreal.WorldPartitionBlueprintLibrary.get_actor_descs():raise RuntimeError('Unexpected partitioned map')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    target_names={row['component'] for row in plan['components'].values()}
    before=snapshot(actors,target_names)
    current=components(actors,plan)
    original_count=sum(c.get_instance_count() for _,c in current.values())
    if original_count!=55383:raise RuntimeError('Installed vegetation count changed')
    shutil.copy2(MAP,backup)
    if sha(backup)!=MAP_SHA:raise RuntimeError('Backup verification failed')
    for key,(actor,component) in current.items():
        actor.modify();component.modify()
        transforms=[unreal.Transform(location=unreal.Vector(*row['location_cm']),
                                     rotation=unreal.Rotator(pitch=0,yaw=row['yaw_degrees'],roll=0),
                                     scale=unreal.Vector(*row['scale'])) for row in plan['components'][key]['transforms']]
        component.clear_instances()
        component.add_instances(transforms,False,True)
    initial=verify(actors,plan)
    if snapshot(actors,target_names)!=before:raise RuntimeError('Unrelated actor/component changed before save')
    if not levels.save_current_level():raise RuntimeError('Map save failed')
    if not levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank'):raise RuntimeError('Unload failed')
    unreal.SystemLibrary.collect_garbage()
    if not levels.load_level(LEVEL):raise RuntimeError('Reload failed')
    after=verify(actors,plan)
    if snapshot(actors,target_names)!=before:raise RuntimeError('Unrelated actor/component changed after reload')
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    loaded=actors.get_all_level_actors()
    ignore=[a for a in loaded if not isinstance(a,unreal.LandscapeProxy)]
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    root_error=0.;probes=0
    for row in plan['components'].values():
        # Uniform deterministic saved-component sample plus both endpoints.
        entries=row['transforms'];indices=sorted(set([0,len(entries)-1,*range(0,len(entries),max(1,len(entries)//512))]))
        for index in indices:
            expected=entries[index];x,y,z=expected['location_cm']
            hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,1000000),unreal.Vector(x,y,-1000000),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,unreal.DrawDebugTrace.NONE,False)
            values=hit.to_tuple() if hit else None
            if not values or not values[0]:raise RuntimeError('Reloaded native root support missing')
            delta=abs(float(values[5].z)-expected['ground_cm'])
            if delta>.1:raise RuntimeError('Native ground changed after canopy save')
            root_error=max(root_error,delta);probes+=1
    if sha(PLAN)!=PLAN_SHA:raise RuntimeError('Plan changed during integration')
    result=dict(schema='raftsim.futaleufu_native_canopy_integration.v1',level=LEVEL,
        previous_map_sha256=MAP_SHA,map_sha256=sha(MAP),plan_sha256=PLAN_SHA,
        backup=str(backup.relative_to(ROOT)),original_instances=original_count,**after,
        original_actors_and_unrelated_instances_unchanged=True,
        actor_count=len(before),post_reload_root_probes=probes,maximum_root_ground_error_cm=root_error,
        source_placement_sha256=plan['source_sha256'],terrain_or_water_modified=False,
        rendered_acceptance=False,packaged_performance_acceptance=False)
    with report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    unreal.log('Futaleufu canopy integrated and reloaded: '+json.dumps(result))
    levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank');unreal.SystemLibrary.collect_garbage()


if __name__=='__main__':
    import unreal
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
