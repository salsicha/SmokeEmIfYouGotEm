"""Bounded correction: add continuous crest slope to crest-free base normals."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
ASSET='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulCrestReview'
try:
    lib=unreal.MaterialEditingLibrary
    material=unreal.load_asset(ASSET)
    path=ROOT/'unreal/Content'/ (ASSET.removeprefix('/Game/')+'.uasset')
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    nodes=[n for n in lib.get_material_expressions(material) if isinstance(n,unreal.MaterialExpressionCustom)
           and str(n.get_editor_property('description'))=='Shared fine crest world slope correction']
    assert len(nodes)==1
    old=str(nodes[0].get_editor_property('code'))
    assert old=='return RaftSimCrestCorrection(Atlas,GridPosition,int2(Size.xy)).yz;'
    nodes[0].set_editor_property('code','return RaftSimCrestCorrection(Atlas,GridPosition,int2(Size.xy),false).yz;')
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    report=dict(material=ASSET,before_sha256=before,after_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                old_code=old,new_code=str(nodes[0].get_editor_property('code')),visual_accepted=False)
    (ROOT/'docs/reconstruction-review-2026-09-07/stateful-crest-normal-repair.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
finally:
    unreal.SystemLibrary.quit_editor()
