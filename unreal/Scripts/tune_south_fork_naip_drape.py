"""Revise only the full-reach NAIP drape line of M_SouthForkCompositeGround.

V1 blended the orthophoto at 0.8 over the procedural tan rock, multiplied it by
clamp(detailLuma/0.10, 0.4, 1.1) (almost always a flat 1.1 brightening) and
dropped it on slopes steeper than ~27 degrees, although the canyon walls of the
South Fork are largely wooded in the imagery. V2: full weight; the rock
material takes over only on faces steeper than ~66 degrees; the scanned rock
detail modulates the photo around 1 (clamp(detailLuma/0.27, 0.7, 1.25)) so it
adds micro variation without changing the imagery's mean. The registered
Troublemaker branch and every other node are unchanged.
"""
import hashlib
import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
MATERIAL = '/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/M_SouthForkCompositeGround'
COLOR_NODE = 'Registered source color bounded in full river world V1'
OLD_LINES = (
    'float fullDrape=saturate(FullPhoto.a)*(1.0-inRapid)*smoothstep(.45,.88,abs(N.z));\n'
    'return lerp(registered,FullPhoto.rgb*clamp(luma/.10,.4,1.1),fullDrape*0.8);\n')
NEW_LINES = (
    '// Drape V2: full weight, rock only on faces steeper than ~66 degrees,\n'
    '// scanned detail modulates the photo around 1.\n'
    'float fullDrape=saturate(FullPhoto.a)*(1.0-inRapid)*smoothstep(.25,.60,abs(N.z));\n'
    'return lerp(registered,FullPhoto.rgb*clamp(luma/.27,.7,1.25),fullDrape);\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    report = (ROOT / os.environ['RAFTSIM_NAIP_DRAPE_REPORT']).resolve()
    assert report.is_relative_to(ROOT / 'tmp') and not report.exists()
    asset = ROOT / 'unreal/Content' / (MATERIAL.removeprefix('/Game/') + '.uasset')
    before = sha(asset)
    lib = unreal.MaterialEditingLibrary
    material = unreal.load_asset(MATERIAL)
    nodes = [n for n in lib.get_material_expressions(material) if isinstance(n, unreal.MaterialExpressionCustom)
             and str(n.get_editor_property('description')) == COLOR_NODE]
    assert len(nodes) == 1
    code = str(nodes[0].get_editor_property('code'))
    assert code.count(OLD_LINES) == 1, 'Drape V1 lines not found'
    nodes[0].set_editor_property('code', code.replace(OLD_LINES, NEW_LINES))
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    report.write_text(json.dumps(dict(material=MATERIAL, sha256_before=before, sha256_after=sha(asset),
                                      replaced=OLD_LINES, with_lines=NEW_LINES), indent=2) + '\n')
    unreal.log('RAFTSIM_NAIP_DRAPE_TUNED')


if __name__ == '__main__':
    main()
