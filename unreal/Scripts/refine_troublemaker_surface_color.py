"""Retain PBR ground detail beneath registered bank color after in-game review."""
import hashlib,json,shutil
from pathlib import Path
import unreal
ROOT=Path(__file__).resolve().parents[2]
report=ROOT/'unreal/Saved/RaftSimValidation/troublemaker-surface-color-20260912.json'
data=json.loads(report.read_text());lib=unreal.MaterialEditingLibrary
mat=unreal.load_asset(data['material'])
root=lib.get_material_property_input_node(mat,unreal.MaterialProperty.MP_BASE_COLOR)
assert str(root.get_editor_property('description'))=='Registered captured bank color V1'
old='return lerp(base,Photo*(.85+.15*saturate(luma/.12)),drape);'
new='return lerp(base,Photo*clamp(luma/.10,.4,1.1),drape*.55);'
code=str(root.get_editor_property('code'));assert old in code
path=ROOT/('unreal/Content/'+data['material'].removeprefix('/Game/')+'.uasset')
before=hashlib.sha256(path.read_bytes()).hexdigest()
backup=ROOT/'tmp/troublemaker-ground-material-backup'/f'{before}.uasset'
if not backup.exists():shutil.copy2(path,backup)
root.set_editor_property('code',code.replace(old,new))
lib.recompile_material(mat);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
assert unreal.EditorAssetLibrary.save_loaded_asset(mat,only_if_is_dirty=False)
data['bank_color_review']={'before_sha256':before,'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'backup':str(backup),'photographic_color_weight':.55,'reason':'Full drape flattened close banks; retain original PBR microvariation.','visual_accepted':False}
report.write_text(json.dumps(data,indent=2)+'\n')
