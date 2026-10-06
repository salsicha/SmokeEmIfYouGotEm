"""Bounded correction of the newly created review asset, not a shared parent."""
from pathlib import Path
import hashlib
import importlib.util
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
try:
    spec=importlib.util.spec_from_file_location('foam_builder',ROOT/'unreal/Scripts/create_stateful_foam_review_material.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    lib=unreal.MaterialEditingLibrary
    material=unreal.load_asset(builder.DEST)
    if material is None:raise RuntimeError('Missing newly created review material')
    file=ROOT/'unreal/Content/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulFoamReview.uasset'
    before=hashlib.sha256(file.read_bytes()).hexdigest()
    original=list(lib.get_material_expressions(material))
    old=[n for n in original if isinstance(n,unreal.MaterialExpressionCustom) and str(n.get_editor_property('description'))=='Single transported foam coverage authority']
    if len(old)!=1 or old[0].get_editor_property('output_type')!=unreal.CustomMaterialOutputType.CMOT_FLOAT3:
        raise RuntimeError('Expected exactly the first review RGB-coverage node')
    node=old[0]
    code=str(node.get_editor_property('code'))
    if 'Base.r*(1-ownership)+Detail.w' not in code:raise RuntimeError('Unexpected first-review code')
    inputs=dict((str(p),n) for p,n in zip(lib.get_material_expression_input_names(node),lib.get_inputs_for_material_expression(material,node)))
    base=inputs['Base']
    restored=[]
    for target in original:
        for pin,source in zip(lib.get_material_expression_input_names(target),lib.get_inputs_for_material_expression(material,target)):
            if source!=node:continue
            if not lib.connect_material_expressions(base,'',target,'' if str(pin)=='None' else str(pin)):raise RuntimeError('Restore failed')
            restored.append(target.get_name())
    if len(restored)!=3:raise RuntimeError('Unexpected first-review consumer count')
    lib.delete_material_expression(material,node)
    changed,bypassed=builder.apply_coverage(material)
    errors=lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if errors:raise RuntimeError('Compile errors: '+str(errors))
    if not unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False):raise RuntimeError('Save failed')
    report=dict(material=builder.DEST,before_sha256=before,after_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
        restored_raw_consumers=restored,final_coverage_consumers=changed,bypassed_additive_coats=bypassed,
        old_code=code,new_code=builder.OWNERSHIP_CODE,visual_accepted=False)
    (ROOT/'docs/reconstruction-review-2026-09-07/stateful-foam-coverage-repair.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.log('Single foam ownership moved from raw aeration to final coverage; review-only repair saved')
finally:
    unreal.SystemLibrary.quit_editor()
