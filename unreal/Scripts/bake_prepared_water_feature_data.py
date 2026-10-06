"""Bake only the base liquid stage of an explicitly prepared modular case."""
import json
import os
from pathlib import Path
import shutil
import sys
import time
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_modular_water_feature import settings_snapshot


def main():
    blend = Path(bpy.data.filepath).resolve()
    root = blend.parent
    setup = json.loads((root/'setup.json').read_text())
    if setup.get('rejected_before_bake'):
        raise ValueError('Prepared case failed its physical preflight; preserve it as evidence, do not bake')
    domain = bpy.data.objects['Feature liquid']
    settings = domain.modifiers[0].domain_settings
    cache = Path(bpy.path.abspath(settings.cache_directory)).resolve()
    receipt, marker = root/'bake-data.json', root/'bake-data-in-progress.json'
    if cache != root/'cache' or Path(setup['blend']).resolve() != blend:
        raise ValueError('Prepared scene/cache path mismatch')
    if settings.cache_type != 'MODULAR' or setup.get('bake_schedule') != 'MODULAR':
        raise ValueError('Explicit modular preparation required')
    if settings_snapshot(settings) != json.loads((root/'domain-settings.json').read_text()):
        raise ValueError('Prepared domain settings changed')
    if receipt.exists() or marker.exists() or any(path.is_file() for path in cache.rglob('*')):
        raise FileExistsError('Existing stage/partial data: preserve and inspect, do not repeat')
    if shutil.disk_usage(root).free < 3*1024**3:
        raise RuntimeError('Need 3 GiB for base liquid stage and reserve; no bake started')
    if settings.has_cache_baked_data:
        raise ValueError('Data already baked')
    with marker.open('x') as stream:
        json.dump(dict(pid=os.getpid(), started_unix=time.time(), stage='DATA', blend=str(blend)), stream)
    bpy.ops.object.select_all(action='DESELECT')
    domain.select_set(True)
    bpy.context.view_layer.objects.active = domain
    start = time.monotonic()
    result = bpy.ops.fluid.bake_data()
    expected = [cache/'data'/f'fluid_data_{frame:04d}.vdb'
                for frame in range(settings.cache_frame_start, settings.cache_frame_end+1)]
    deferred = [p for name in ('mesh', 'particles') for p in (cache/name).glob('*') if p.is_file()]
    report = dict(stage='DATA', bake_seconds=time.monotonic()-start, result=list(result),
                  baked_data=settings.has_cache_baked_data,
                  baked_mesh=settings.has_cache_baked_mesh,
                  baked_particles=settings.has_cache_baked_particles,
                  data_frames=sum(path.is_file() and path.stat().st_size > 0 for path in expected),
                  cache_bytes=sum(path.stat().st_size for path in cache.rglob('*') if path.is_file()),
                  physical_accuracy_accepted=False, visual_accuracy_accepted=False)
    receipt.write_text(json.dumps(report, indent=2))
    if 'FINISHED' not in result or not report['baked_data'] or report['data_frames'] != len(expected) or deferred:
        raise RuntimeError('Incomplete or unexpectedly expanded data bake; preserve marker/cache')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    marker.unlink()  # Only this successful invocation's marker; never cached evidence.
    print('MODULAR_DATA_BAKED', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
