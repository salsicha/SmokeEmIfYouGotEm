"""Opt-in frozen-current characteristic experiment; never save the playable parent."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
DEST = '/Game/RaftSim/Environment/GeneratedLocalReview/FrothDeparture/M_SouthForkFrothDepartureV2'
REPORT = ROOT/'tmp/south-fork-froth-departure-material-v2-20260917.json'
BASELINE = '7e0f29aa41787954ef5d2156345a66c4f5d4d507f79985ae0f6a8311c6fb9038'
INCLUDE = '/Plugin/RaftSimWaterDetail/Private/RaftSimFrothDeparture.ush'
TAIL = '''
float2 worldM=(FrothUV+FrothOrigin.xy)*3;
float p=saturate(1-exp(-max(VertexFoam.r,0)*max(OpticalDensity,0)));
float a=frac(FrothTime),b=frac(a+.5),weight=1-abs(2*a-1);
float3 da=RaftSimFrothDeparture(DepartureDetail,DepartureFlow,worldM,FrothFlow.xy,a,DepartureEnable,8);
float3 db=RaftSimFrothDeparture(DepartureDetail,DepartureFlow,worldM,FrothFlow.xy,b,DepartureEnable,8);
float2 pa=worldM-lerp(FrothFlow.xy*a,da.xy,da.z);
float2 pb=worldM-lerp(FrothFlow.xy*b,db.xy,db.z);
// Filter the DEFORMED coordinates, before coverage-dependent early returns so
// derivatives are available across empty/full foam boundaries as well.
float footprintA=max(length(ddx(pa)),length(ddy(pa)));
float footprintB=max(length(ddx(pb)),length(ddy(pb)));
if(p<=0)return 0;if(p>=1)return 1;
RaftSimFrothCells cells;
return lerp(cells.Phase(pb,p,footprintB),cells.Phase(pa,p,footprintA),weight);
'''


def main():
    import unreal
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import integrate_south_fork_local_froth as source
    from raftsim_material_graph_signature import canonical_graph
    audit = 'RaftSimAuditFrothDeparture' in unreal.SystemLibrary.get_command_line()
    output = REPORT.with_name('south-fork-froth-departure-v2-reload-v1-20260917.json') if audit else REPORT
    if audit and os.environ.get('RAFTSIM_FROTH_DEPARTURE_RELOAD_REPORT'):
        output = Path(os.environ['RAFTSIM_FROTH_DEPARTURE_RELOAD_REPORT']).resolve()
        if output.parent != (ROOT/'tmp').resolve() or output.suffix != '.json':
            raise ValueError('Fresh scoped tmp JSON report required')
    if output.exists():
        raise FileExistsError(output)
    assert source.sha(source.FILE) == BASELINE
    lib = unreal.MaterialEditingLibrary
    if audit:
        material = unreal.load_asset(DEST)
    else:
        assert not unreal.EditorAssetLibrary.does_asset_exist(DEST)
        material = unreal.EditorAssetLibrary.duplicate_asset(source.PATH, DEST)
    assert material
    nodes = list(lib.get_material_expressions(material))
    coverage, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkTransportedFoamOpticsV1']
    code = (ROOT/'unreal/Plugins/RaftSim/Shaders/Private/RaftSimFrothCells.ush').read_text()+TAIL
    def graphs():
        properties = ('MP_WORLD_POSITION_OFFSET', 'MP_NORMAL', 'MP_OPACITY_MASK')
        return canonical_graph({p: source.graph(material, lib.get_material_property_input_node(
            material, getattr(unreal.MaterialProperty, p))) for p in properties})
    def all_nodes():
        return canonical_graph({n.get_name(): source.graph(material, n)[n.get_name()] for n in nodes})
    destination_file = ROOT/'unreal/Content'/(DEST.removeprefix('/Game/')+'.uasset')
    if audit:
        prior = json.loads(REPORT.read_text())
        assert source.sha(destination_file) == prior['material_sha256']
        assert all_nodes() == prior['candidate_nodes'] and graphs() == prior['protected_graphs']
        assert coverage.get_editor_property('code') == code
        assert list(coverage.get_editor_property('include_file_paths')) == [INCLUDE]
        result = dict(read_only_reload_passed=True, material_sha256=source.sha(destination_file))
    else:
        before = all_nodes(); protected = graphs()
        inputs = source.links(material, coverage)
        authority = source.links(material, inputs['VertexFoam'])
        paired = source.links(material, inputs['FrothFlow'])
        assert inputs['FrothFlow'].get_editor_property('desc') == 'SouthForkPairedFoamFlowV1'
        connections = dict(DepartureDetail=authority['Texture'],DepartureFlow=paired['FlowTexture'],
                           DepartureEnable=paired['Enable'])
        pins = list(coverage.get_editor_property('inputs'))
        for name in connections:
            pin = unreal.CustomInput(); pin.set_editor_property('input_name',name); pins.append(pin)
        coverage.set_editor_property('inputs',pins)
        for name,node in connections.items():
            assert lib.connect_material_expressions(node,'',coverage,name)
        coverage.set_editor_property('code',code)
        coverage.set_editor_property('include_file_paths',[INCLUDE])
        expected = before[coverage.get_name()]
        expected['code'] = code
        expected['inputs'] = dict(expected['inputs'],**{k:v.get_name() for k,v in connections.items()})
        assert all_nodes() == before and graphs() == protected
        lib.recompile_material(material)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
        result = dict(material=DEST,material_sha256=source.sha(destination_file),
                      candidate_nodes=all_nodes(),protected_graphs=protected,
                      only_coverage_departures_changed=True)
    assert source.sha(source.FILE) == BASELINE
    result.update(source_unchanged=True,source_sha256=BASELINE,visual_accepted=False,
                  physical_accepted=False,performance_accepted=False,release_accepted=False)
    with output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
    unreal.log('Froth departure material evidence: '+str(output))


if __name__ == '__main__':
    import unreal
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
