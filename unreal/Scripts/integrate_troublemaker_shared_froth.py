"""Migrate the actual compact South Fork carrier, retaining wet/contact geometry.

Uses the same in-game procedural froth helper and CPU optical phase as the
full-reach parents. A fresh receipt and byte-verified backup are mandatory.
Only this material is saved; no map, mesh, hydraulic field or hull is changed.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from configure_playable_troublemaker_foam import graph_signature
from integrate_south_fork_local_froth import links
from raftsim_material_graph_signature import canonical_graph

PATH = '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/M_TroublemakerWater'
FILE = ROOT/'unreal/Content'/(PATH.removeprefix('/Game/')+'.uasset')
SHADER = ROOT/'unreal/Plugins/SEIYGECore/Shaders/Private/RaftSimFrothCells.ush'
MARKER = 'Captured shared transported froth V2'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    report = (ROOT/os.environ['RAFTSIM_COMPACT_FROTH_REPORT']).resolve()
    backup = report.with_suffix('.backup.zip')
    before_report = report.with_suffix('.before.json')
    if not report.is_relative_to(ROOT/'tmp') or any(p.exists() for p in (report, backup, before_report)):
        raise RuntimeError('Fresh repository-local receipt and backup required')
    lib = unreal.MaterialEditingLibrary
    material = unreal.load_asset(PATH)
    if not isinstance(material, unreal.Material):
        raise RuntimeError('Actual compact carrier missing')
    nodes = list(lib.get_material_expressions(material))
    def custom(marker):
        matches = [n for n in nodes if isinstance(n, unreal.MaterialExpressionCustom)
                   and str(n.get_editor_property('description')) == marker]
        if len(matches) != 1:
            raise RuntimeError('Expected exactly one '+marker)
        return matches[0]
    if any(str(n.get_editor_property('desc')) == MARKER for n in nodes):
        raise RuntimeError('Already migrated; inspect a fresh read-only graph')
    coverage = custom('Captured single transported foam optics V1')
    normal = custom('Captured transported froth normal V1')
    ripple = custom('Survey current-carried aperiodic ripple normal V2')
    if lib.get_material_property_input_node(material, unreal.MaterialProperty.MP_NORMAL) != normal:
        raise RuntimeError('Unexpected normal branch; do not overwrite')
    old = {key: value for key, value in links(material, coverage).items() if value is not None}
    normal_links = links(material, normal)
    if set(old) != {'TransportedFoam', 'Lace', 'OpticalDensity'} or normal_links['BaseNormalTS'] != ripple:
        raise RuntimeError('Unexpected legacy optical graph')
    protected = {k: canonical_graph(graph_signature(material, getattr(unreal.MaterialProperty, 'MP_'+k)))
                 for k in ('OPACITY', 'WORLD_POSITION_OFFSET', 'EMISSIVE_COLOR')}
    ripple_graph = canonical_graph(graph_signature(material, unreal.MaterialProperty.MP_NORMAL))
    # Preserve this actual graph before changing it, not a historical hash assumption.
    digest = sha(FILE)
    before_report.write_text(json.dumps(dict(material=PATH, sha256=digest,
        protected=protected, original_normal_graph=ripple_graph), indent=2)+'\n')
    maps = {p: sha(p) for p in (
        ROOT/'unreal/Content/RaftSim/Maps/L_SouthFork_Troublemaker.umap',
        ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap')}
    with zipfile.ZipFile(backup, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(FILE, FILE.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(backup) as archive:
        if hashlib.sha256(archive.read(FILE.relative_to(ROOT).as_posix())).hexdigest() != digest:
            raise RuntimeError('Backup verification failed')
    def expression(kind, marker):
        node = lib.create_material_expression(material, kind)
        node.set_editor_property('desc', marker)
        return node
    uv = expression(unreal.MaterialExpressionTextureCoordinate, 'Compact shared froth UV0')
    uv.set_editor_property('coordinate_index', 0)
    flow = expression(unreal.MaterialExpressionTextureCoordinate, 'Compact shared foam transport UV3')
    flow.set_editor_property('coordinate_index', 3)
    def vector(name):
        found = [n for n in nodes if isinstance(n, unreal.MaterialExpressionVectorParameter)
                 and str(n.get_editor_property('parameter_name')) == name]
        if len(found) > 1:
            raise RuntimeError('Duplicated optical parameter '+name)
        node = found[0] if found else expression(unreal.MaterialExpressionVectorParameter, name)
        if not found:
            node.set_editor_property('parameter_name', name)
            node.set_editor_property('default_value', unreal.LinearColor(0, 0, 0, 0))
        return node
    origin = vector('RaftSimWaterUVOrigin')
    cpu = vector('RaftSimCPUFoamClock')
    clock = expression(unreal.MaterialExpressionCustom, 'Compact CPU foam phase V1')
    clock.set_editor_property('code', 'return frac(frac(CPUClock.x)+CPUClock.y);')
    clock.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    pin = unreal.CustomInput(); pin.set_editor_property('input_name', 'CPUClock')
    clock.set_editor_property('inputs', [pin])
    assert lib.connect_material_expressions(cpu, '', clock, 'CPUClock')
    additions = [('FrothUV', uv), ('FrothFlow', flow), ('FrothOrigin', origin), ('FrothTime', clock)]
    inputs = list(coverage.get_editor_property('inputs'))
    for name, _ in additions:
        pin = unreal.CustomInput(); pin.set_editor_property('input_name', name); inputs.append(pin)
    coverage.set_editor_property('inputs', inputs)
    for name, source in additions:
        assert lib.connect_material_expressions(source, '', coverage, name)
    coverage.set_editor_property('description', MARKER)
    coverage.set_editor_property('code', SHADER.read_text()+
        '\nfloat2 worldM=(FrothUV+FrothOrigin.xy)*3;\n'
        'float footprintM=max(length(ddx(worldM)),length(ddy(worldM)));\n'
        'RaftSimFrothCells cells; return cells.Sample(TransportedFoam,OpticalDensity,worldM,FrothFlow.xy,FrothTime,footprintM);\n')
    # Bubble relief follows the same visible web, not the obsolete detached lace.
    # Raw transported amount supplies height; the existing ripple normal stays intact.
    assert lib.connect_material_expressions(old['TransportedFoam'], 'R', normal, 'Foam')
    assert lib.connect_material_expressions(coverage, '', normal, 'Lace')
    for key, value in protected.items():
        assert canonical_graph(graph_signature(material, getattr(unreal.MaterialProperty, 'MP_'+key))) == value
    assert links(material, normal)['BaseNormalTS'] == ripple
    current = links(material, coverage)
    assert current['FrothFlow'] == flow and current['FrothTime'] == clock
    assert links(material, clock)['CPUClock'] == cpu
    # All existing output consumers remain wired to this same coverage node.
    consumers = [n.get_name() for n in lib.get_material_expressions(material)
                 if coverage in links(material, n).values()]
    assert len(consumers) == 4, consumers  # color, roughness, specular, lit relief
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    assert all(sha(path) == value for path, value in maps.items())
    report.write_text(json.dumps(dict(schema='raftsim.compact_shared_froth_migration.v1',
        material=PATH, before_sha256=digest, after_sha256=sha(FILE),
        shader_sha256=sha(SHADER), backup_sha256=sha(backup),
        transport_uv_channel=3, phase_source='RaftSimCPUFoamClock',
        optical_consumers=consumers, underlying_ripple_retained=True,
        opacity_geometry_emissive_and_maps_unchanged=True,
        foam_amount_sources_density_and_physics_unchanged=True,
        visual_accepted=False, boat_accepted=False, fps_accepted=False), indent=2)+'\n')
    unreal.log('Compact shared transported froth migrated: '+str(report))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
