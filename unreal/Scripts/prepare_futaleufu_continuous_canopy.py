"""Read-only native qualification of continuous canopy roots and production meshes.

Loads all 800 saved terrain proxies, checks every proposed plant against actual
Landscape collision, and saves only a diagnostic receipt. No world/asset save.
"""
import hashlib,json,math,os,traceback
from pathlib import Path
import unreal

ROOT=Path(__file__).resolve().parents[2]
LEVEL='/Game/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1'
PLAN=ROOT/'tmp/futaleufu-continuous-canopy-v2/placement.json'
MAP=ROOT/'unreal/Content/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1.umap'
OUT=ROOT/'tmp/futaleufu-continuous-canopy-grounding-v1'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def xyz(value):return [float(value.x),float(value.y),float(value.z)]


def main():
    if OUT.exists():raise RuntimeError('Fresh native qualification required')
    OUT.mkdir()
    pinned={str(p):sha(p) for p in (PLAN,MAP)}
    plan=json.loads(PLAN.read_text())
    if (plan['schema']!='raftsim.futaleufu_continuous_canopy.v1' or plan['terrain_modified']
            or plan['collision_enabled'] or plan['native_grounding_verified']):
        raise RuntimeError('Expected nonphysical unqualified continuous canopy plan')
    if plan['terrain_manifest_sha256']!=sha(ROOT/'tmp/futaleufu-context-terrain-v1/manifest.json'):
        raise RuntimeError('Plan terrain changed')
    for path,digest in plan['sources_sha256'].items():
        if sha(Path(path))!=digest:raise RuntimeError('Plan source changed: '+path)
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):raise RuntimeError('Native continuous terrain load failed')
    descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    ground=[a for a in actors if isinstance(a,unreal.LandscapeStreamingProxy)]
    if len(ground)!=800:raise RuntimeError('All actual terrain proxies must be resident')
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    meshes=[]
    for row in plan['meshes']:
        path=ROOT/'unreal/Content'/Path(row['asset'].split('.')[0].removeprefix('/Game/')).with_suffix('.uasset')
        if sha(path)!=row['asset_sha256']:raise RuntimeError('Production canopy mesh changed')
        mesh=unreal.load_asset(row['asset'])
        if not mesh:raise RuntimeError('Missing production canopy mesh')
        bounds=mesh.get_bounding_box()
        actual=dict(min=xyz(bounds.min),max=xyz(bounds.max))
        if any(abs(a-b)>.0001 for key in ('min','max') for a,b in zip(actual[key],row['bounds'][key])):
            raise RuntimeError('Native mesh dimensions differ from plan')
        materials=[m.material_interface.get_path_name() if m.material_interface else None
                   for m in mesh.get_editor_property('static_materials')]
        if materials!=row['materials']:raise RuntimeError('Native canopy material differs from inspected production material')
        meshes.append(actual)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ignore=[a for a in actors if not isinstance(a,unreal.LandscapeProxy)]
    count=0;maximum=0.;missing=[];chunks=[]
    for chunk in plan['chunks']:
        local=0.;failed=0
        for row in chunk['instances']:
            x,y,z=row['location_cm'];mesh=int(row['mesh']);scale=row['scale_xyz']
            if (not all(math.isfinite(v) for v in [x,y,z,*scale,row['ground_cm']])
                    or not 0<=mesh<len(meshes) or min(scale)<=0
                    or row['source_water_clearance_m']<max(12.,row['crown_bound_radius_m']+8.)):
                raise RuntimeError('Invalid canopy transform or source water clearance')
            hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,1000000),unreal.Vector(x,y,-1000000),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,unreal.DrawDebugTrace.NONE,False)
            values=hit.to_tuple() if hit else None
            if not values or not values[0]:
                failed+=1;missing.append(dict(chunk=chunk['chunk'],xy_cm=[x,y]));continue
            ground_z=float(values[5].z)
            buried=20. if mesh==2 else 30.
            error=max(abs(ground_z-row['ground_cm']),abs(z+meshes[mesh]['min'][2]*scale[2]-(ground_z-buried)))
            if not math.isfinite(error):raise RuntimeError('Nonfinite native ground')
            local=max(local,error);maximum=max(maximum,error);count+=1
            if count%8192==0:unreal.log('Continuous canopy native roots checked: '+str(count))
        chunks.append(dict(chunk=chunk['chunk'],expected=len(chunk['instances']),missing=failed,maximum_root_error_cm=local))
    stable=all(sha(Path(path))==digest for path,digest in pinned.items())
    result=dict(schema='raftsim.futaleufu_continuous_canopy_grounding.v1',level=LEVEL,
        plan_sha256=pinned[str(PLAN)],map_sha256=pinned[str(MAP)],native_landscape_proxies=800,
        expected_instances=plan['instance_count'],native_root_probes=count,maximum_root_ground_error_cm=maximum,
        missing_ground=missing,chunks=chunks,pinned_unchanged=stable,
        all_roots_grounded=not missing and count==plan['instance_count'] and maximum<=1.,
        saved_map_or_assets=False,rendered_acceptance=False,packaged_performance_acceptance=False)
    with (OUT/'grounding.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    if not stable or not result['all_roots_grounded']:raise RuntimeError('Native continuous canopy grounding failed; inspect receipt')
    unreal.log('Continuous canopy grounding passed: '+str(count)+' roots; maximum error cm='+str(maximum))
    levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank');unreal.SystemLibrary.collect_garbage()


if OUT.exists():raise RuntimeError('Fresh native qualification required; existing evidence preserved')
try:main()
except Exception:
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'failure.txt').write_text(traceback.format_exc());raise
finally:unreal.SystemLibrary.quit_editor()
