"""Stage only a regenerable local preview mesh with the retained world material."""
import hashlib
import json
from pathlib import Path
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from verify_troublemaker_dem_rock_cap_collision import import_candidate_solid

DEST='/Game/RaftSim/Environment/GeneratedLocalReview/JointSouthFork20260915/SM_OriginalReturnRockSolid'
MATERIAL='/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/MI_SouthForkCompositeGround'
REPORT=ROOT/'tmp/south-fork-rock-union-render-stage-v1-20260915.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def asset_file(path):return ROOT/'unreal/Content'/(path.removeprefix('/Game/').split('.')[0]+'.uasset')


def main():
    assert not REPORT.exists() and not unreal.EditorAssetLibrary.does_asset_exist(DEST)
    collision_path=ROOT/'unreal/Saved/RaftSimValidation/south-fork-rock-union-runtime-v2-20260915.json'
    collision=json.loads(collision_path.read_text())
    assert collision['sampled_full_map_union_verified'] and collision['native_runtime']['field_queries_verified']
    material=unreal.load_asset(MATERIAL);assert isinstance(material,unreal.MaterialInstanceConstant)
    parent=material.get_editor_property('parent');assert isinstance(parent,unreal.Material)
    parent_path=parent.get_path_name().split('.')[0]
    before={MATERIAL:sha(asset_file(MATERIAL)),parent_path:sha(asset_file(parent_path))}
    lib=unreal.MaterialEditingLibrary
    assert lib.get_material_property_input_node(parent,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET) is None
    uv_nodes=[n for n in lib.get_material_expressions(parent) if isinstance(n,unreal.MaterialExpressionCustom)
        and str(n.get_editor_property('description'))=='Full river world to retained rapid source frame']
    assert len(uv_nodes)==2
    translation=collision['candidate_translation_cm']
    prefix=f'P -= float3({translation[0]:.12f}, {translation[1]:.12f}, 0.0);'
    uv_codes=[str(n.get_editor_property('code')) for n in uv_nodes]
    assert all(code.startswith(prefix) for code in uv_codes)
    mesh,export=import_candidate_solid()
    assert export['source_cap_sha256']==collision['source_cap_sha256'] and export['fbx_sha256']==collision['fbx_sha256']
    staged=unreal.EditorAssetLibrary.duplicate_asset(mesh.get_path_name().split('.')[0],DEST)
    assert isinstance(staged,unreal.StaticMesh)
    staged.set_material(0,material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert staged.get_num_triangles(0)==export['triangle_count']==2192
    assert staged.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    assert unreal.EditorAssetLibrary.save_loaded_asset(staged,only_if_is_dirty=False)
    for asset,digest in before.items():assert sha(asset_file(asset))==digest
    REPORT.write_text(json.dumps(dict(mesh_asset=staged.get_path_name(),mesh_file=asset_file(DEST).relative_to(ROOT).as_posix(),
        mesh_sha256=sha(asset_file(DEST)),material_asset=material.get_path_name(),material_package=MATERIAL,
        material_sha256=before[MATERIAL],parent_material=parent_path,parent_material_sha256=before[parent_path],
        source_cap_sha256=export['source_cap_sha256'],fbx_sha256=export['fbx_sha256'],
        collision_report_sha256=sha(collision_path),translation_cm=translation,scale=[1,-1,1],
        triangle_count=2192,world_projected_source_uv_expressions=uv_codes,world_position_offset=False,
        original_materials_unchanged=True,only_regenerable_local_asset_saved=True,
        production_promoted=False,playable_integrated=False,visual_accepted=False),indent=2)+'\n')
    unreal.log('Local joint-preview mesh staged: '+str(REPORT))


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
