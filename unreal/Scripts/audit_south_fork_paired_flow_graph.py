"""Read-only check of the actual playable material's foam-current graph.

Raw carrier UV3 is a fallback, not the GPU-owned window's final optical flow.
This proves saved graph wiring only, not rendered pixel motion or acceptance.
"""
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'tmp/southfork-eddy-paired-graph-v1.json'
PATH = '/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4'


def main():
    if REPORT.exists():
        raise RuntimeError('Fresh graph audit required; preserve old evidence')
    material = unreal.load_asset(PATH)
    if not material:
        raise RuntimeError('Actual playable material missing')
    lib = unreal.MaterialEditingLibrary
    nodes = list(lib.get_material_expressions(material))
    coverage, = [n for n in nodes if str(n.get_editor_property('desc')) == 'SouthForkTransportedFoamOpticsV1']
    links = dict(zip(map(str, lib.get_material_expression_input_names(coverage)),
                     lib.get_inputs_for_material_expression(material, coverage)))
    flow = links['FrothFlow']
    if str(flow.get_editor_property('desc')) != 'SouthForkPairedFoamFlowV1':
        raise RuntimeError('Actual foam optics do not use the paired-current node')
    if 'RaftSimRegisteredFoamFlow' not in str(flow.get_editor_property('code')):
        raise RuntimeError('Paired-current helper is not the active graph input')
    inputs = dict(zip(map(str, lib.get_material_expression_input_names(flow)),
                      lib.get_inputs_for_material_expression(material, flow)))
    texture = inputs['FlowTexture']
    if str(texture.get_editor_property('parameter_name')) != 'StatefulFoamFlowTexture':
        raise RuntimeError('Paired graph texture parameter mismatch')
    if int(inputs['CPUFlow'].get_editor_property('coordinate_index')) != 3:
        raise RuntimeError('Unexpected fallback transport channel')
    report = dict(material=PATH, paired_current_connected=True,
                  paired_texture_parameter='StatefulFoamFlowTexture',
                  fallback_uv_channel=3, read_only=True,
                  scope='Saved production graph wiring only. Raw UV3 is the fallback; GPU-owned foam optics use the paired texture. No pixel, boat, or FPS acceptance.')
    with REPORT.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2)
    unreal.log('South Fork paired-current graph verified read-only: ' + str(REPORT))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
