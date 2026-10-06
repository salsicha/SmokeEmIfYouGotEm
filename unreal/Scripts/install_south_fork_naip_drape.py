"""Import the full-reach NAIP drape and use it in the normal South Fork ground.

`physics/scripts/build_south_fork_naip_drape.py` reprojects the repository's
official NAIP window exports into the terrain frame (receipt next to the PNG).
This editor script imports that PNG as a colour texture and extends
`M_SouthForkCompositeGround` so that, OUTSIDE the registered Troublemaker
window (whose own 0.425 m imagery and class map are unchanged), gently sloped
terrain takes the NAIP colour where the drape alpha is valid. Steep faces keep
the existing seamless rock material and the inferred submerged bed is excluded
by the drape alpha. Geometry, collision, water and every other asset are
unchanged; this is appearance evidence (orthophoto colour with its capture
lighting), not intrinsic albedo.

Environment: RAFTSIM_NAIP_DRAPE_DIR (contains T_SouthForkFullReachNAIP.png and
receipt.json) and RAFTSIM_NAIP_DRAPE_REPORT (fresh tmp JSON).
"""
import hashlib
import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
DEST = '/Game/RaftSim/Environment/SouthForkReconstruction/FullReach'
TEXTURE = DEST + '/T_SouthForkFullReachNAIP'
MATERIAL = DEST + '/M_SouthForkCompositeGround'
COLOR_NODE = 'Registered source color bounded in full river world V1'
DRAPE_WEIGHT = 0.8


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def asset_file(package):
    return ROOT / 'unreal/Content' / (package.removeprefix('/Game/') + '.uasset')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def import_texture(png):
    require(not unreal.EditorAssetLibrary.does_asset_exist(TEXTURE), 'Texture already exists')
    task = unreal.AssetImportTask()
    task.filename = str(png)
    task.destination_path = DEST
    task.destination_name = TEXTURE.rsplit('/', 1)[1]
    task.automated = True
    task.replace_existing = False
    task.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(TEXTURE)
    require(isinstance(texture, unreal.Texture2D), 'Drape import failed')
    texture.set_editor_property('srgb', True)
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_WORLD)
    texture.set_editor_property('max_texture_size', 16384)
    texture.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
    require(texture.blueprint_get_size_x() == 16384 and texture.blueprint_get_size_y() == 8192, 'Unexpected drape size')
    require(unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False), 'Texture save failed')
    return texture


def main():
    drape_dir = (ROOT / os.environ['RAFTSIM_NAIP_DRAPE_DIR']).resolve()
    report = (ROOT / os.environ['RAFTSIM_NAIP_DRAPE_REPORT']).resolve()
    require(report.is_relative_to(ROOT / 'tmp') and not report.exists(), 'Fresh tmp report required')
    receipt = json.loads((drape_dir / 'receipt.json').read_text())
    png = drape_dir / 'T_SouthForkFullReachNAIP.png'
    require(sha(png) == receipt['sha256'], 'Drape PNG differs from its receipt')
    width, height, px = receipt['width'], receipt['height'], receipt['pixel_m']
    e0, n_top = receipt['top_left_utm_m']
    ox, oy = receipt['world_origin_utm_m']
    material_before = sha(asset_file(MATERIAL))

    texture = import_texture(png)
    lib = unreal.MaterialEditingLibrary
    material = unreal.load_asset(MATERIAL)
    require(isinstance(material, unreal.Material), 'Ground material missing')
    nodes = list(lib.get_material_expressions(material))
    colors = [n for n in nodes if isinstance(n, unreal.MaterialExpressionCustom)
              and str(n.get_editor_property('description')) == COLOR_NODE]
    require(len(colors) == 1, 'Registered colour node not found exactly once')
    color = colors[0]
    require('FullPhoto' not in [str(i.get_editor_property('input_name')) for i in color.get_editor_property('inputs')],
            'Drape already installed')

    # World position -> drape UV (world x = east*100, y = -north*100 about the
    # full-reach origin; the drape's first row is its northern edge).
    position = lib.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -1400, 600)
    uv = lib.create_material_expression(material, unreal.MaterialExpressionCustom, -1150, 600)
    uv.set_editor_property('description', 'Full-reach NAIP drape UV V1')
    uv.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    pin = unreal.CustomInput()
    pin.set_editor_property('input_name', 'P')
    uv.set_editor_property('inputs', [pin])
    uv.set_editor_property('code',
        f'return float2((P.x*0.01 + {ox - e0:.6f}) / {px * width:.6f}, '
        f'({n_top - oy:.6f} + P.y*0.01) / {px * height:.6f});')
    require(lib.connect_material_expressions(position, '', uv, 'P'), 'UV input connection failed')
    sample = lib.create_material_expression(material, unreal.MaterialExpressionTextureSampleParameter2D, -900, 600)
    sample.set_editor_property('parameter_name', 'SouthForkFullReachNAIP')
    sample.set_editor_property('texture', texture)
    sample.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    require(lib.connect_material_expressions(uv, '', sample, 'UVs'), 'Sample UV connection failed')

    inputs = list(color.get_editor_property('inputs'))
    full = unreal.CustomInput()
    full.set_editor_property('input_name', 'FullPhoto')
    inputs.append(full)
    color.set_editor_property('inputs', inputs)
    require(lib.connect_material_expressions(sample, 'RGBA', color, 'FullPhoto'), 'Drape colour connection failed')
    original = str(color.get_editor_property('code'))
    marker = 'return lerp(base,Photo*clamp(luma/.10,.4,1.1),drape*.55);'
    require(original.rstrip().endswith(marker), 'Unexpected registered colour code')
    code = original.rstrip()[:-len(marker)] + (
        'float3 registered=lerp(base,Photo*clamp(luma/.10,.4,1.1),drape*.55);\n'
        '// Full-reach NAIP drape, only outside the registered rapid window:\n'
        '// orthophoto colour on gentle slopes, rock material on steep faces,\n'
        '// never on the inferred submerged bed (alpha 0).\n'
        'float inRapid=(all(AuthorityUV>=0.0)&&all(AuthorityUV<=1.0))?1.0:0.0;\n'
        'float fullDrape=saturate(FullPhoto.a)*(1.0-inRapid)*smoothstep(.45,.88,abs(N.z));\n'
        f'return lerp(registered,FullPhoto.rgb*clamp(luma/.10,.4,1.1),fullDrape*{DRAPE_WEIGHT});\n')
    color.set_editor_property('code', code)
    color.set_editor_property('description', COLOR_NODE)
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    require(unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False), 'Material save failed')
    result = dict(
        schema='raftsim.south_fork_naip_drape_install.v1', texture=TEXTURE, texture_sha256=sha(asset_file(TEXTURE)),
        drape_png_sha256=receipt['sha256'], material=MATERIAL, material_sha256_before=material_before,
        material_sha256_after=sha(asset_file(MATERIAL)), drape_weight=DRAPE_WEIGHT,
        uv_code=str(uv.get_editor_property('code')), registered_rapid_unchanged=True,
        geometry_collision_water_unchanged=True, intrinsic_albedo=False, visual_accepted=False)
    report.write_text(json.dumps(result, indent=2) + '\n')
    unreal.log('RAFTSIM_NAIP_DRAPE_INSTALLED ' + json.dumps(result))


if __name__ == '__main__':
    main()
