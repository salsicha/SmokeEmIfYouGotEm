"""Apply reviewed buffer exclusions through native foliage metadata, then reload.

All retained source transforms remain exact. Only affected existing foliage
packages are saved; every other scene package must remain byte-identical.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import traceback

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_futaleufu_continuous_canopy import ROOT, LEVEL, sha
from update_futaleufu_native_buffers import snapshot, write

OLD = ROOT/'tmp/futaleufu-continuous-canopy-v2/placement.json'
NEW = ROOT/'tmp/futaleufu-hydraulic-buffer-canopy-v1/placement.json'
TERRAIN = ROOT/'tmp/futaleufu-native-buffer-install-v1'
OUT = ROOT/'tmp/futaleufu-native-buffer-canopy-v1'
MODE = os.environ.get('RAFTSIM_BUFFER_CANOPY_MODE', '')


def exclusion_contract(old, new):
    rows = [r for c in old['chunks'] for r in c['instances']]
    retained = [r for c in new['chunks'] for r in c['instances']]
    excluded = {r['parent_flat_index'] for r in new['hydraulic_buffer_update']['excluded_instances']}
    if len(rows) != 251317 or len(retained) != 251275 or len(excluded) != 42 or not excluded.issubset(range(len(rows))):
        raise RuntimeError('Complete original/new canopy and exactly 42 exclusions required')
    expected = [r for i, r in enumerate(rows) if i not in excluded]
    for before, after in zip(expected, retained):
        a = {k: v for k, v in before.items() if k != 'source_water_clearance_m'}
        b = {k: v for k, v in after.items() if k != 'source_water_clearance_m'}
        if a != b:
            raise RuntimeError('Retained source transform or appearance changed')
    remove = []
    for i in sorted(excluded):
        r = rows[i]
        remove.append(dict(parent_flat_index=i, mesh_asset=old['meshes'][r['mesh']]['asset'],
            location_cm=r['location_cm'], scale_xyz=r['scale_xyz'], yaw_deg=r['yaw_deg']))
    return dict(schema='raftsim.futaleufu_buffer_canopy_update.v1', remove=remove,
        old_instances=len(rows), retained_instances=len(retained))


def load_targets(contract, packages=None):
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL):
        raise RuntimeError('Continuous scene load failed')
    descs = []
    for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs():
        if d.native_class.get_name() != 'InstancedFoliageActor':
            continue
        b = d.bounds
        if packages is not None:
            include = str(d.actor_package) in packages
        else:
            include = any(b.min.x-1 <= r['location_cm'][0] <= b.max.x+1 and
                          b.min.y-1 <= r['location_cm'][1] <= b.max.y+1 for r in contract['remove'])
        if include:
            descs.append(d)
    if not descs or (packages is not None and len(descs) != len(packages)):
        raise RuntimeError('Missing native foliage descriptors')
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    actors = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
              if isinstance(a, unreal.InstancedFoliageActor)]
    if len(actors) != len(descs):
        raise RuntimeError('Unexpected foliage residency')
    return actors


def settings(actors):
    result = {}
    for a in actors:
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            result[c.get_path_name()] = dict(mesh=c.static_mesh.get_path_name(),
                materials=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())],
                collision=str(c.get_collision_enabled()), start=c.get_editor_property('instance_start_cull_distance'),
                end=c.get_editor_property('instance_end_cull_distance'))
    return result


def main():
    if MODE not in ('apply', 'verify'):
        raise RuntimeError('Explicit apply or verify mode required')
    if (sha(OLD) != '26a19b0900197e807997caca46dd484bade332fc58a522e7f40ba01a52df2a04' or
            sha(NEW) != '440a578b1a9e53e97fca8afe2fa7cf27384e42ee4bba974204308bc63aa9fbad'):
        raise RuntimeError('Reviewed canopy source changed')
    contract = exclusion_contract(json.loads(OLD.read_text()), json.loads(NEW.read_text()))
    contract.update(old_plan_sha256=sha(OLD), new_plan_sha256=sha(NEW))
    before = snapshot()
    if MODE == 'apply':
        if OUT.exists():
            raise RuntimeError('Fresh installation required; retain previous evidence')
        verified = json.loads((TERRAIN/'verified-v2.json').read_text())
        terrain_saved = json.loads((TERRAIN/'saved.json').read_text())
        if not verified['saved_packages_unchanged'] or terrain_saved['after'] != before:
            raise RuntimeError('Saved, reloaded buffer terrain must match the current scene')
        actors = load_targets(contract)
        names = sorted(a.get_package().get_name() for a in actors)
        contract['loaded_foliage_packages'] = names
        if shutil.disk_usage(ROOT).free < 41*1024**3:
            raise RuntimeError('40 GiB reserve and backup capacity required')
        OUT.mkdir()
        write(OUT/'before.json', before)
        write(OUT/'request.json', contract)
        old_settings = settings(actors)
        write(OUT/'settings.json', old_settings)
        for name in names:
            rel = 'unreal/Content/'+name.removeprefix('/Game/')+'.uasset'
            target = OUT/'backup'/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/rel, target)
            if sha(target) != before[rel]:
                raise RuntimeError('Native foliage backup verification failed')
    else:
        saved = json.loads((OUT/'saved.json').read_text())
        if saved['after'] != before:
            raise RuntimeError('Scene changed before independent canopy reload')
        request = json.loads((OUT/'request.json').read_text())
        contract['loaded_foliage_packages'] = request['loaded_foliage_packages']
        if contract != request:
            raise RuntimeError('Canopy exclusion source changed')
        actors = load_targets(contract, contract['loaded_foliage_packages'])
        old_settings = json.loads((OUT/'settings.json').read_text())
    receipt = OUT/('native-'+MODE+'.json')
    if receipt.exists():
        raise RuntimeError('Fresh native receipt required')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, 'RaftSim.UpdateFutaleufuBufferCanopy %s %s %s' % (
        (OUT/'request.json').relative_to(ROOT).as_posix(), MODE, receipt.relative_to(ROOT).as_posix()))
    native = json.loads(receipt.read_text())
    if (native['request_sha256'] != sha(OUT/'request.json') or not native['all_exclusions_absent_after_operation']
            or not native['native_metadata_matches_render_instances'] or settings(actors) != old_settings):
        raise RuntimeError('Native foliage metadata/render/settings verification failed')
    if MODE == 'apply':
        if native['removed_instances'] != 42 or snapshot() != before:
            raise RuntimeError('Incomplete native exclusion or premature save')
        packages = {a.get_package().get_name(): a.get_package() for a in actors}
        names = native['target_packages']
        if not names or any(n not in packages for n in names):
            raise RuntimeError('Unknown target foliage package')
        if not unreal.EditorLoadingAndSavingUtils.save_packages([packages[n] for n in names], False):
            raise RuntimeError('Targeted native foliage save failed; backup retained')
        after = snapshot()
        allowed = {'unreal/Content/'+n.removeprefix('/Game/')+'.uasset' for n in names}
        changed = {p for p in before if after.get(p) != before[p]}
        if set(after) != set(before) or changed != allowed:
            raise RuntimeError('Unexpected package mutation; inspect backup')
        write(OUT/'saved.json', dict(after=after, changed_packages=sorted(changed),
            unchanged_packages=len(before)-len(changed), native=native, normal_map_modified=False))
    else:
        if (native['retained_native_metadata_sha256'] != saved['native']['retained_native_metadata_sha256'] or
                native['retained_loaded_instances'] != saved['native']['retained_loaded_instances'] or snapshot() != before):
            raise RuntimeError('Serialized retained foliage changed')
        write(OUT/'verified.json', dict(native=native, saved_receipt_sha256=sha(OUT/'saved.json'),
            retained_total_instances=251275, removed_total_instances=42, fresh_process_reload_verified=True,
            retained_settings_unchanged=True, saved_packages_unchanged=True,
            normal_playable_map_modified=False, water_raft_integration_pending=True))
    unreal.log('Native buffer canopy '+MODE+': '+json.dumps(native))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists() and not (OUT/('failure-'+MODE+'.txt')).exists():
            (OUT/('failure-'+MODE+'.txt')).write_text(traceback.format_exc())
        raise
    # The ExecutePythonScript runner owns shutdown; no duplicate quit request.
