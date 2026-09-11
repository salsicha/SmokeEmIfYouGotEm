"""Fresh-load structural verification of the fine-grid ownership-only material change."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
BASE='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulCrestReview'


def main():
    lib=unreal.MaterialEditingLibrary
    source=unreal.load_asset(BASE+'_OpticsReview')
    material=unreal.load_asset(BASE+'_FineGridReview')
    assert source and material
    before={n.get_name():n for n in lib.get_material_expressions(source)}
    after={n.get_name():n for n in lib.get_material_expressions(material)}
    assert set(before).issubset(after)
    additions=[after[n] for n in set(after)-set(before)]
    assert len(additions)==1
    half=additions[0]
    assert isinstance(half,unreal.MaterialExpressionScalarParameter)
    assert str(half.get_editor_property('parameter_name'))=='StatefulDetailHalfCellM'
    assert half.get_editor_property('default_value')==.125
    changed=[]
    for name,a in before.items():
        b=after[name]
        assert a.get_class()==b.get_class()
        def inputs(mat,node):
            return {str(p):n.get_name() if n else None for p,n in zip(
                lib.get_material_expression_input_names(node),lib.get_inputs_for_material_expression(mat,node))}
        ai,bi=inputs(source,a),inputs(material,b)
        if isinstance(a,unreal.MaterialExpressionCustom):
            code=str(a.get_editor_property('code'))
            label=str(a.get_editor_property('description'))
            if label in ('Single transported foam coverage authority','Legacy drift foam only outside GPU ownership'):
                assert str(b.get_editor_property('code'))==code.replace('Domain.zw-0.25','Domain.zw-HalfCell')
                assert bi.pop('HalfCell')==half.get_name()
                changed.append(label)
            else:
                assert code==str(b.get_editor_property('code'))
        assert ai==bi,name
    assert len(changed)==2
    for prop in (unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET,unreal.MaterialProperty.MP_NORMAL,
                 unreal.MaterialProperty.MP_OPACITY,unreal.MaterialProperty.MP_BASE_COLOR,unreal.MaterialProperty.MP_ROUGHNESS):
        assert lib.get_material_property_input_node(source,prop).get_name()==lib.get_material_property_input_node(material,prop).get_name()
    assert sum(isinstance(n,unreal.MaterialExpressionPreviousFrameSwitch) for n in after.values())==2
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    asset=ROOT/('unreal/Content/'+(BASE+'_FineGridReview').removeprefix('/Game/')+'.uasset')
    report=dict(passed=True,asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),
                changed_nodes=changed,unchanged_other_wiring_and_custom_code=True,previous_frame_switches=2,
                scope='Saved graph, not photographic acceptance or a replacement for runtime shader validation')
    (ROOT/'docs/reconstruction-review-2026-09-07/fine-detail-material-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    unreal.log('Fine-detail fresh-load graph audit passed')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
