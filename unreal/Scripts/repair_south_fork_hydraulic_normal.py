"""Restore the existing hydraulic normal root; audit repeated author refreshes.

No shader arithmetic, expression, water state or non-normal output may change.
Run with -RaftSimRepairHydraulicNormal once; without it, audit a fresh load.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from integrate_south_fork_local_froth import graph,links
from raftsim_material_graph_signature import canonical_graph
from configure_playable_troublemaker_foam import graph_signature
PATH='/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4'
FILE=ROOT/('unreal/Content/'+PATH.removeprefix('/Game/')+'.uasset')
BASE='6f235b61577289f195cbbb801ce8a83e40b961827ba4be637806178ea1dcedf9'
REPORT=ROOT/'tmp/south-fork-hydraulic-normal-installed-v1.json'
PROPS=('BASE_COLOR','ROUGHNESS','SPECULAR','OPACITY','OPACITY_MASK','EMISSIVE_COLOR','WORLD_POSITION_OFFSET')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
lib=unreal.MaterialEditingLibrary
mat=unreal.load_asset(PATH)
assert isinstance(mat,unreal.Material) and mat.get_editor_property('tangent_space_normal')
def snapshot():
    nodes=list(lib.get_material_expressions(mat))
    records={}
    for node in nodes:graph(mat,node,records)
    return canonical_graph(records)
def protected():return {p:graph_signature(mat,getattr(unreal.MaterialProperty,'MP_'+p)) for p in PROPS}
def verify():
    node=lib.get_material_property_input_node(mat,unreal.MaterialProperty.MP_NORMAL)
    assert str(node.get_editor_property('desc'))=='SouthForkMovingDetailNormalV1'
    assert str(node.get_editor_property('code'))=='return normalize(float3(Base.xy-Detail.yz*Base.z,Base.z));'
    pins=links(mat,node)
    assert str(pins['Base'].get_editor_property('desc'))=='SouthForkCurrentGradientNormalV1'
    assert str(pins['Detail'].get_editor_property('desc'))=='SouthForkRegisteredDetailV1'
    assert pins['Detail'].get_name() in protected()['WORLD_POSITION_OFFSET']['nodes']
    return graph_signature(mat,unreal.MaterialProperty.MP_NORMAL)
install='-RaftSimRepairHydraulicNormal' in unreal.SystemLibrary.get_command_line()
if install:
    assert not REPORT.exists() and sha(FILE)==BASE
    original=snapshot();outputs=protected()
    assert str(lib.get_material_property_input_node(mat,unreal.MaterialProperty.MP_NORMAL).get_editor_property('desc'))=='SouthForkCurrentGradientNormalV1'
    backup=ROOT/'tmp/south-fork-hydraulic-normal-backup'/f'{BASE}.uasset'
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():shutil.copy2(FILE,backup)
    assert sha(backup)==BASE
    for _ in range(2):
        unreal.SystemLibrary.execute_console_command(None,'RaftSim.RefreshSouthForkCurrentNormals')
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert snapshot()==original,'An existing node changed'
        assert protected()==outputs,'Non-normal output changed'
        normal=verify()
    assert sha(FILE)!=BASE
    REPORT.write_text(json.dumps(dict(before_sha256=BASE,after_sha256=sha(FILE),
        nodes=original,protected=outputs,normal=normal,refresh_count=2,
        visual_accepted=False,performance_accepted=False),indent=2)+'\n')
else:
    saved=json.loads(REPORT.read_text())
    assert sha(FILE)==saved['after_sha256']
    assert snapshot()==saved['nodes'] and protected()==saved['protected']
    assert verify()==saved['normal']
    out=ROOT/'tmp/south-fork-hydraulic-normal-fresh-v1.json'
    assert not out.exists()
    out.write_text(json.dumps(dict(material_sha256=sha(FILE),fresh_saved_graph_pass=True))+'\n')
unreal.log('HYDRAULIC_NORMAL_REPAIR_PASS install='+str(install))
