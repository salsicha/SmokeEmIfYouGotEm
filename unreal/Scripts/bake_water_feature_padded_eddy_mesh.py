"""Guarded native mesh stage for a completed fresh padded-bed eddy candidate."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_modular_water_feature import settings_snapshot


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    source = Path(bpy.data.filepath).resolve()
    root = source.parent
    proof = json.loads((root/'padding-preflight.json').read_text())
    bake = json.loads((root/'bake-data.json').read_text())
    domain = bpy.data.objects['Feature liquid']
    state = domain.modifiers[0].domain_settings
    cache = Path(bpy.path.abspath(state.cache_directory)).resolve()
    receipt, marker = root/'bake-mesh.json', root/'bake-mesh-in-progress.json'
    if not proof['complete'] or proof['accepted'] or cache != root/'cache' or state.cache_type != 'MODULAR':
        raise ValueError('Fresh padded modular candidate required')
    if not bake['baked_data'] or bake['data_frames'] != 192 or not state.has_cache_baked_data:
        raise ValueError('Complete192-frame native DATA required')
    if receipt.exists() or marker.exists() or state.has_cache_baked_mesh:
        raise FileExistsError('Existing mesh stage: preserve, do not repeat')
    if any(p.is_file() for p in (cache/'mesh').rglob('*')):
        raise FileExistsError('Unexpected existing mesh evidence')
    if settings_snapshot(state) != json.loads((root/'domain-settings.json').read_text()):
        # Baked flags and pause fields are completion metadata, not physics.
        before = json.loads((root/'domain-settings.json').read_text())
        difference = {k for k,v in settings_snapshot(state).items() if v != before[k]}
        if any(not (k.startswith('has_cache_baked_') or k.startswith('cache_frame_pause_')) for k in difference):
            raise ValueError('Physical solver settings changed')
    if shutil.disk_usage(root).free < 3*1024**3:
        raise RuntimeError('Need3GiB reserve before mesh stage')
    hashes = dict(proof['dependency_sha256'])
    for p in (root/'padding-preflight.json', root/'bake-data.json', root/'setup.json',
              Path(__file__), Path(__file__).with_name('bake_prepared_water_feature_data.py')):
        hashes[str(p.resolve())] = digest(p)
    data = {str(p.resolve()): digest(p) for name in ('data','config')
            for p in (cache/name).rglob('*') if p.is_file()}
    if any(digest(p) != sha for p,sha in hashes.items()):
        raise ValueError('Pinned source changed before native mesh')
    with marker.open('x') as stream:
        json.dump(dict(pid=os.getpid(), stage='MESH', started_unix=time.time()), stream)
    bpy.ops.object.select_all(action='DESELECT')
    domain.select_set(True)
    bpy.context.view_layer.objects.active = domain
    start = time.perf_counter()
    result = bpy.ops.fluid.bake_mesh()
    expected = [cache/'mesh'/f'fluid_mesh_{f:04d}.bobj.gz' for f in range(1,193)]
    if ('FINISHED' not in result or not state.has_cache_baked_mesh
            or any(not p.is_file() or p.stat().st_size <= 0 for p in expected)):
        raise RuntimeError('Incomplete native mesh stage; preserve marker/evidence')
    if any(digest(p) != sha for p,sha in {**hashes, **data}.items()):
        raise ValueError('Native meshing changed source or base liquid')
    output = root/'feature-mesh.blend'
    if output.exists():
        raise FileExistsError(output)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    mesh_hashes = {str(p.resolve()): digest(p) for p in (cache/'mesh').rglob('*') if p.is_file()}
    report = dict(complete=True, accepted=False, baked_mesh=True, result=list(result),
        blend=str(output), data_unchanged=True, data_frames=192, mesh_frames=192,
        elapsed_s=time.perf_counter()-start, dependency_sha256=hashes,
        data_sha256=data, mesh_sha256=mesh_hashes, output_blend_sha256=digest(output), scope=__doc__)
    with receipt.open('x') as stream:
        json.dump(report, stream, indent=2)
    marker.unlink()
    print('PADDED_EDDY_MESH_BAKED', report['mesh_frames'], report['elapsed_s'], flush=True)


if __name__ == '__main__':
    main()
