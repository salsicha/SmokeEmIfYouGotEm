"""Install qualified full-corridor foliage into the continuous terrain candidate.

Uses native partitioned foliage/HISM, production meshes, bounded culling and
nonblocking instances. Only new foliage assets/actor packages are saved. The
original terrain/map packages are backed up and must remain byte-identical.
Normal L_Terminator, riverbed, water, raft and crew are never changed here.
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal

ROOT=Path(__file__).resolve().parents[2]
LEVEL='/Game/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1'
PLAN=ROOT/'tmp/futaleufu-continuous-canopy-v2/placement.json'
GROUND=ROOT/'tmp/futaleufu-continuous-canopy-grounding-v1/grounding.json'
MAP=ROOT/'unreal/Content/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1.umap'
OUT=ROOT/'tmp/futaleufu-continuous-canopy-install-v1'
ASSET_FOLDER='/Game/RaftSim/Environment/FutaleufuContinuous/Foliage'
ASSET_NAMES=('FT_ContinuousBroadleaf_A_V1','FT_ContinuousConifer_A_V1','FT_ContinuousUnderstory_A_V1')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def original_files():
    result=[MAP]
    for prefix in ('__ExternalActors__','__ExternalObjects__'):
        folder=ROOT/'unreal/Content'/prefix/'RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1'
        if folder.exists():result.extend(p for p in folder.rglob('*') if p.is_file())
    return result


def load_world(levels):
    if not levels.load_level(LEVEL):raise RuntimeError('Continuous map load failed')
    descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    if sum(isinstance(a,unreal.LandscapeStreamingProxy) for a in actors)!=800:
        raise RuntimeError('Incomplete native terrain residency')
    return actors


def foliage_components(actors,assets):
    result=[]
    for actor in actors:
        if not isinstance(actor,unreal.InstancedFoliageActor):continue
        if not actor.get_editor_property('is_spatially_loaded'):raise RuntimeError('Foliage must remain spatially loaded')
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh=component.static_mesh
            if mesh and mesh.get_path_name() in assets:result.append((actor,component,assets.index(mesh.get_path_name())))
    return result


def verify(actors,plan):
    assets=[m['asset'] for m in plan['meshes']];buckets={};expected=0
    for chunk in plan['chunks']:
        for row in chunk['instances']:
            x,y,_=row['location_cm'];key=(row['mesh'],math.floor(x/100),math.floor(y/100))
            buckets.setdefault(key,[]).append(row);expected+=1
    maximum=0.;count=0;per_mesh=[0,0,0];packages={}
    for actor,component,mesh in foliage_components(actors,assets):
        if component.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION:
            raise RuntimeError('Decorative canopy must not add boat collision')
        if component.get_editor_property('instance_start_cull_distance')!=45000 or component.get_editor_property('instance_end_cull_distance')!=65000:
            raise RuntimeError('Canopy culling contract changed')
        materials=[component.get_material(i).get_path_name() if component.get_material(i) else None for i in range(component.get_num_materials())]
        if materials!=plan['meshes'][mesh]['materials']:raise RuntimeError('Canopy appearance changed')
        package=actor.get_package()
        if '__ExternalActors__' not in package.get_name():raise RuntimeError('Expected external foliage package')
        packages[package.get_name()]=package
        for index in range(component.get_instance_count()):
            transform=component.get_instance_transform(index,True);v=transform.translation;s=transform.scale3d;q=transform.rotation
            x,y,z=float(v.x),float(v.y),float(v.z)
            yaw=math.degrees(math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)))
            found=None
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    key=(mesh,math.floor(x/100)+dx,math.floor(y/100)+dy)
                    for j,row in enumerate(buckets.get(key,())):
                        error=max(abs(a-b) for a,b in zip((x,y,z),row['location_cm']))
                        scale_error=max(abs(a-b) for a,b in zip((s.x,s.y,s.z),row['scale_xyz']))
                        yaw_error=abs((yaw-row['yaw_deg']+180)%360-180)
                        if error<=1. and scale_error<=1e-5 and yaw_error<=.001 and abs(q.x)<=1e-6 and abs(q.y)<=1e-6:
                            found=(key,j,error);break
                    if found:break
                if found:break
            if not found:raise RuntimeError('Native canopy transform has no matching qualified source placement')
            key,j,error=found;buckets[key].pop(j)
            count+=1;per_mesh[mesh]+=1;maximum=max(maximum,error)
    if count!=expected or any(buckets.values()) or per_mesh!=plan['instances_per_mesh']:
        raise RuntimeError('Missing, duplicated or misclassified canopy instances')
    return dict(verified_instances=count,instances_per_mesh=per_mesh,maximum_transform_error_cm=maximum,
        spatial_foliage_actors=len(packages),all_components_nonblocking=True),list(packages.values())


def main():
    if 'RaftSimInstallContinuousCanopy' not in unreal.SystemLibrary.get_command_line():
        raise RuntimeError('Explicit install flag required')
    plan=json.loads(PLAN.read_text());ground=json.loads(GROUND.read_text())
    if (not ground['all_roots_grounded'] or ground['native_root_probes']!=plan['instance_count']
            or ground['plan_sha256']!=sha(PLAN) or ground['map_sha256']!=sha(MAP)):
        raise RuntimeError('Native full-canopy grounding receipt required')
    for path,digest in plan['sources_sha256'].items():
        if sha(Path(path))!=digest:raise RuntimeError('Canopy source changed')
    if any(unreal.EditorAssetLibrary.does_asset_exist(ASSET_FOLDER+'/'+name) for name in ASSET_NAMES):
        raise RuntimeError('Fresh foliage type assets required; inspect any previous run')
    OUT.mkdir();before={str(p):sha(p) for p in original_files()}
    for path in before:
        source=Path(path);backup=OUT/'backup'/source.relative_to(ROOT/'unreal/Content')
        backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,backup)
        if sha(backup)!=before[path]:raise RuntimeError('Candidate backup failed')
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=load_world(levels)
    if any(isinstance(a,unreal.InstancedFoliageActor) for a in actors):
        raise RuntimeError('Candidate already has foliage; no duplicate installation')
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    types=[];asset_tools=unreal.AssetToolsHelpers.get_asset_tools()
    for name,row in zip(ASSET_NAMES,plan['meshes']):
        asset_path=ROOT/'unreal/Content'/Path(row['asset'].split('.')[0].removeprefix('/Game/')).with_suffix('.uasset')
        if sha(asset_path)!=row['asset_sha256']:raise RuntimeError('Production mesh changed')
        foliage=asset_tools.create_asset(name,ASSET_FOLDER,unreal.FoliageType_InstancedStaticMesh,
            unreal.FoliageType_InstancedStaticMeshFactory())
        if not foliage:raise RuntimeError('Foliage type creation failed')
        foliage.set_editor_property('mesh',unreal.load_asset(row['asset']))
        foliage.set_editor_property('override_materials',[unreal.load_asset(m) for m in row['materials']])
        foliage.set_editor_property('cull_distance',unreal.Int32Interval(min=45000,max=65000))
        foliage.set_editor_property('enable_density_scaling',False)
        foliage.set_editor_property('cast_shadow',True)
        body=foliage.get_editor_property('body_instance');body.set_editor_property('collision_enabled',unreal.CollisionEnabled.NO_COLLISION)
        body.set_editor_property('collision_profile_name','NoCollision');foliage.set_editor_property('body_instance',body)
        types.append(foliage)
    inserted=0
    for chunk in plan['chunks']:
        for mesh,foliage in enumerate(types):
            transforms=[unreal.Transform(location=unreal.Vector(*r['location_cm']),
                rotation=unreal.Rotator(pitch=0,yaw=r['yaw_deg'],roll=0),scale=unreal.Vector(*r['scale_xyz']))
                for r in chunk['instances'] if r['mesh']==mesh]
            if transforms:unreal.InstancedFoliageActor.add_instances(world,foliage,transforms)
            inserted+=len(transforms)
        if inserted//10000!=(inserted-len(chunk['instances']))//10000:unreal.log('Continuous canopy inserted: '+str(inserted))
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    for _,component,_ in foliage_components(actors,[m['asset'] for m in plan['meshes']]):
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_editor_property('can_ever_affect_navigation',False)
        component.set_cull_distances(45000,65000)
    initial,packages=verify(actors,plan)
    if not all(sha(Path(p))==h for p,h in before.items()):raise RuntimeError('Original terrain package changed before save')
    packages.extend(f.get_package() for f in types)
    if not unreal.EditorLoadingAndSavingUtils.save_packages(packages,False):raise RuntimeError('Targeted foliage package save failed')
    if not all(sha(Path(p))==h for p,h in before.items()):raise RuntimeError('Original terrain package changed during foliage save')
    levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank');unreal.SystemLibrary.collect_garbage()
    reloaded=load_world(levels);after,_=verify(reloaded,plan)
    if not all(sha(Path(p))==h for p,h in before.items()):raise RuntimeError('Original terrain package changed after reload')
    result=dict(schema='raftsim.futaleufu_continuous_canopy_install.v1',level=LEVEL,plan_sha256=sha(PLAN),
        grounding_receipt_sha256=sha(GROUND),**after,original_terrain_packages_unchanged=len(before),
        asset_packages=[f.get_path_name() for f in types],rendered_acceptance=False,packaged_performance_acceptance=False,
        normal_playable_map_modified=False,water_or_terrain_modified=False)
    with (OUT/'integration.json').open('x') as f:json.dump(result,f,indent=2)
    unreal.log('Continuous canopy saved and reloaded: '+json.dumps(result))
    levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank');unreal.SystemLibrary.collect_garbage()


if OUT.exists():raise RuntimeError('Fresh installation output required; previous evidence preserved')
try:main()
except Exception:
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'failure.txt').write_text(traceback.format_exc());raise
finally:unreal.SystemLibrary.quit_editor()
