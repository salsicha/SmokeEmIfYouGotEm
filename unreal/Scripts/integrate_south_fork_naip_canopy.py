"""Place the NAIP-evidence canopy in the normal South Fork FullReach map.

Reads `placement.json` from `physics/scripts/build_south_fork_naip_canopy.py`
(positions from NAIP canopy, roots from the captured surface grid, species and
sizes inferred). Instances are grouped into 256 m cells; each cell gets up to
two spatially loaded `RaftSimCapturedCanopyActor`s (forms 0-2 and 3-5), so
World Partition streams them with the terrain. Component settings are mirrored
from an existing captured canopy actor (visual, non-colliding). A random
sample of roots is traced against the loaded physical ground to measure the
root-to-rendered-terrain error. Existing actors and assets are not modified.

Environment: RAFTSIM_NAIP_CANOPY_PLACEMENT (placement.json, repo-relative),
RAFTSIM_NAIP_CANOPY_REPORT (fresh tmp JSON).
"""
import hashlib
import json
import os
import random
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
CELL_CM = 25600.0
GROUPS = ((0, 1, 2), (3, 4, 5))
NAMES = ('canopy_a', 'canopy_b', 'canopy_c')
# A later additive pass (e.g. the recoloured lower gorge) uses its own prefix.
LABEL_PREFIX = os.environ.get('RAFTSIM_NAIP_CANOPY_LABEL', 'South Fork NAIP canopy')
SAMPLE_TRACES = 3000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def trace_ground(world, ignore, x, y, z):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, z + 3000), unreal.Vector(x, y, z - 3000),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore, unreal.DrawDebugTrace.NONE, False)
    values = hit.to_tuple() if hit else None
    if not values or not values[0]:
        return None
    return values[5].z


def main():
    placement_path = (ROOT / os.environ['RAFTSIM_NAIP_CANOPY_PLACEMENT']).resolve()
    report = (ROOT / os.environ['RAFTSIM_NAIP_CANOPY_REPORT']).resolve()
    require(report.is_relative_to(ROOT / 'tmp') and not report.exists(), 'Fresh tmp report required')
    data = json.loads(placement_path.read_text())
    require(data['schema'] == 'raftsim.south_fork.naip_canopy_placement.v1' and data['level'] == LEVEL, 'Wrong placement')
    rows = data['instances']
    require(len(rows) == data['instance_count'] > 0, 'Empty placement')
    placement_sha = sha(placement_path)

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    require(levels.load_level(LEVEL), 'Level load failed')
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    require(not any(str(d.label).startswith(LABEL_PREFIX) for d in descriptors), 'NAIP canopy already installed')
    before_count = len(descriptors)

    # Mirror component settings from an existing captured canopy actor.
    canopy_descs = [d for d in descriptors if d.native_class.get_name() == 'RaftSimCapturedCanopyActor']
    require(canopy_descs, 'No existing canopy actor to mirror')
    unreal.WorldPartitionBlueprintLibrary.load_actors([canopy_descs[0].guid])
    reference = [a for a in subsystem.get_all_level_actors() if a.get_name() == str(canopy_descs[0].name)][0]
    ref = reference.get_editor_property('canopy_a')
    mirrored = {}
    for prop in ('cast_shadow', 'cast_dynamic_shadow', 'instance_start_cull_distance', 'instance_end_cull_distance',
                 'b_use_as_occluder', 'b_affect_distance_field_lighting', 'b_affect_dynamic_indirect_lighting'):
        try:
            mirrored[prop] = ref.get_editor_property(prop)
        except Exception:
            pass

    meshes = [unreal.load_asset(a['package']) for a in data['assets']]
    require(all(isinstance(m, unreal.StaticMesh) for m in meshes), 'Missing canopy mesh')
    bounds = [m.get_bounding_box() for m in meshes]

    cells = {}
    for row in rows:
        x, y, _ = row['world_root_cm']
        cells.setdefault((int(x // CELL_CM), int(y // CELL_CM)), []).append(row)
    canopy_class = unreal.load_class(None, '/Script/RaftSimRaft.RaftSimCapturedCanopyActor')
    require(canopy_class, 'Canopy class missing')
    created = []
    for (cx, cy), group in sorted(cells.items()):
        origin = unreal.Vector(cx * CELL_CM, cy * CELL_CM, 0)
        for gi, forms in enumerate(GROUPS):
            members = [r for r in group if r['form_index'] in forms]
            if not members:
                continue
            actor = subsystem.spawn_actor_from_class(canopy_class, origin)
            require(actor, 'Spawn failed')
            label = f'{LABEL_PREFIX} {cx} {cy} {"oak" if gi == 0 else "riparian-pine"} - imagery canopy, inferred species'
            actor.set_actor_label(label)
            actor.tags = [unreal.Name('RaftSimCapturedCanopy'), unreal.Name('RaftSimNaipCanopy'),
                          unreal.Name('InferredVegetationNotSurveyedTrees')]
            actor.set_editor_property('placement_source_sha256', placement_sha)
            count = 0
            for slot, form in enumerate(forms):
                component = actor.get_editor_property(NAMES[slot])
                require(component.set_static_mesh(meshes[form]), 'Mesh assignment failed')
                component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                component.set_editor_property('generate_overlap_events', False)
                for prop, value in mirrored.items():
                    try:
                        component.set_editor_property(prop, value)
                    except Exception:
                        pass
                b = bounds[form]
                height_cm = b.max.z - b.min.z
                transforms = []
                for r in members:
                    if r['form_index'] != form:
                        continue
                    x, y, z = r['world_root_cm']
                    s = r['height_m'] * 100.0 / height_cm
                    # Sink roots 20 cm so trunks meet sloping terrain.
                    transforms.append(unreal.Transform(
                        location=unreal.Vector(x - origin.x, y - origin.y, z - 20.0 - b.min.z * s),
                        rotation=unreal.Rotator(pitch=0, yaw=r['yaw_degrees'], roll=0),
                        scale=unreal.Vector(s, s, s)))
                if transforms:
                    component.add_instances(transforms, False, False)
                    count += len(transforms)
            created.append(dict(name=actor.get_name(), label=label, cell=[cx, cy], group=gi, instances=count))
    require(sum(c['instances'] for c in created) == len(rows), 'Instance count mismatch')

    # Sampled root check against the physical ground actually rendered.
    ground = [d for d in descriptors if str(d.label).startswith(('SouthFork_coarse_terrain_', 'SouthFork_captured_context_'))]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in ground])
    # Loaded ground has no collision until compilation is flushed; without
    # this every trace missed in the first installation's sample.
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ground_names = {str(d.name) for d in ground}
    ignore = [a for a in subsystem.get_all_level_actors() if a.get_name() not in ground_names]
    rng = random.Random(20260926)
    sample = rng.sample(rows, min(SAMPLE_TRACES, len(rows)))
    errors, misses = [], 0
    for r in sample:
        x, y, z = r['world_root_cm']
        hit = trace_ground(world, ignore, x, y, z)
        if hit is None:
            misses += 1
        else:
            errors.append(hit - z)
    errors.sort()

    require(levels.save_current_level(), 'Level save failed')
    require(unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False), 'Package save failed')
    after = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    new = [d for d in after if str(d.label).startswith(LABEL_PREFIX)]
    require(len(new) == len(created) and len(after) == before_count + len(created), 'Unexpected actor descriptor change')
    require(all(d.is_spatially_loaded for d in new), 'Canopy actors must be spatially loaded')

    def pct(p):
        return errors[min(len(errors) - 1, int(p * len(errors)))] if errors else None
    result = dict(
        schema='raftsim.south_fork_naip_canopy_integration.v1', level=LEVEL,
        placement=str(placement_path.relative_to(ROOT).as_posix()), placement_sha256=placement_sha,
        instance_count=len(rows), actor_count=len(created), cell_cm=CELL_CM,
        mirrored_component_settings={k: str(v) for k, v in mirrored.items()},
        root_trace_sample=len(sample), root_trace_misses=misses,
        root_minus_ground_cm_percentiles=dict(p01=pct(0.01), p50=pct(0.5), p99=pct(0.99)) if errors else None,
        existing_actor_descriptors=before_count, actor_descriptors_after=len(after),
        collision='none (visual canopy)', species_inferred=True, positions_from_imagery=True,
        terrain_or_hydraulic_geometry_modified=False, visual_accepted=False)
    report.write_text(json.dumps(result, indent=2) + '\n')
    unreal.log('RAFTSIM_NAIP_CANOPY_INSTALLED ' + json.dumps({k: result[k] for k in ('instance_count', 'actor_count', 'root_trace_misses', 'root_minus_ground_cm_percentiles')}))


if __name__ == '__main__':
    main()
