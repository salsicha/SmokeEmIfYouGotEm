"""Tintable reviewed-rock material and its reach instances (granite, basalt).

Run inside the editor:

    UnrealEditor-Cmd SmokeEmIfYouGotEm.uproject -run=pythonscript \
        -script=unreal/Scripts/create_tinted_rock_materials.py

The six reviewed Poly Haven rocks (RockMossSet01) carry M_RockMossSet01_ReviewLit,
whose base colour is the scan's mossy tan diffuse with no parameters. The
observations describe grey granite on the Futaleufu Terminator banks and dark
basalt talus at Chilko Lava Canyon, so this builds M_RaftSim_ReviewedRockTinted:
the scan's normal and roughness are kept, and its diffuse luminance (the rock's
cracks, facets and lichen pattern, with the moss hue removed) is remapped
between RockDarkColor and RockLightColor. Two instances set the reach colours
(approximate, from descriptions and photographs; not measured albedo). The
editor applies them to the reach's reviewed rock components. A JSON report is
written to RAFTSIM_TINTED_ROCK_REPORT when set.
"""
import json
import os

import unreal

SCAN = '/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockMossSet01_1K'
PARENT_DIR = '/Game/RaftSim/Materials'
PARENT = 'M_RaftSim_ReviewedRockTinted'
INSTANCES = {
    # Futaleufu: "granite formations rising straight from the riverbanks",
    # "white and sculpted" boulders; medium-light grey granite.
    '/Game/RaftSim/Environment/FutaleufuRun/Rocks/MI_RaftSim_Futaleufu_GraniteRockV1': dict(
        RockDarkColor=(0.120, 0.120, 0.117), RockLightColor=(0.420, 0.415, 0.402), RockLuminanceScale=3.0,
        RockRoughnessScale=1.0),
    # Chilko: "dark basalt boulder talus (1-3 m boulders) at the waterline".
    '/Game/RaftSim/Environment/ChilkoRun/Rocks/MI_RaftSim_Chilko_BasaltRockV1': dict(
        RockDarkColor=(0.026, 0.026, 0.028), RockLightColor=(0.125, 0.120, 0.114), RockLuminanceScale=3.0,
        RockRoughnessScale=0.95),
}
MEL = unreal.MaterialEditingLibrary


def expression(material, cls, x, y):
    return MEL.create_material_expression(material, cls, x, y)


def scalar_parameter(material, name, value, x, y):
    e = expression(material, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property('parameter_name', name)
    e.set_editor_property('default_value', value)
    return e


def vector_parameter(material, name, rgb, x, y):
    e = expression(material, unreal.MaterialExpressionVectorParameter, x, y)
    e.set_editor_property('parameter_name', name)
    e.set_editor_property('default_value', unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    return e


def texture_sample(material, texture, sampler, x, y):
    e = expression(material, unreal.MaterialExpressionTextureSample, x, y)
    e.texture = texture
    e.sampler_type = sampler
    return e


def build_parent():
    path = f'{PARENT_DIR}/{PARENT}'
    # Rebuilt in place: the reach maps reference it (deleting would break them).
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        material = unreal.load_asset(path)
        material.modify()
        MEL.delete_all_material_expressions(material)
    else:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            PARENT, PARENT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    base_tex = unreal.load_asset(f'{SCAN}/T_RockMossSet01_BaseColor_1K')
    normal_tex = unreal.load_asset(f'{SCAN}/T_RockMossSet01_NormalGL_1K')
    rough_tex = unreal.load_asset(f'{SCAN}/T_RockMossSet01_Roughness_1K')
    assert base_tex and normal_tex and rough_tex, 'reviewed rock textures missing'
    S = unreal.MaterialSamplerType
    base = texture_sample(material, base_tex, S.SAMPLERTYPE_COLOR, -1200, -200)
    normal = texture_sample(material, normal_tex, S.SAMPLERTYPE_NORMAL, -1200, 200)
    rough = texture_sample(material, rough_tex, S.SAMPLERTYPE_MASKS, -1200, 450)
    # Luminance of the scan (moss hue removed), scaled to a 0-1 blend.
    weights = expression(material, unreal.MaterialExpressionConstant3Vector, -1000, -60)
    weights.set_editor_property('constant', unreal.LinearColor(0.299, 0.587, 0.114, 1.0))
    lum = expression(material, unreal.MaterialExpressionDotProduct, -850, -150)
    MEL.connect_material_expressions(base, 'RGB', lum, 'A')
    MEL.connect_material_expressions(weights, '', lum, 'B')
    lum_scale = scalar_parameter(material, 'RockLuminanceScale', 3.0, -850, 0)
    scaled = expression(material, unreal.MaterialExpressionMultiply, -700, -120)
    MEL.connect_material_expressions(lum, '', scaled, 'A')
    MEL.connect_material_expressions(lum_scale, '', scaled, 'B')
    blend = expression(material, unreal.MaterialExpressionSaturate, -560, -120)
    MEL.connect_material_expressions(scaled, '', blend, '')
    dark = vector_parameter(material, 'RockDarkColor', (0.10, 0.10, 0.10), -560, -380)
    light = vector_parameter(material, 'RockLightColor', (0.40, 0.40, 0.40), -560, -260)
    color = expression(material, unreal.MaterialExpressionLinearInterpolate, -380, -260)
    MEL.connect_material_expressions(dark, '', color, 'A')
    MEL.connect_material_expressions(light, '', color, 'B')
    MEL.connect_material_expressions(blend, '', color, 'Alpha')
    # The same soft ambient fill as the ReviewLit original (8 % of base colour).
    fill_scale = expression(material, unreal.MaterialExpressionConstant, -380, -60)
    fill_scale.set_editor_property('r', 0.08)
    fill = expression(material, unreal.MaterialExpressionMultiply, -200, -60)
    MEL.connect_material_expressions(color, '', fill, 'A')
    MEL.connect_material_expressions(fill_scale, '', fill, 'B')
    rough_scale = scalar_parameter(material, 'RockRoughnessScale', 1.0, -1000, 600)
    rough_scaled = expression(material, unreal.MaterialExpressionMultiply, -850, 500)
    MEL.connect_material_expressions(rough, 'R', rough_scaled, 'A')
    MEL.connect_material_expressions(rough_scale, '', rough_scaled, 'B')
    rough_final = expression(material, unreal.MaterialExpressionSaturate, -700, 500)
    MEL.connect_material_expressions(rough_scaled, '', rough_final, '')
    P = unreal.MaterialProperty
    MEL.connect_material_property(color, '', P.MP_BASE_COLOR)
    MEL.connect_material_property(normal, 'RGB', P.MP_NORMAL)
    MEL.connect_material_property(rough_final, '', P.MP_ROUGHNESS)
    MEL.connect_material_property(fill, '', P.MP_EMISSIVE_COLOR)
    material.set_editor_property('two_sided', False)
    material.set_editor_property('used_with_instanced_static_meshes', True)
    material.set_editor_property('used_with_nanite', True)
    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def build_instance(parent, path, params):
    folder, name = path.rsplit('/', 1)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mic = unreal.load_asset(path)
        mic.modify()
    else:
        mic = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mic, parent)
    for key, value in params.items():
        if isinstance(value, tuple):
            MEL.set_material_instance_vector_parameter_value(mic, key, unreal.LinearColor(value[0], value[1], value[2], 1.0))
        else:
            MEL.set_material_instance_scalar_parameter_value(mic, key, value)
    MEL.update_material_instance(mic)
    unreal.EditorAssetLibrary.save_loaded_asset(mic)
    return dict(path=path, parent=parent.get_path_name(), parameters={k: list(v) if isinstance(v, tuple) else v
                                                                        for k, v in params.items()})


def main():
    parent = build_parent()
    report = dict(parent=parent.get_path_name(), instances=[build_instance(parent, p, v) for p, v in INSTANCES.items()])
    unreal.log(f'RaftSim tinted rock materials: {json.dumps(report)}')
    out = os.environ.get('RAFTSIM_TINTED_ROCK_REPORT', '')
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=1)


main()
