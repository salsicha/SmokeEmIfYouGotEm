"""Fresh-load the delivered ground and water, preserving physics and source identity."""
import hashlib
import json
from pathlib import Path
import sys
import unreal
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import audit_playable_troublemaker_foam
import audit_south_fork_playable_package
from configure_playable_troublemaker_foam import graph_signature
data=json.loads((ROOT/'unreal/Saved/RaftSimValidation/troublemaker-surface-color-20260912.json').read_text())
lib=unreal.MaterialEditingLibrary
mat=unreal.load_asset(data['material']);instance=unreal.load_asset(data['instance'])
assert instance.get_editor_property('parent')==mat
if 'bank_color_review' in data:
    asset=ROOT/('unreal/Content/'+data['material'].removeprefix('/Game/')+'.uasset')
    assert hashlib.sha256(asset.read_bytes()).hexdigest()==data['bank_color_review']['after_sha256']
for prop,signature in data['protected_graphs'].items():
    assert graph_signature(mat,getattr(unreal.MaterialProperty,'MP_'+prop))==signature,prop
root=lib.get_material_property_input_node(mat,unreal.MaterialProperty.MP_BASE_COLOR)
assert str(root.get_editor_property('description'))=='Registered captured bank color V1'
from verify_troublemaker_surface_history import verify_protected_assets
terrain_revision=verify_protected_assets(data['protected_assets'])
fields=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_flow'
delivery=json.loads((fields/'delivery.json').read_text())
for name,digest in delivery['files'].items():
    assert hashlib.sha256((fields/name).read_bytes()).hexdigest()==digest,name
if terrain_revision:
    assert delivery['source_geometry_sha256']==terrain_revision['source_geometry_sha256']
    texture=ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/T_TroublemakerSurfaceAuthority.uasset'
    assert hashlib.sha256(texture.read_bytes()).hexdigest()==terrain_revision['authority_texture_sha256']
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(data['normal_playable_map'])
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    ground=[a for a in actors if isinstance(a,unreal.StaticMeshActor) and unreal.Name('RaftSimPhysicalGround') in a.tags]
    assert len(ground)==1 and ground[0].static_mesh_component.static_mesh.get_path_name().split('.')[0]==terrain_revision['mesh']
    config=[a for a in actors if a.get_class().get_name()=='RaftSimRiverWaterConfig']
    assert len(config)==1 and config[0].get_editor_property('cooked_fields_dir')==fields.relative_to(ROOT).as_posix()
out=ROOT/'unreal/Saved/RaftSimValidation/troublemaker-playable-surfaces-fresh-20260912.json'
out.write_text(json.dumps({'passed':True,'ground':data['material'],'normal_playable_map':data['normal_playable_map'],
    'terrain_collision_flow_unchanged':not bool(terrain_revision),'explicit_matched_terrain_revision_verified':bool(terrain_revision),'ground_normals_roughness_wpo_unchanged':True,
    'water_froth_graph_verified':True,'packaged_release_or_realism_accepted':False},indent=2)+'\n')
unreal.log(f'Fresh playable surfaces verified: {out}')
