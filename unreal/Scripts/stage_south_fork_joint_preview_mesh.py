"""Stage only a regenerable local preview mesh with the retained world material."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from verify_troublemaker_dem_rock_cap_collision import import_candidate_solid,EXPORT as DEFAULT_EXPORT

DEST='/Game/RaftSim/Environment/GeneratedLocalReview/JointSouthFork20260915/SM_OriginalReturnRockSolid'
MATERIAL='/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/MI_SouthForkCompositeGround'
REPORT=ROOT/'tmp/south-fork-rock-union-render-stage-v1-20260915.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def asset_file(path):return ROOT/'unreal/Content'/(path.removeprefix('/Game/').split('.')[0]+'.uasset')


def stage_configuration(path,root=ROOT):
    """Only fresh regenerable local assets; material selection is not overridden."""
    root=Path(root).resolve();raw=json.loads(Path(path).read_text())
    config={key:(root/raw[key]).resolve() for key in ('export_directory','collision_audit','report')}
    if not config['export_directory'].is_relative_to(root/'tmp') or not (config['export_directory']/'manifest.json').is_file():
        raise ValueError('Existing generated export required')
    if not config['collision_audit'].is_relative_to(root/'unreal/Saved/RaftSimValidation') or not config['collision_audit'].is_file():
        raise ValueError('Existing local native collision/runtime audit required')
    if not config['report'].is_relative_to(root/'tmp') or config['report'].exists():
        raise ValueError('Fresh project tmp staging report required')
    for key in ('destination','import_asset'):
        asset=raw[key]
        if not asset.startswith('/Game/RaftSim/Environment/GeneratedLocalReview/') or any(
                not part or not part.replace('_','').isalnum() for part in asset[1:].split('/')):
            raise ValueError('Only regenerable local-review asset paths allowed')
        config[key]=asset
    if config['destination']==config['import_asset']:
        raise ValueError('Separate import and staged asset required')
    return config


def validate_stage_evidence(export,collision):
    if collision.get('sampled_full_map_union_verified') is not True or collision.get('failures')!=[]:
        raise ValueError('Actual map-union collision evidence failed')
    runtime=collision.get('native_runtime')
    if not runtime or runtime.get('field_queries_verified') is not True or isinstance(runtime.get('query_count'),bool) or not isinstance(runtime.get('query_count'),int) or runtime['query_count']<=0:
        raise ValueError('Native field-query evidence required before staging')
    if export['source_cap_sha256']!=collision['source_cap_sha256'] or export['fbx_sha256']!=collision['fbx_sha256']:
        raise ValueError('Render and collision source solid differ')
    count=export['triangle_count']
    if isinstance(count,bool) or not isinstance(count,int) or count<=0:
        raise ValueError('Explicit positive integer source triangle count required')
    return count


def main():
    config_path=os.environ.get('RAFTSIM_JOINT_MESH_STAGE_CONFIG')
    config=stage_configuration(config_path) if config_path else dict(export_directory=None,import_asset=None,
        destination=DEST,report=REPORT,
        collision_audit=ROOT/'unreal/Saved/RaftSimValidation/south-fork-rock-union-runtime-v2-20260915.json')
    destination,report=config['destination'],config['report']
    assert not report.exists() and not unreal.EditorAssetLibrary.does_asset_exist(destination)
    collision_path=config['collision_audit']
    collision=json.loads(collision_path.read_text())
    # Refuse missing native proof before importing or saving anything.
    export_directory=config['export_directory'] or DEFAULT_EXPORT
    export_evidence=json.loads((export_directory/'manifest.json').read_text())
    expected_triangles=validate_stage_evidence(export_evidence,collision)
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
    mesh,export=import_candidate_solid(config['export_directory'],config['import_asset'])
    assert validate_stage_evidence(export,collision)==expected_triangles
    staged=unreal.EditorAssetLibrary.duplicate_asset(mesh.get_path_name().split('.')[0],destination)
    assert isinstance(staged,unreal.StaticMesh)
    staged.set_material(0,material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert staged.get_num_triangles(0)==expected_triangles
    assert staged.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    assert unreal.EditorAssetLibrary.save_loaded_asset(staged,only_if_is_dirty=False)
    for asset,digest in before.items():assert sha(asset_file(asset))==digest
    report.write_text(json.dumps(dict(mesh_asset=staged.get_path_name(),mesh_file=asset_file(destination).relative_to(ROOT).as_posix(),
        mesh_sha256=sha(asset_file(destination)),material_asset=material.get_path_name(),material_package=MATERIAL,
        material_sha256=before[MATERIAL],parent_material=parent_path,parent_material_sha256=before[parent_path],
        source_cap_sha256=export['source_cap_sha256'],fbx_sha256=export['fbx_sha256'],
        collision_report_sha256=sha(collision_path),translation_cm=translation,scale=[1,-1,1],
        triangle_count=expected_triangles,world_projected_source_uv_expressions=uv_codes,world_position_offset=False,
        original_materials_unchanged=True,only_regenerable_local_asset_saved=True,
        production_promoted=False,playable_integrated=False,visual_accepted=False),indent=2)+'\n')
    unreal.log('Local joint-preview mesh staged: '+str(report))


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
