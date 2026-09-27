"""Import an evidence-reconstruction Landscape drape as a colour texture (generic
form of install_colorado_hance_evidence_drape.py).

Environment: RAFTSIM_DRAPE_TERRAIN_MANIFEST (repo-relative terrain manifest whose
outputs.drape / drape_sha256 name the PNG) and RAFTSIM_DRAPE_TEXTURE (the
/Game/... asset path to create or replace). The texture is sRGB, clamped, world
group; LoadOrCreateLandscapeCandidateMaterial samples it for the river.
Appearance evidence (photograph colour with its capture lighting), not albedo.
"""
import hashlib
import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]


def main():
    manifest = json.loads((ROOT / os.environ['RAFTSIM_DRAPE_TERRAIN_MANIFEST']).read_text())
    texture_path = os.environ['RAFTSIM_DRAPE_TEXTURE']
    png = ROOT / manifest['outputs']['drape']
    if hashlib.sha256(png.read_bytes()).hexdigest() != manifest['outputs']['drape_sha256']:
        raise RuntimeError('Drape differs from its manifest')
    task = unreal.AssetImportTask()
    task.filename = str(png)
    task.destination_path, task.destination_name = texture_path.rsplit('/', 1)
    task.automated, task.replace_existing, task.save = True, True, False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(texture_path)
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError('Drape import failed')
    texture.set_editor_property('srgb', True)
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_WORLD)
    texture.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
    w, h = manifest['drape']['size_px']
    if texture.blueprint_get_size_x() != w or texture.blueprint_get_size_y() != h:
        raise RuntimeError('Unexpected drape size')
    if not unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False):
        raise RuntimeError('Texture save failed')
    unreal.log('RAFTSIM_EVIDENCE_DRAPE_IMPORTED ' + texture_path)


main()
