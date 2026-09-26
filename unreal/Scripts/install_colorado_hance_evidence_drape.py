"""Import the evidence-based Hance orthophoto drape as a Landscape colour texture.

physics/scripts/export_hance_evidence_runtime.py writes
terrain/hance_evidence_2021/hance_evidence_drape_4096x2048.png: the 2021
corridor imagery over the whole 2500 x 1212 m Landscape, north up, with an
invented smooth colour continuation outside the imagery footprint (labelled in
hance_evidence_terrain_manifest.json). This script imports it as
/Game/RaftSim/Environment/ColoradoRun/Terrain/T_RaftSim_ColoradoHance_EvidenceDrape
(sRGB, clamped, world group), which LoadOrCreateLandscapeCandidateMaterial uses
for colorado_river. Re-running replaces the texture's source bytes in place.
Appearance evidence (orthophoto colour with its capture lighting), not albedo.
"""
import hashlib
import json
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
TERRAIN = ROOT / 'physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/hance_evidence_2021'
DEST = '/Game/RaftSim/Environment/ColoradoRun/Terrain'
TEXTURE = DEST + '/T_RaftSim_ColoradoHance_EvidenceDrape'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    manifest = json.loads((TERRAIN / 'hance_evidence_terrain_manifest.json').read_text())
    png = ROOT / manifest['outputs']['drape']
    require(hashlib.sha256(png.read_bytes()).hexdigest() == manifest['outputs']['drape_sha256'], 'Drape differs from its manifest')
    task = unreal.AssetImportTask()
    task.filename = str(png)
    task.destination_path = DEST
    task.destination_name = TEXTURE.rsplit('/', 1)[1]
    task.automated = True
    task.replace_existing = True
    task.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(TEXTURE)
    require(isinstance(texture, unreal.Texture2D), 'Drape import failed')
    texture.set_editor_property('srgb', True)
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_WORLD)
    texture.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
    require(texture.blueprint_get_size_x() == 4096 and texture.blueprint_get_size_y() == 2048, 'Unexpected drape size')
    require(unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False), 'Texture save failed')
    unreal.log('RaftSim Hance evidence drape imported: %s' % TEXTURE)


main()
