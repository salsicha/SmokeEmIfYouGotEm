"""Retain exact native collision sources through cooking; save no maps.

RAFTSIM_GROUND_CPU_CONFIG selects an explicit, hash-locked local configuration.
Original packages are backed up before the first save. Partial receipts permit
resuming only unchanged inputs and already-proven resulting packages.
"""
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
IDENTITY = ('format', 'collision_lod', 'collision_trace_flag',
            'collision_source_sha256', 'triangle_count', 'provider_vertex_count', 'flip_normals')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def unchanged_source(before, after):
    if not before.get('available') or not after.get('available'):
        raise ValueError('Native collision source unavailable')
    if not after.get('allow_cpu_access'):
        raise ValueError('CPU source retention disabled')
    if any(key not in before or key not in after or before[key] != after[key] for key in IDENTITY):
        raise ValueError('Original collision source changed')
    if len(before['collision_source_sha256']) != 64 or before['triangle_count'] <= 0:
        raise ValueError('Complete native source identity required')


def package_file(asset):
    prefixes = ('/Game/RaftSim/Environment/SouthForkReconstruction/',
                '/Game/RaftSim/Environment/GeneratedLocalReview/')
    if not asset.startswith(prefixes) or any(not part or not part.replace('_', '').isalnum() for part in asset[1:].split('/')):
        raise ValueError('Explicit South Fork source mesh required')
    return ROOT/'unreal/Content'/(asset[6:]+'.uasset')


def main():
    import unreal
    config_path = Path(os.environ['RAFTSIM_GROUND_CPU_CONFIG']).resolve()
    config = json.loads(config_path.read_text())
    report_path, backup_path = ((ROOT/config[key]).resolve() for key in ('report', 'backup'))
    output = (ROOT/config['cooked_expected']).resolve()
    if not output.is_relative_to(ROOT/'tmp') or output.exists():
        raise ValueError('Fresh local cooked-source expectation required')
    if not backup_path.is_relative_to(ROOT/'tmp') or not report_path.is_relative_to(ROOT/'docs/reconstruction-review-2026-09-07'):
        raise ValueError('Local backup and versioned provenance receipt required')
    records = config['assets']
    if not records or len({row['asset'] for row in records}) != len(records):
        raise ValueError('Nonempty unique source inventory required')
    report = json.loads(report_path.read_text()) if report_path.exists() else dict(
        schema='raftsim.ground_cpu_retention.v1', config_sha256=digest(config_path),
        completed=False, maps_saved=False, cooked_verified=False, assets=[])
    assert report['config_sha256'] == digest(config_path)
    previous = {row['asset']: row for row in report['assets']}
    # Check the entire requested set before any asset mutation.
    for row in records:
        expected = previous[row['asset']]['retained_asset_sha256'] if row['asset'] in previous else row['asset_sha256']
        assert digest(package_file(row['asset'])) == expected, row['asset']
    if not backup_path.exists():
        assert not previous
        with zipfile.ZipFile(backup_path, 'x', zipfile.ZIP_STORED) as backup:
            for row in records:
                path = package_file(row['asset'])
                backup.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(backup_path) as backup:
        for row in records:
            path = package_file(row['asset']).relative_to(ROOT).as_posix()
            assert hashlib.sha256(backup.read(path)).hexdigest() == row['asset_sha256']
    for index, row in enumerate(records):
        mesh = unreal.load_asset(row['asset'])
        assert isinstance(mesh, unreal.StaticMesh)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        before = json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(mesh))
        assert before['available'] and before['triangle_count'] == row['triangle_count']
        if row['asset'] in previous:
            unchanged_source(previous[row['asset']]['before'], before)
            continue
        material_paths = [slot.material_interface.get_path_name() if slot.material_interface else None
                          for slot in mesh.get_editor_property('static_materials')]
        mesh.set_editor_property('allow_cpu_access', True)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        after = json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(mesh))
        unchanged_source(before, after)
        assert material_paths == [slot.material_interface.get_path_name() if slot.material_interface else None
                                  for slot in mesh.get_editor_property('static_materials')]
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        report['assets'].append(dict(asset=row['asset'], original_asset_sha256=row['asset_sha256'],
            retained_asset_sha256=digest(package_file(row['asset'])), before=before, after=after,
            native_source_unchanged=True, material_paths=material_paths))
        report_path.write_text(json.dumps(report, indent=2)+'\n')
        if index % 25 == 0:
            unreal.log(f'Exact ground CPU retention: {index+1}/{len(records)}')
            unreal.SystemLibrary.collect_garbage()
    report['completed'] = len(report['assets']) == len(records)
    report_path.write_text(json.dumps(report, indent=2)+'\n')
    assert report['completed']
    output.write_text(json.dumps(dict(assets=[dict(asset=row['asset'],
        **{key: row['after'][key] for key in IDENTITY}) for row in report['assets']]), indent=2)+'\n')
    unreal.log(f'Original collision triangles retained for {len(records)} assets: {report_path}')


if __name__ == '__main__':
    main()
