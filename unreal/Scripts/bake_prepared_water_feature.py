"""Bake one previously prepared feature.blend, refusing existing cache data.

Run Blender with the prepared blend open. No cache is erased or overwritten.
The preparation and this bake receipt remain separate provenance records.
"""
import json
from pathlib import Path
import time

import bpy


def main():
    root = Path(bpy.data.filepath).resolve().parent
    setup = json.loads((root/'setup.json').read_text())
    if Path(setup['blend']).resolve() != Path(bpy.data.filepath).resolve():
        raise ValueError('Setup/blend mismatch')
    receipt = root/'bake.json'
    lock = root/'bake-in-progress.json'
    if receipt.exists() or lock.exists():
        raise FileExistsError('Bake receipt or live-work marker exists; inspect before acting')
    domain = bpy.data.objects['Feature liquid']
    settings = domain.modifiers[0].domain_settings
    cache = Path(bpy.path.abspath(settings.cache_directory)).resolve()
    if cache != (root/'cache').resolve():
        raise ValueError('Cache outside prepared case')
    if any(p.is_file() for p in cache.rglob('*')):
        raise FileExistsError('Existing cache files: will not overwrite or repeat a partial bake')
    if settings.has_cache_baked_data or settings.has_cache_baked_mesh:
        raise ValueError('Blend already declares a baked cache')
    if settings.resolution_max != setup['resolution'] or bpy.context.scene.frame_end != setup['frames']:
        raise ValueError('Settings changed since preparation')
    with lock.open('x') as out:
        json.dump(dict(blend=bpy.data.filepath, started_unix=time.time()), out)
    bpy.ops.object.select_all(action='DESELECT')
    domain.select_set(True)
    bpy.context.view_layer.objects.active = domain
    start = time.monotonic()
    result = bpy.ops.fluid.bake_all()
    report = dict(setup, bake_seconds=time.monotonic()-start, bake_result=list(result),
                  baked_data=settings.has_cache_baked_data,
                  baked_mesh=settings.has_cache_baked_mesh,
                  baked_particles=settings.has_cache_baked_particles,
                  baked_from_prepared_scene=True)
    receipt.write_text(json.dumps(report, indent=2))
    if 'FINISHED' not in result or not all(report[k] for k in ('baked_data','baked_mesh','baked_particles')):
        raise RuntimeError('Incomplete bake; retain cache and marker for diagnosis')
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    # Only this invocation's marker is removed after a complete receipt/save.
    lock.unlink()
    print('PREPARED_BAKE_RESULT', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
