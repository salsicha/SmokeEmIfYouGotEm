"""Trace a deterministic sample of NAIP canopy roots against the rendered ground.

Loads the level's physical ground actors, flushes compilation so collision is
ready, and records (stored root - ground hit) for a 3000-root sample.
Environment: RAFTSIM_NAIP_CANOPY_PLACEMENT, RAFTSIM_NAIP_CANOPY_ROOTS_REPORT.
"""
import json
import os
import random
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'


def main():
    data = json.loads((ROOT / os.environ['RAFTSIM_NAIP_CANOPY_PLACEMENT']).read_text())
    report = (ROOT / os.environ['RAFTSIM_NAIP_CANOPY_ROOTS_REPORT']).resolve()
    assert report.is_relative_to(ROOT / 'tmp') and not report.exists()
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert levels.load_level(LEVEL)
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    ground = [d for d in descs if str(d.label).startswith(('SouthFork_coarse_terrain_', 'SouthFork_captured_context_',
                                                           'SouthFork_retained_rapid_', 'SouthFork_inferred_join_'))]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in ground])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    names = {str(d.name) for d in ground}
    loaded = subsystem.get_all_level_actors()
    ground_actors = [a for a in loaded if a.get_name() in names]
    ignore = [a for a in loaded if a.get_name() not in names]
    rng = random.Random(20260926)
    sample = rng.sample(data['instances'], min(3000, len(data['instances'])))
    diffs, misses = [], []
    for r in sample:
        x, y, z = r['world_root_cm']
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, z + 5000), unreal.Vector(x, y, z - 5000),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore, unreal.DrawDebugTrace.NONE, False)
        t = hit.to_tuple() if hit else None
        if not t or not t[0]:
            misses.append(r['id'])
            continue
        diffs.append(z - t[5].z)
    diffs.sort()
    p = lambda q: diffs[min(len(diffs) - 1, int(q * len(diffs)))] if diffs else None
    result = dict(ground_descriptors=len(ground), ground_actors_loaded=len(ground_actors), sample=len(sample),
                  misses=len(misses), miss_ids=misses[:20],
                  root_minus_ground_cm=dict(p01=p(0.01), p05=p(0.05), p50=p(0.5), p95=p(0.95), p99=p(0.99),
                                            min=diffs[0] if diffs else None, max=diffs[-1] if diffs else None))
    report.write_text(json.dumps(result, indent=2) + '\n')
    unreal.log('RAFTSIM_NAIP_CANOPY_ROOTS ' + json.dumps(result))


if __name__ == '__main__':
    main()
