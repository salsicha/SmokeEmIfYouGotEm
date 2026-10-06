"""Create an isolated lit fragment material. No existing water asset is modified."""
from pathlib import Path
import json
import unreal

ROOT = Path(__file__).resolve().parents[2]
DEST = '/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_SecondaryWaterReview'


def main():
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        raise RuntimeError('Preserve existing secondary-water review material')
    folder, name = DEST.rsplit('/', 1)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, folder, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError('Material creation failed')
    lib = unreal.MaterialEditingLibrary
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    color = lib.create_material_expression(material, unreal.MaterialExpressionConstant3Vector)
    color.set_editor_property('constant', unreal.LinearColor(.72, .76, .75, 1))
    assert lib.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    for prop, value in [(unreal.MaterialProperty.MP_ROUGHNESS, .6),
                        (unreal.MaterialProperty.MP_SPECULAR, .25)]:
        node = lib.create_material_expression(material, unreal.MaterialExpressionConstant)
        node.set_editor_property('r', value)
        assert lib.connect_material_property(node, '', prop)
    lib.set_material_usage(material, unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
    lib.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    result = {'asset': DEST, 'default_lit': True, 'opaque': True,
              'roughness': .6, 'specular': .25, 'emission': False,
              'production_promotion': False}
    out = ROOT / 'docs/reconstruction-review-2026-09-07/secondary-water-material.json'
    out.write_text(json.dumps(result, indent=2)+'\n')
    unreal.log('Secondary water material saved: '+str(out))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
