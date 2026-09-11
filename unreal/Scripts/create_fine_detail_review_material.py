"""Adapt only ownership's half-cell width for the finer, same-domain experiment."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(__file__).resolve().parents[2]
SOURCE = '/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulCrestReview_OpticsReview'
DEST = SOURCE.replace('_OpticsReview', '_FineGridReview')


def main():
    lib = unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        raise RuntimeError('Preserve previous fine-grid review')
    source_file = ROOT / ('unreal/Content/' + SOURCE.removeprefix('/Game/') + '.uasset')
    source_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
    source = unreal.load_asset(SOURCE)
    protected = [unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET,
                 unreal.MaterialProperty.MP_NORMAL, unreal.MaterialProperty.MP_OPACITY]
    protected_names = [lib.get_material_property_input_node(source, p).get_name() for p in protected]
    material = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST)
    assert material is not None
    nodes = list(lib.get_material_expressions(material))
    half = lib.create_material_expression(material, unreal.MaterialExpressionScalarParameter)
    half.set_editor_property('parameter_name', 'StatefulDetailHalfCellM')
    half.set_editor_property('default_value', .125)
    labels = ['Single transported foam coverage authority',
              'Legacy drift foam only outside GPU ownership']
    for label in labels:
        matches = [n for n in nodes if isinstance(n, unreal.MaterialExpressionCustom)
                   and str(n.get_editor_property('description')) == label]
        if len(matches) != 1:
            raise RuntimeError('Expected one ownership node: ' + label)
        node = matches[0]
        code = str(node.get_editor_property('code'))
        if code.count('Domain.zw-0.25') != 1:
            raise RuntimeError('Unexpected half-cell expression: ' + label)
        node.set_editor_property('code', code.replace('Domain.zw-0.25', 'Domain.zw-HalfCell'))
        pins = list(node.get_editor_property('inputs'))
        pin = unreal.CustomInput()
        pin.set_editor_property('input_name', 'HalfCell')
        pins.append(pin)
        node.set_editor_property('inputs', pins)
        assert lib.connect_material_expressions(half, '', node, 'HalfCell')
    assert protected_names == [lib.get_material_property_input_node(material, p).get_name() for p in protected]
    errors = lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if errors:
        raise RuntimeError('Material compile errors: ' + str(errors))
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    assert hashlib.sha256(source_file.read_bytes()).hexdigest() == source_hash
    report = dict(asset=DEST, source=SOURCE, unchanged_source_sha256=source_hash,
                  changed_ownership_nodes=labels, preserved_wpo_normal_opacity_roots=protected_names,
                  half_cell_m=.125, visual_accepted=False, performance_accepted=False)
    (ROOT/'docs/reconstruction-review-2026-09-07/fine-detail-material.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
