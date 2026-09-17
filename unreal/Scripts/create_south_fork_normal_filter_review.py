"""Isolate optical-normal derivative filtering on a generated, non-playable copy."""
import json
from pathlib import Path
import sys

BASELINE = '7164871356a26f5ad38dbde25fbde70c7d1d684e6c76ec856983415e0a4696cb'
DEST = '/Game/RaftSim/Environment/GeneratedLocalReview/OpticalNormalFilter/M_SouthForkOpticalNormalFilter'
FOOTPRINT = 'float footprint = max(length(ddx(p)), length(ddy(p)));'
FLOAT_HASH = '''        float3 q = frac(float3(p.x, p.y, p.x) * 0.1031);
        q += dot(q, q.yzx + 33.33);
        return frac((q.x + q.y) * q.z);'''
INTEGER_HASH = '''        int2 cell = int2(floor(p));
        uint h = uint(cell.x)*1597334677u ^ uint(cell.y)*3812015801u;
        h ^= h >> 16; h *= 2246822519u; h ^= h >> 13;
        return (float(h & 65535u) + 0.5) / 65536.0;'''


def unfiltered_control(code):
    if code.count(FOOTPRINT) != 1:
        raise ValueError('Expected exactly one phase-footprint expression')
    # A diagnostic only, not a final anti-aliasing policy. Retain both spectra,
    # strength, phase, flow, directions and actual gradient-noise evaluation.
    return code.replace(FOOTPRINT, 'float footprint = 0.0; // diagnostic: no derivative attenuation')


def control_code(code, control):
    if control == 'integer-hash':
        if code.count(FLOAT_HASH) != 1:
            raise ValueError('Expected the reviewed floating lattice hash')
        return code.replace(FLOAT_HASH, INTEGER_HASH)
    if control == 'unfiltered':
        return unfiltered_control(code)
    if control == 'constant':
        return 'return normalize(float3(0.18,0.09,1.0)); // diagnostic: constant tangent-space tilt'
    if control == 'zero-flow':
        if code.count('Flow.xy * phase') != 2:
            raise ValueError('Expected two optical flow phases')
        return code.replace('Flow.xy * phase', 'float2(0,0) * phase')
    raise ValueError('Unknown normal control')


def main(control='unfiltered'):
    import unreal
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import integrate_south_fork_local_froth as source
    from raftsim_material_graph_signature import canonical_graph
    suffix = '' if control == 'unfiltered' else '_' + control.replace('-', '_')
    destination = DEST + suffix
    report = source.ROOT/f'tmp/south-fork-normal-filter-review{suffix}-v1-20260917.json'
    if report.exists() or unreal.EditorAssetLibrary.does_asset_exist(destination):
        raise RuntimeError('Preserve previous review evidence')
    assert source.sha(source.FILE) == BASELINE, 'Unreviewed source material revision'
    material = unreal.EditorAssetLibrary.duplicate_asset(source.PATH, destination)
    assert material
    lib = unreal.MaterialEditingLibrary
    nodes = list(lib.get_material_expressions(material))
    normal, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkCurrentGradientNormalV1']
    before = {n.get_name(): canonical_graph(source.graph(material, n)[n.get_name()]) for n in nodes}
    code = normal.get_editor_property('code')
    assert code == (source.ROOT/'unreal/Shaders/Private/RaftSimLocalCurrentNormal.hlsl').read_text()
    protected = ('MP_WORLD_POSITION_OFFSET', 'MP_BASE_COLOR', 'MP_ROUGHNESS', 'MP_OPACITY', 'MP_OPACITY_MASK')
    def graphs():
        return canonical_graph({p: source.graph(material, lib.get_material_property_input_node(
            material, getattr(unreal.MaterialProperty, p))) for p in protected})
    protected_before = graphs()
    replacement = control_code(code, control)
    normal.set_editor_property('code', replacement)
    for node in nodes:
        expected = dict(before[node.get_name()])
        if node == normal:
            expected['code'] = replacement
        assert canonical_graph(source.graph(material, node)[node.get_name()]) == expected
    assert graphs() == protected_before
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    assert source.sha(source.FILE) == BASELINE
    with report.open('x', encoding='utf-8') as output:
        json.dump(dict(material=destination, control=control, source_sha256=BASELINE, source_unchanged=True,
            material_sha256=source.sha(source.ROOT/'unreal/Content'/(destination.removeprefix('/Game/')+'.uasset')),
            old_nodes_unchanged_except_normal_filter=True, protected_graphs=protected_before,
            normal_graph=canonical_graph(source.graph(material, normal)),
            visual_accepted=False, physical_accepted=False, release_accepted=False), output, indent=2)
    unreal.log('Optical normal filter review saved: '+str(report))


if __name__ == '__main__':
    import unreal
    try:
        command = unreal.SystemLibrary.get_command_line()
        controls = ('integer-hash',) if 'RaftSimIntegerNormalHash' in command else (('constant', 'zero-flow') if 'RaftSimAdditionalNormalControls' in command else ('unfiltered',))
        for control in controls:
            main(control)
    finally:
        unreal.SystemLibrary.quit_editor()
