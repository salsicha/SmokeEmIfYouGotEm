"""Install only the nine reviewed buffer heightfields, with recoverable backups.

Run apply and verify in separate rendered editor processes. No save is possible
until the native command proves every target render vertex and both triangle
interiors in every cell agree with the source. This is terrain integration,
not a claim of playable water, canopy clearance or packaged performance.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import traceback

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_futaleufu_continuous_canopy import ROOT, LEVEL, MAP, original_files, sha

OLD = ROOT / 'tmp/futaleufu-context-terrain-v1'
NEW = ROOT / 'tmp/futaleufu-hydraulic-buffer-terrain-v1'
OLD_SHA = '503529a38131b108df9e6de3eb17a9b86967fafdb4a937e9a9d40f43e336d39d'
NEW_SHA = '540daa6e87ad06c8f5579fd005e74b8633ed48f106d32f3f67e33b2b2164dada'
OUT = ROOT / 'tmp/futaleufu-native-buffer-install-v1'
MODE = os.environ.get('RAFTSIM_BUFFER_UPDATE_MODE', '')
AUDIT_TAG = os.environ.get('RAFTSIM_BUFFER_AUDIT_TAG', '')


def write(path, data):
    with path.open('x') as f:
        json.dump(data, f, indent=2, allow_nan=False)


def source_contract():
    if sha(OLD / 'manifest.json') != OLD_SHA or sha(NEW / 'manifest.json') != NEW_SHA:
        raise RuntimeError('Reviewed terrain manifest changed')
    old = json.loads((OLD / 'manifest.json').read_text())
    new = json.loads((NEW / 'manifest.json').read_text())
    before = {tuple(c['chunk']): c for c in old['chunks']}
    if len(before) != 800 or len(new['chunks']) != 800 or old['landscape'] != new['landscape']:
        raise RuntimeError('Full terrain extent/encoding changed')
    chunks = []
    for c in new['chunks']:
        previous = before[tuple(c['chunk'])]
        for folder, row in ((OLD, previous), (NEW, c)):
            if sha(folder / row['heightfield']) != row['sha256']:
                raise RuntimeError('Changed source PNG')
        if c['sha256'] == previous['sha256']:
            continue
        if c['world_northwest_xy_cm'] != previous['world_northwest_xy_cm']:
            raise RuntimeError('Geographic terrain registration changed')
        chunks.append(dict(label='ContinuousTerrain_%d_%d' % tuple(c['chunk']),
            location_cm=c['world_northwest_xy_cm'] + [new['landscape']['actor_z_cm']],
            before=(OLD / previous['heightfield']).relative_to(ROOT).as_posix(), before_sha256=previous['sha256'],
            after=(NEW / c['heightfield']).relative_to(ROOT).as_posix(), after_sha256=c['sha256']))
    if len(chunks) != 9:
        raise RuntimeError('Exactly nine reviewed changed chunks required')
    return dict(schema='raftsim.futaleufu_buffer_native_update.v1', level=LEVEL,
        old_manifest_sha256=OLD_SHA, new_manifest_sha256=NEW_SHA, unchanged_source_chunks=791, chunks=chunks)


def snapshot():
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in original_files()}


def load_targets(contract):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):
        raise RuntimeError('Continuous scene load failed')
    labels = {r['label'] for r in contract['chunks']}
    centers = [(r['location_cm'][0]+12600, r['location_cm'][1]+12600) for r in contract['chunks']]
    roots, proxies = [], []
    for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs():
        if str(d.label) in labels and d.native_class.get_name() == 'Landscape':
            roots.append(d.guid)
        if d.native_class.get_name() == 'LandscapeStreamingProxy':
            b = d.bounds
            x, y = (b.min.x+b.max.x)/2, (b.min.y+b.max.y)/2
            if any(abs(x-cx)<1 and abs(y-cy)<1 for cx, cy in centers):
                proxies.append(d.guid)
    if len(roots) != 9 or len(proxies) != 9:
        raise RuntimeError('Nine geographically registered existing root/proxy pairs required')
    unreal.WorldPartitionBlueprintLibrary.load_actors(roots+proxies)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    if sum(isinstance(a, unreal.LandscapeStreamingProxy) for a in actors) != 9:
        raise RuntimeError('Unexpected terrain residency; do not load the full river for a local edit')
    return actors


def main():
    if MODE not in ('apply', 'verify'):
        raise RuntimeError('Explicit apply or verify mode required')
    if AUDIT_TAG and (MODE != 'verify' or not AUDIT_TAG.isalnum()):
        raise RuntimeError('Optional alphanumeric tag is for fresh read-only rechecks only')
    contract = source_contract()
    if MODE == 'apply':
        if OUT.exists():
            raise RuntimeError('Fresh output required; preserve earlier attempts')
        if sha(MAP) != '2fc8d78efc7672c43e42752e74c5e9d8796ec6f9290fdf2de814e2f7bd5aea94':
            raise RuntimeError('Existing native scene changed')
        before = snapshot()
        total = sum((ROOT / rel).stat().st_size for rel in before)
        if shutil.disk_usage(ROOT).free < 40 * 1024**3 + total + 1024**3:
            raise RuntimeError('40 GiB reserve plus verified backup capacity required')
        OUT.mkdir()
        write(OUT / 'before.json', before)
        for rel, digest in before.items():
            target = OUT / 'backup' / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, target)
            if sha(target) != digest:
                raise RuntimeError('Backup verification failed')
        write(OUT / 'request.json', contract)
    else:
        saved = json.loads((OUT / 'saved.json').read_text())
        before = json.loads((OUT / 'before.json').read_text())
        if saved['after'] != snapshot():
            raise RuntimeError('Saved scene changed before independent verification')
        if contract != json.loads((OUT / 'request.json').read_text()):
            raise RuntimeError('Source contract changed before verification')
    suffix = ('-' + AUDIT_TAG) if AUDIT_TAG else ''
    receipt = OUT / ('native-' + MODE + suffix + '.json')
    if receipt.exists():
        raise RuntimeError('Fresh native receipt required')
    actors = load_targets(contract)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    command = 'RaftSim.UpdateFutaleufuBufferTerrain %s %s %s' % (
        (OUT / 'request.json').relative_to(ROOT).as_posix(), MODE, receipt.relative_to(ROOT).as_posix())
    unreal.SystemLibrary.execute_console_command(world, command)
    result = json.loads(receipt.read_text())  # Missing receipt prevents ANY save.
    if (result['request_sha256'] != sha(OUT / 'request.json') or result['chunks'] != 9
            or result['render_vertices'] != 9 * 127**2 or result['complex_collision_probes'] != 9 * 126**2 * 2
            or result['maximum_collision_error_cm'] > 10):
        raise RuntimeError('Incomplete native terrain verification')
    if MODE == 'apply':
        if snapshot() != before:
            raise RuntimeError('Scene bytes changed before targeted save')
        packages = {a.get_package().get_name(): a.get_package() for a in actors}
        names = result['target_packages']
        if len(names) != 18 or any(name not in packages for name in names):
            raise RuntimeError('Expected nine existing root/proxy package pairs')
        if not unreal.EditorLoadingAndSavingUtils.save_packages([packages[n] for n in names], False):
            raise RuntimeError('Targeted terrain package save failed; backup retained')
        after = snapshot()
        allowed = {'unreal/Content/' + n.removeprefix('/Game/') + '.uasset' for n in names}
        changed = {rel for rel in before if after.get(rel) != before[rel]}
        if set(after) != set(before) or not changed or not changed.issubset(allowed):
            raise RuntimeError('Unexpected package changes; inspect verified backup before proceeding')
        write(OUT / 'saved.json', dict(after=after, changed_packages=sorted(changed),
            unchanged_packages=len(before)-len(changed), native_receipt_sha256=sha(receipt),
            source_manifest_sha256=NEW_SHA, fresh_process_reload_verified=False,
            canopy_update_pending=True, playable_water_integrated=False))
    else:
        if snapshot() != saved['after']:
            raise RuntimeError('Read-only reload audit changed saved packages')
        write(OUT / ('verified'+suffix+'.json'), dict(native=result, saved_receipt_sha256=sha(OUT / 'saved.json'),
            read_only_fresh_process=True, saved_packages_unchanged=True, backup_verified=True,
            canopy_update_pending=True, playable_water_integrated=False, packaged_performance_accepted=False))
    unreal.log('Futaleufu native buffer terrain ' + MODE + ': ' + json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Never replace earlier evidence or automatically overwrite assets with
        # backups. A failed save needs explicit inspection of exact packages.
        if OUT.exists() and not (OUT / ('failure-' + MODE + '.txt')).exists():
            (OUT / ('failure-' + MODE + '.txt')).write_text(traceback.format_exc())
        raise
    # -ExecutePythonScript owns editor shutdown. Do not request a second exit
    # from Python; the outer runner must still check the actual process status.
