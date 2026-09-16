import copy
import hashlib
import json

import pytest

from refresh_south_fork_joint_preview_stage import refresh


def fixture(root):
    def save(name, data):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return hashlib.sha256(data).hexdigest()
    asset = '/Game/Test/Ground'
    mesh = save('unreal/Content/Test/Ground.uasset', b'CPU retained')
    mat = save('unreal/Content/Test/Material.uasset', b'material')
    parent = save('unreal/Content/Test/Parent.uasset', b'parent')
    before = dict(format='native_v1', collision_lod=0, collision_trace_flag=3,
                  collision_source_sha256='b'*64, triangle_count=12,
                  provider_vertex_count=24, flip_normals=True, available=True, allow_cpu_access=False)
    row = dict(asset=asset, original_asset_sha256='a'*64, retained_asset_sha256=mesh,
               before=before, after=dict(before, allow_cpu_access=True), native_source_unchanged=True,
               material_paths=['/Game/Test/Material.Material'])
    receipt = dict(schema='raftsim.ground_cpu_retention.v1', completed=True, assets=[row])
    stage = dict(mesh_asset=asset+'.Ground', mesh_file='unreal/Content/Test/Ground.uasset',
                 mesh_sha256='a'*64, material_asset='/Game/Test/Material.Material', material_sha256=mat,
                 parent_material='/Game/Test/Parent', parent_material_sha256=parent,
                 world_position_offset=False, original_materials_unchanged=True, triangle_count=12,
                 source_cap_sha256='c'*64, fbx_sha256='d'*64, translation_cm=[1,2,0], scale=[1,-1,1],
                 collision_report_sha256='e'*64, production_promoted=False, visual_accepted=False)
    collision = dict(saved_candidate_verified=True, saved_candidate_asset=asset, saved_candidate_sha256=mesh,
                     saved_candidate_source_sha256='b'*64, failures=[], sampled_full_map_union_verified=True,
                     native_runtime=dict(field_queries_verified=True), saved_assets=False, saved_levels=False,
                     water_state_modified=False, source_cap_sha256='c'*64, fbx_sha256='d'*64,
                     candidate_translation_cm=[1,2,0])
    return stage, collision, receipt


def run(root, stage, collision, receipt):
    for name, data in [('stage', stage), ('collision', collision), ('receipt', receipt)]:
        (root / (name+'.json')).write_text(json.dumps(data))
    return refresh(root/'stage.json', root/'collision.json', root=root, receipt=root/'receipt.json')


def test_preserves_history_and_only_rebinds_proven_revision(tmp_path):
    stage, collision, receipt = fixture(tmp_path)
    original = copy.deepcopy(stage)
    result = run(tmp_path, stage, collision, receipt)
    assert json.loads((tmp_path/'stage.json').read_text()) == original
    assert result['mesh_sha256'] == collision['saved_candidate_sha256']
    assert result['production_promoted'] is False and result['visual_accepted'] is False
    assert result['cpu_retention_rebind']['original_stage_sha256'] == hashlib.sha256((tmp_path/'stage.json').read_bytes()).hexdigest()
    for key in ('translation_cm','scale','triangle_count','source_cap_sha256','fbx_sha256'):
        assert result[key] == original[key]


@pytest.mark.parametrize('case', ['native_package','native_source','geometry','transform','material',
                                  'receipt','source_changed','native_failed','water_changed','material_bytes'])
def test_refuses_unproven_changes(tmp_path, case):
    stage, collision, receipt = fixture(tmp_path)
    if case == 'native_package': collision['saved_candidate_sha256'] = 'f'*64
    if case == 'native_source': collision['saved_candidate_source_sha256'] = 'f'*64
    if case == 'geometry': collision['source_cap_sha256'] = 'f'*64
    if case == 'transform': collision['candidate_translation_cm'][0] += 1
    if case == 'material': receipt['assets'][0]['material_paths'] = ['/Game/Other']
    if case == 'receipt': receipt['completed'] = False
    if case == 'source_changed': receipt['assets'][0]['after']['triangle_count'] = 13
    if case == 'native_failed': collision['failures'] = ['bad union']
    if case == 'water_changed': collision['water_state_modified'] = True
    if case == 'material_bytes': (tmp_path/'unreal/Content/Test/Material.uasset').write_bytes(b'changed')
    with pytest.raises(ValueError):
        run(tmp_path, stage, collision, receipt)
