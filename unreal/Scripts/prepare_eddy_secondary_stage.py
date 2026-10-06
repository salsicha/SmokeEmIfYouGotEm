"""Prepare an independent cache copy for native eddy secondary-phase studies."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_modular_water_feature import settings_snapshot


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    source = Path(bpy.data.filepath).resolve()
    root, output = source.parent, args.output.resolve()
    lab = Path(__file__).resolve().parents[2]/'tmp'/'water-feature-lab'
    if output.parent != lab or output.exists():
        raise ValueError('Fresh direct child of workspace feature lab required')
    setup = json.loads((root/'setup.json').read_text())
    mesh = json.loads((root/'bake-mesh.json').read_text())
    state = bpy.data.objects['Feature liquid'].modifiers[0].domain_settings
    cache = Path(bpy.path.abspath(state.cache_directory)).resolve()
    if (setup['case'] != 'eddy' or not setup.get('grid_aligned_domain')
            or source != Path(mesh['blend']).resolve() or not mesh['baked_mesh']
            or not mesh['original_data_unchanged'] or state.cache_type != 'MODULAR'
            or not state.has_cache_baked_data or not state.has_cache_baked_mesh
            or state.has_cache_baked_particles or cache != root/'cache'
            or not all((state.use_foam_particles, state.use_spray_particles, state.use_bubble_particles))
            or any(p.is_file() for p in (cache/'particles').rglob('*'))):
        raise ValueError('Completed aligned data/mesh, enabled unbaked secondary phases required')
    hashes = {str(p.relative_to(cache)): digest(p) for p in cache.rglob('*') if p.is_file()}
    byte_count = sum((cache/p).stat().st_size for p in hashes)
    if shutil.disk_usage(root).free < byte_count+6*1024**3:
        raise RuntimeError('Need full independent copy plus6GiB reserve')
    source_hash, before = digest(source), settings_snapshot(state)
    output.mkdir()
    # Real copies, never hard links/reflinks into a stage that can write config.
    shutil.copytree(cache, output/'cache', copy_function=shutil.copy2)
    for name, value in hashes.items():
        if digest(cache/name) != value or digest(output/'cache'/name) != value:
            raise RuntimeError('Copy/source hash mismatch; preserve partial evidence')
    state.cache_directory = str(output/'cache')
    if settings_snapshot(state) != before:
        raise RuntimeError('Cache relocation changed other domain settings')
    blend = output/'feature.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    if digest(source) != source_hash:
        raise RuntimeError('Original mesh blend changed')
    setup.update(blend=str(blend), secondary_staged_from=str(source),
                 secondary_staged_from_sha256=source_hash,
                 staging_scope='Independent copied base/mesh; original physical settings and cached motion retained. Secondary phases unqualified.')
    with (output/'setup.json').open('x') as stream:
        json.dump(setup, stream, indent=2)
    with (output/'secondary-preflight.json').open('x') as stream:
        json.dump(dict(complete=True, original_unchanged=True, source_blend=str(source),
            source_blend_sha256=source_hash, source_cache=str(cache),
            copied_cache_file_sha256=hashes, copied_bytes=byte_count,
            physical_settings_unchanged=True, domain_settings=before,
            independently_copied=True, physical_accuracy_accepted=False), stream, indent=2)
    print('SECONDARY_PREPARED', str(blend), byte_count, flush=True)


if __name__ == '__main__':
    main()
