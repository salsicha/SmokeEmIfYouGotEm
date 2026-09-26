"""Re-import a rebuilt full-reach NAIP drape over T_SouthForkFullReachNAIP.

The ground material references the texture by path, so replacing its source
image in place updates every terrain tile without touching the material.
Environment: RAFTSIM_NAIP_DRAPE_DIR (T_SouthForkFullReachNAIP.png +
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


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    drape_dir = (ROOT / os.environ['RAFTSIM_NAIP_DRAPE_DIR']).resolve()
    report = (ROOT / os.environ['RAFTSIM_NAIP_DRAPE_REPORT']).resolve()
    assert report.is_relative_to(ROOT / 'tmp') and not report.exists()
    receipt = json.loads((drape_dir / 'receipt.json').read_text())
    png = drape_dir / 'T_SouthForkFullReachNAIP.png'
    assert sha(png) == receipt['sha256'], 'Drape PNG differs from its receipt'
    asset_file = ROOT / 'unreal/Content' / (TEXTURE.removeprefix('/Game/') + '.uasset')
    before = sha(asset_file)
    assert unreal.EditorAssetLibrary.does_asset_exist(TEXTURE)
    task = unreal.AssetImportTask()
    task.filename = str(png)
    task.destination_path = DEST
    task.destination_name = TEXTURE.rsplit('/', 1)[1]
    task.automated = True
    task.replace_existing = True
    task.replace_existing_settings = False
    task.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(TEXTURE)
    assert isinstance(texture, unreal.Texture2D)
    texture.set_editor_property('srgb', True)
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_WORLD)
    texture.set_editor_property('max_texture_size', 16384)
    texture.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
    assert texture.blueprint_get_size_x() == 16384 and texture.blueprint_get_size_y() == 8192
    assert unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    result = dict(texture=TEXTURE, drape_png_sha256=receipt['sha256'], texture_sha256_before=before,
                  texture_sha256_after=sha(asset_file), material_changed=False)
    report.write_text(json.dumps(result, indent=2) + '\n')
    unreal.log('RAFTSIM_NAIP_DRAPE_TEXTURE_UPDATED ' + json.dumps(result))


if __name__ == '__main__':
    main()
