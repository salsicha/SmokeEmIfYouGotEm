"""Bounded repair of this task's new material: zero atlas must not normalize NaN."""
from pathlib import Path
import hashlib
import importlib.util
import json
import unreal

root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('macro_builder',Path(__file__).with_name('create_stateful_gpu_carrier_material.py'))
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
try:
    material=unreal.load_asset(builder.DEST)
    node=unreal.MaterialEditingLibrary.get_material_property_input_node(material,unreal.MaterialProperty.MP_NORMAL)
    if not isinstance(node,unreal.MaterialExpressionCustom) or node.get_editor_property('description')!='GPU macro normal with existing detail':raise RuntimeError('Unexpected normal graph')
    old_code=node.get_editor_property('code')
    old_expected='float3 coarse=TransformWorldVectorToTangent(Parameters.TangentToWorld,normalize(Macro.xyz)); return normalize(lerp(Base,coarse+Base-float3(0,0,1),Enable));'
    if old_code not in (old_expected,builder.SAFE_MACRO_NORMAL_CODE):raise RuntimeError('Unexpected normal implementation; preserve it')
    asset=root/'unreal/Content/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulGPUCarrierReview.uasset'
    before=hashlib.sha256(asset.read_bytes()).hexdigest()
    node.set_editor_property('code',builder.SAFE_MACRO_NORMAL_CODE)
    errors=unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if errors:raise RuntimeError(str(errors))
    if not unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False):raise RuntimeError('Save failed')
    (root/'docs/reconstruction-review-2026-09-07/stateful-gpu-carrier-safe-default.json').write_text(json.dumps(dict(
        material=builder.DEST,before_sha256=before,after_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),
        old_code=old_code,new_code=builder.SAFE_MACRO_NORMAL_CODE,reason='Avoid normalizing zero when the optional atlas is not bound'),indent=2),encoding='utf-8')
    unreal.log('GPU macro material safe-default repair compiled and saved')
finally:
    unreal.SystemLibrary.quit_editor()
