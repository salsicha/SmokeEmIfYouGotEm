"""One foam coverage authority inside the fixed GPU simulation window."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
SOURCE='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulMotionReview'
DEST='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulFoamReview'
OWNERSHIP_CODE='''float2 xy=(World.xy-Center.xy)*0.01;
float2 river=float2(dot(xy,Basis.xy),dot(xy,Basis.zw));
float2 uv=(river-Domain.xy)/Domain.zw;
// Resolve fades from its outer cell centres, not the texture's outer borders.
float2 edge=min(uv,1-uv)*Domain.zw-0.25;
float ownership=smoothstep(0,4,min(edge.x,edge.y))*Enable;
// Detail.w already includes this edge fade plus wet-depth attenuation.
// Do not multiply it by ownership a second time or add the old foam beneath it.
return saturate(Base*(1-ownership)+Detail.w);'''


def apply_coverage(material):
    lib=unreal.MaterialEditingLibrary
    original=list(lib.get_material_expressions(material))
    def custom_named(label):
        found=[n for n in original if isinstance(n,unreal.MaterialExpressionCustom) and str(n.get_editor_property('description'))==label]
        if len(found)!=1:raise RuntimeError('Expected one '+label)
        return found[0]
    def input_named(node,pin):
        pairs=list(zip(lib.get_material_expression_input_names(node),lib.get_inputs_for_material_expression(material,node)))
        found=[n for p,n in pairs if str(p)==pin and n is not None]
        if len(found)!=1:raise RuntimeError('Expected connected pin '+pin)
        return found[0]
    detail=custom_named('World-registered persistent detail sample')
    # Replace FINAL shaded coverage, not raw aeration: the old lace/web gate
    # would otherwise perforate the simulated coverage a second time.
    candidates=[]
    for expression in original:
        if not isinstance(expression,unreal.MaterialExpressionClamp):continue
        raw=input_named(expression,'None')
        if not isinstance(raw,unreal.MaterialExpressionMultiply):continue
        gain=input_named(raw,'B')
        if isinstance(gain,unreal.MaterialExpressionScalarParameter) and str(gain.get_editor_property('parameter_name'))=='LiveFoamIntensity':
            candidates.append(expression)
    if len(candidates)!=1:raise RuntimeError('Expected one final legacy foam coverage clamp')
    coverage=candidates[0]
    node=lib.create_material_expression(material,unreal.MaterialExpressionCustom)
    node.set_editor_property('description','Single transported foam coverage authority')
    node.set_editor_property('code',OWNERSHIP_CODE)
    node.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    connections=[('Base',coverage,''),('Detail',detail,'')]
    for pin in ('World','Center','Basis','Domain','Enable'):
        source=input_named(detail,pin)
        output=str(lib.get_input_node_output_name_for_material_expression(detail,source))
        connections.append((pin,source,output))
    pins=[]
    for pin,_,_ in connections:
        entry=unreal.CustomInput();entry.set_editor_property('input_name',pin);pins.append(entry)
    node.set_editor_property('inputs',pins)
    for pin,source,output in connections:
        if not lib.connect_material_expressions(source,output,node,pin):raise RuntimeError('Ownership connection failed')
    changed=[]
    for target in original:
        for pin,source in zip(lib.get_material_expression_input_names(target),lib.get_inputs_for_material_expression(material,target)):
            if source!=coverage:continue
            if not lib.connect_material_expressions(node,'',target,'' if str(pin)=='None' else str(pin)):raise RuntimeError('Color consumer rewire failed')
            changed.append([target.get_name(),str(pin)])
    if not changed:raise RuntimeError('No final coverage consumers replaced')
    # Both former additive coats would bleach the same foam a second time.
    # The established parent now receives the authoritative coverage for its
    # color, froth-cell detail, roughness and opacity. Geometry/history unchanged.
    bypassed=[]
    for prop,label in [(unreal.MaterialProperty.MP_BASE_COLOR,'Current-transported froth color'),
                       (unreal.MaterialProperty.MP_ROUGHNESS,'Current-transported froth roughness')]:
        coat=custom_named(label)
        base=input_named(coat,'Base')
        if lib.get_material_property_input_node(material,prop) not in (coat,base):raise RuntimeError('Unexpected final coat wiring')
        output=str(lib.get_input_node_output_name_for_material_expression(coat,base))
        if not lib.connect_material_property(base,output,prop):raise RuntimeError('Coat bypass failed')
        bypassed.append(label)
    return changed,bypassed


def main():
    lib=unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):raise RuntimeError('Destination exists; preserve comparison evidence')
    immutable=[ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkRegisteredRockPlayable.umap',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulMotionReview.uasset']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in immutable}
    material=unreal.EditorAssetLibrary.duplicate_asset(SOURCE,DEST)
    if material is None:raise RuntimeError('Duplicate failed')
    changed,bypassed=apply_coverage(material)
    errors=lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if errors:raise RuntimeError('Compile errors: '+str(errors))
    if not unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False):raise RuntimeError('Save failed')
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):raise RuntimeError('Immutable source changed')
    report=dict(material=DEST,unchanged=hashes,coverage_consumers=changed,bypassed_additive_coats=bypassed,
        ownership_code=OWNERSHIP_CODE,domain_transition_m=4,cell_m=0.5,
        geometry_or_solver_changed=False,visual_accepted=False,performance_accepted=False)
    (ROOT/'docs/reconstruction-review-2026-09-07/stateful-foam-material-v2-setup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.log('Single stateful foam authority material saved; original motion material unchanged')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
