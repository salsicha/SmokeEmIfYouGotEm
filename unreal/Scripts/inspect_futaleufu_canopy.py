"""Read-only inventory before correcting saved-map canopy registration."""
import hashlib,json,os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LEVEL='/Game/RaftSim/Maps/L_Terminator'

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def xyz(v):return [float(v.x),float(v.y),float(v.z)]

def main():
    import unreal
    output=(ROOT/os.environ['RAFTSIM_CANOPY_INVENTORY']).resolve()
    output.relative_to(ROOT/'tmp')
    if output.exists():raise ValueError('Fresh inventory required')
    path=ROOT/'unreal/Content/RaftSim/Maps/L_Terminator.umap';before=sha(path)
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):raise RuntimeError('Map load failed')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    # This existing map is non-partitioned; the API returns None there.
    # Its actors are already loaded, while partitioned successors need descs.
    descriptions=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    wanted=[d.guid for d in descriptions if 'FutaleufuEvidence' in str(d.label) or 'FutaleufuEvidence' in str(d.name)]
    if wanted:unreal.WorldPartitionBlueprintLibrary.load_actors(wanted)
    found=[];other=[]
    for actor in actors.get_all_level_actors():
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            name=component.get_name();tags=[str(t) for t in actor.tags]
            row=dict(actor=actor.get_name(),label=actor.get_actor_label(),component=name,tags=tags,
                count=component.get_instance_count(),mesh=component.static_mesh.get_path_name() if component.static_mesh else None)
            if 'FutaleufuEvidence' not in name and 'RaftSimFutaleufuEvidenceCanopy' not in tags:
                other.append(row);continue
            mesh=component.static_mesh
            row.update(actor_location_cm=xyz(actor.get_actor_location()),actor_scale=xyz(actor.get_actor_scale3d()),
                component_transform=str(component.get_world_transform()),collision=str(component.get_collision_enabled()),
                materials=[component.get_material(i).get_path_name() if component.get_material(i) else None for i in range(component.get_num_materials())],
                bounds=dict(min=xyz(mesh.get_bounding_box().min),max=xyz(mesh.get_bounding_box().max)) if mesh else None,
                instances=[])
            for i in range(component.get_instance_count()):
                transform=component.get_instance_transform(i,world_space=True)
                row['instances'].append(dict(location_cm=xyz(transform.translation),scale=xyz(transform.scale3d),rotation=str(transform.rotation)))
            found.append(row)
    if not found:raise RuntimeError('No existing evidence canopy found; no mutation permitted')
    if sha(path)!=before:raise RuntimeError('Map changed during read-only inventory')
    result=dict(schema='raftsim.futaleufu_saved_canopy_inventory.v1',level=LEVEL,map_sha256=before,
        map_unchanged=True,saved_anything=False,canopy=found,other_instanced_components=other,
        total_evidence_instances=sum(r['count'] for r in found))
    with output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    unreal.log('Read-only Futaleufu canopy inventory: '+str(result['total_evidence_instances']))
    levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank')
    unreal.SystemLibrary.collect_garbage()

if __name__=='__main__':
    import unreal
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
