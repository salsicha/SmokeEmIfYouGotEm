"""Read-only native grounding preflight. Never saves or mutates the map.

Environment: RAFTSIM_CANOPY_PREFLIGHT_DIR, a fresh repo/tmp output directory.
Inputs are bound to the inspected saved map and the reviewed native-grid source.
Output transforms are preparation only, not rendered or performance acceptance.
"""
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inspect_futaleufu_canopy import ROOT, LEVEL, sha, xyz
from futaleufu_canopy_transforms import transform_row

MAP_SHA = 'd52f78659fa50d9a8fc930bae477400192e41cfd4ba12148067b5e0c4fb9a882'
SOURCE_SHA = 'b679e2859d4f7f2ad04676bbe595b21ed1895d8ef101f75957710cd840052646'
INVENTORY_SHA = '1aa40fcccbf0c728bf145e4c4965ada06f9cc25a0b4175a93d7ff773646b9d32'
SOURCE = ROOT/'tmp/futaleufu-native-grid-canopy-v1/rock-filtered-canopy.json'
INVENTORY = ROOT/'tmp/futaleufu-canopy-inventory-native-v2/report.json'


def main():
    import unreal
    output = (ROOT/os.environ['RAFTSIM_CANOPY_PREFLIGHT_DIR']).resolve()
    output.relative_to(ROOT/'tmp')
    report = output/'grounding.json'
    if report.exists():
        raise ValueError('Fresh native preflight required')
    map_path = ROOT/'unreal/Content/RaftSim/Maps/L_Terminator.umap'
    protected = {map_path: MAP_SHA, SOURCE: SOURCE_SHA, INVENTORY: INVENTORY_SHA}
    for path, digest in protected.items():
        if sha(path) != digest:
            raise RuntimeError('Changed preflight dependency: '+str(path))
    data = json.loads(SOURCE.read_text())
    inventory = json.loads(INVENTORY.read_text())
    if data['level'] != LEVEL or data['terrain_or_hydraulic_geometry_modified']:
        raise ValueError('Expected nonphysical canopy placement')
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):
        raise RuntimeError('Map load failed')
    if unreal.WorldPartitionBlueprintLibrary.get_actor_descs():
        raise RuntimeError('Map structure changed; inspect partitioned map explicitly')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    ground = [a for a in actors if isinstance(a, unreal.LandscapeProxy)]
    if not ground:
        raise RuntimeError('No native Landscape ground found')
    ignore = [a for a in actors if a not in ground]
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    bound_components = {}
    for previous in inventory['canopy']:
        actor = next(a for a in actors if a.get_name() == previous['actor'])
        component = next(c for c in actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
                         if c.get_name() == previous['component'])
        if component.get_instance_count() != previous['count']:
            raise RuntimeError('Saved canopy count changed')
        if component.static_mesh.get_path_name() != previous['mesh']:
            raise RuntimeError('Saved canopy mesh changed')
        materials = [component.get_material(i).get_path_name() if component.get_material(i) else None
                     for i in range(component.get_num_materials())]
        if materials != previous['materials'] or component.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION:
            raise RuntimeError('Saved canopy appearance/collision changed')
        bounds = component.static_mesh.get_bounding_box()
        if dict(min=xyz(bounds.min), max=xyz(bounds.max)) != previous['bounds']:
            raise RuntimeError('Mesh bounds changed')
        key = 'understory' if 'Understory' in previous['component'] else ('0' if 'CanopyA_' in previous['component'] else '1')
        if key in bound_components:
            raise RuntimeError('Ambiguous saved canopy component')
        bound_components[key] = previous
    if set(bound_components) != {'0', '1', 'understory'}:
        raise RuntimeError('Expected exactly the three inspected canopy components')
    result = dict(schema='raftsim.futaleufu_native_canopy_grounding.v1', level=LEVEL,
        map_sha256=MAP_SHA, source_sha256=SOURCE_SHA, inventory_sha256=INVENTORY_SHA,
        saved_anything=False, terrain_modified=False, render_validated=False,
        performance_validated=False, ground_actors=[a.get_name() for a in ground],
        components={key:dict(actor=v['actor'], component=v['component'], mesh=v['mesh'],
                           materials=v['materials'], transforms=[]) for key,v in bound_components.items()},
        missing_ground=[], traced=0)
    for understory, rows in ((False, data['instances']), (True, data['understory'])):
        for index, row in enumerate(rows):
            key = 'understory' if understory else str(row[5])
            previous = bound_components[key]
            # Validate before native calls. Advisory DSM heights never set roots.
            transform_row(row, previous['bounds'], 0., understory=understory)
            x,y = row[:2]
            hit = unreal.SystemLibrary.line_trace_single(world,
                unreal.Vector(x,y,1000000), unreal.Vector(x,y,-1000000),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
                unreal.DrawDebugTrace.NONE, False)
            values = hit.to_tuple() if hit else None
            if not values or not values[0]:
                result['missing_ground'].append(dict(kind=key, index=index, xy_cm=[x,y]))
                continue
            z = float(values[5].z)
            if not math.isfinite(z):
                raise RuntimeError('Nonfinite native ground')
            transform = transform_row(row, previous['bounds'], z, understory=understory)
            result['components'][key]['transforms'].append(transform)
            result['traced'] += 1
            if result['traced'] % 4096 == 0:
                unreal.log('Futaleufu native canopy ground traces: '+str(result['traced']))
    for path,digest in protected.items():
        if sha(path) != digest:
            raise RuntimeError('Dependency changed during preflight: '+str(path))
    result['all_roots_grounded'] = not result['missing_ground']
    result['expected'] = len(data['instances'])+len(data['understory'])
    result['map_unchanged'] = True
    with report.open('x') as stream:
        json.dump(result, stream, separators=(',',':'), allow_nan=False)
    if not result['all_roots_grounded'] or result['traced'] != result['expected']:
        raise RuntimeError('Native ground missing; preserve installed map and inspect grounding.json')
    unreal.log('Futaleufu canopy preflight passed: '+str(result['traced']))
    levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank')
    unreal.SystemLibrary.collect_garbage()


if __name__ == '__main__':
    import unreal
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
