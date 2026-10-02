"""Guard four real river parents: shared froth/current, unchanged geometry.

Run only after the native shared-feature build. No level, instance, bed, source
capture or contact asset is saved. Backups and source/graph receipts survive
failures. This is a wiring audit, not pixel, boat, conservation or FPS acceptance.
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
from integrate_south_fork_local_froth import graph, links
from raftsim_material_graph_signature import canonical_graph

PARENTS = (
    ('Colorado', 'ColoradoRun', 'M_RaftSim_ColoradoCurrentWaterV3', 'L_Hance'),
    ('Pacuare', 'PacuareRun', 'M_RaftSim_PacuareCurrentWaterV2', 'L_UpperHuacas'),
    ('Futaleufu', 'FutaleufuRun', 'M_RaftSim_FutaleufuCurrentWaterV5', 'L_Terminator'),
    ('Chilko', 'ChilkoRun', 'M_RaftSim_ChilkoCurrentWaterV4', 'L_LavaCanyon'),
)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def protected_graphs(material):
    lib = unreal.MaterialEditingLibrary
    return canonical_graph({name: graph(material, lib.get_material_property_input_node(
        material, getattr(unreal.MaterialProperty, name)))
        for name in ('MP_WORLD_POSITION_OFFSET', 'MP_OPACITY_MASK')})


def calibration(material):
    result = {}
    for node in unreal.MaterialEditingLibrary.get_material_expressions(material):
        if isinstance(node, (unreal.MaterialExpressionScalarParameter,
                             unreal.MaterialExpressionVectorParameter)):
            name = str(node.get_editor_property('parameter_name'))
            value = str(node.get_editor_property('default_value'))
            result.setdefault(name, []).append(value)
    return {key: sorted(values) for key, values in result.items()}


def verify(material, label):
    lib = unreal.MaterialEditingLibrary
    nodes = list(lib.get_material_expressions(material))
    def marker(suffix):
        found = [n for n in nodes if str(n.get_editor_property('desc')) == label + suffix]
        if len(found) != 1:
            raise RuntimeError(label + suffix + ' missing/duplicated')
        return found[0]
    coverage = marker('TransportedFoamOpticsV1')
    lace = marker('LocalFoamLaceV1')
    clock = marker('CommittedFrothTimeV1')
    normal = marker('CurrentGradientNormalV1')
    pins = links(material, coverage)
    if pins['Lace'] != lace or pins['FrothTime'] != clock:
        raise RuntimeError('Local froth graph not connected')
    if int(pins['FrothFlow'].get_editor_property('coordinate_index')) != 3:
        raise RuntimeError('Foam optics must use actual CPU transport UV3')
    if str(links(material, clock)['CPUClock'].get_editor_property('parameter_name')) != 'RaftSimCPUFoamClock':
        raise RuntimeError('Foam uses a detached time source')
    np = links(material, normal)
    if np['TimeSeconds'] != clock or int(np['Flow'].get_editor_property('coordinate_index')) != 3:
        raise RuntimeError('Local normal and froth do not share transport/phase')
    consumers = [n.get_name() for n in nodes if coverage in links(material, n).values()]
    if len(consumers) != 4:
        raise RuntimeError('Expected colour, roughness, opacity and scattering consumers')
    expected = (ROOT/'unreal/Plugins/RaftSim/Shaders/Private/RaftSimFrothCells.ush').read_text()
    if not str(coverage.get_editor_property('code')).startswith(expected):
        raise RuntimeError('Froth code is not the in-game shared helper')
    return dict(local_flow_uv_channel=3, cpu_published_foam_phase=True,
                optical_consumers=consumers, calibration=calibration(material),
                protected=protected_graphs(material))


def main():
    report = (ROOT/os.environ['RAFTSIM_SHARED_OPTICS_REPORT']).resolve()
    if not report.is_relative_to(ROOT/'tmp') or report.exists():
        raise RuntimeError('Fresh repository-local tmp report required')
    backup = report.with_suffix('.backup.zip')
    if backup.exists():
        raise RuntimeError('Preserve previous backup')
    records = []
    for label, folder, asset, level in PARENTS:
        path = f'/Game/RaftSim/Environment/{folder}/Water/Materials/{asset}'
        file = ROOT/'unreal/Content'/(path.removeprefix('/Game/')+'.uasset')
        map_file = ROOT/'unreal/Content/RaftSim/Maps'/(level+'.umap')
        material = unreal.load_asset(path)
        if not material or any(str(n.get_editor_property('desc')) == label+'TransportedFoamOpticsV1'
                               for n in unreal.MaterialEditingLibrary.get_material_expressions(material)):
            raise RuntimeError('Missing or already-migrated parent: '+path)
        records.append(dict(label=label, path=path, file=file, map_file=map_file,
                            map_before=sha(map_file), before=sha(file), material=material,
                            protected=protected_graphs(material), calibration=calibration(material)))
    with zipfile.ZipFile(backup, 'x', zipfile.ZIP_DEFLATED) as archive:
        for record in records:
            archive.write(record['file'], record['file'].relative_to(ROOT).as_posix())
    with zipfile.ZipFile(backup) as archive:
        for record in records:
            if hashlib.sha256(archive.read(record['file'].relative_to(ROOT).as_posix())).hexdigest() != record['before']:
                raise RuntimeError('Backup verification failed')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, 'RaftSim.RefreshSharedFeatureOptics')
    first = {}
    for record in records:
        current = verify(record['material'], record['label'])
        if current['protected'] != record['protected']:
            raise RuntimeError('Protected geometry/wet branch changed: '+record['path'])
        for name, value in record['calibration'].items():
            if current['calibration'].get(name) != value:
                raise RuntimeError('Existing optical calibration changed: '+name)
        first[record['label']] = current
    # Native refresh must be idempotent, including the previously special Chilko graph.
    unreal.SystemLibrary.execute_console_command(world, 'RaftSim.RefreshSharedFeatureOptics')
    for record in records:
        if verify(record['material'], record['label']) != first[record['label']]:
            raise RuntimeError('Refresh not idempotent')
        unreal.MaterialEditingLibrary.recompile_material(record['material'])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    results = []
    for record in records:
        if not unreal.EditorAssetLibrary.save_loaded_asset(record['material'], only_if_is_dirty=False):
            raise RuntimeError('Save failed')
        if sha(record['map_file']) != record['map_before']:
            raise RuntimeError('Map changed during optical-only migration')
        results.append(dict(river=record['label'], material=record['path'],
                            before_sha256=record['before'], after_sha256=sha(record['file']),
                            map_unchanged=True, verified=first[record['label']]))
    report.write_text(json.dumps(dict(schema='raftsim.shared_river_optics_migration.v1',
                                     parents=results, backup_sha256=sha(backup),
                                     physics_and_wet_geometry_unchanged=True, refresh_idempotent=True,
                                     visual_accepted=False, boat_accepted=False, fps_accepted=False), indent=2)+'\n')
    unreal.log('Shared river optics migration verified: '+str(report))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
