"""Bake native secondary phases in an independent preserved-liquid cache copy."""
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(secondary_model=None):
    source = Path(bpy.data.filepath).resolve()
    root = source.parent
    setup = json.loads((root/'setup.json').read_text())
    preflight = json.loads((root/'secondary-preflight.json').read_text())
    domain = bpy.data.objects['Feature liquid']
    state = domain.modifiers[0].domain_settings
    cache = Path(bpy.path.abspath(state.cache_directory)).resolve()
    receipt, marker, output = root/'bake-particles.json', root/'bake-particles-in-progress.json', root/'feature-phases.blend'
    if (setup['case'] != 'eddy' or not setup.get('grid_aligned_domain')
            or source != Path(setup['blend']).resolve() or cache != root/'cache'
            or not preflight['complete'] or not preflight['original_unchanged']
            or not preflight['independently_copied'] or not preflight['physical_settings_unchanged']
            or not state.has_cache_baked_data or not state.has_cache_baked_mesh
            or state.has_cache_baked_particles or state.cache_type != 'MODULAR'
            or not all((state.use_foam_particles, state.use_spray_particles, state.use_bubble_particles))
            or settings_snapshot(state) != preflight['domain_settings']):
        raise ValueError('Independent completed aligned base/mesh preflight required')
    if (any(p.exists() for p in (receipt, marker, output))
            or any(p.is_file() for p in (cache/'particles').rglob('*'))):
        raise FileExistsError('Existing secondary evidence; do not duplicate stage')
    frames = range(state.cache_frame_start, state.cache_frame_end+1)
    preserved = {name: value for name, value in preflight['copied_cache_file_sha256'].items()
                 if Path(name).parts[0] in ('data', 'mesh')}
    original_cache = Path(preflight['source_cache'])
    for name, value in preflight['copied_cache_file_sha256'].items():
        if digest(cache/name) != value or digest(original_cache/name) != value:
            raise RuntimeError('Preflight/source cache differs')
    for frame in frames:
        if any(not (cache/folder/name).is_file() for folder, name in
               [('data', f'fluid_data_{frame:04d}.vdb'), ('mesh', f'fluid_mesh_{frame:04d}.bobj.gz')]):
            raise ValueError('Incomplete input frame coverage')
    if shutil.disk_usage(root).free < 6*1024**3:
        raise RuntimeError('Need6GiB reserve')
    source_hash = digest(source)
    with marker.open('x') as stream:
        json.dump(dict(pid=os.getpid(), stage='PARTICLES', started_unix=time.time()), stream)
    bpy.ops.object.select_all(action='DESELECT')
    domain.select_set(True)
    bpy.context.view_layer.objects.active = domain
    start = time.monotonic()
    result = bpy.ops.fluid.bake_particles()
    elapsed = time.monotonic()-start
    for name, value in preserved.items():
        if digest(cache/name) != value:
            raise RuntimeError('Copied base/mesh changed; preserve failed marker')
    for name, value in preflight['copied_cache_file_sha256'].items():
        if digest(original_cache/name) != value:
            raise RuntimeError('Original source cache changed')
    if digest(source) != source_hash or digest(Path(preflight['source_blend'])) != preflight['source_blend_sha256']:
        raise RuntimeError('Original scene changed')
    particles = [cache/'particles'/f'fluid_particles_{frame:04d}.vdb' for frame in frames]
    complete = all(p.is_file() and p.stat().st_size > 0 for p in particles)
    report = dict(stage='PARTICLES', diagnostic_only=True, result=list(result),
        bake_seconds=elapsed, baked_particles=state.has_cache_baked_particles,
        particle_frames=sum(p.is_file() and p.stat().st_size > 0 for p in particles),
        particle_bytes=sum(p.stat().st_size for p in particles if p.is_file()),
        source_blend=str(source), source_blend_sha256=source_hash, originals_unchanged=True,
        preserved_data_mesh_sha256=preserved, copied_data_mesh_unchanged=True,
        blend=str(output), physical_accuracy_accepted=False, visual_accuracy_accepted=False,
        scope='Native one-way secondary particle phase study, not resolved gas interfaces, calibrated generation or physical eddy acceptance.')
    if secondary_model is not None:
        report['simulation_correction'] = secondary_model.report()
        report['simulation_correction_verified'] = (
            secondary_model.calls == len(particles) and secondary_model.total_changed > 0)
        report['scope'] = ('Native secondary transport with independently checked bounded occupancy '
            'completion before classification. Fresh simulation, not cached phase relabeling. '
            'Surface placement, kinetics, optical density and eddy physics remain unaccepted.')
    with receipt.open('x') as stream:
        json.dump(report, stream, indent=2)
    if 'FINISHED' not in result or not state.has_cache_baked_particles or not complete:
        raise RuntimeError('Incomplete secondary bake; preserve marker')
    if secondary_model is not None and not report['simulation_correction_verified']:
        raise RuntimeError('Stage hook coverage failed; preserve unqualified evidence/marker')
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    marker.unlink()  # Successful marker owned by this invocation only.
    print('EDDY_SECONDARY_BAKED', json.dumps({k: v for k, v in report.items()
                                            if k != 'preserved_data_mesh_sha256'}), flush=True)


if __name__ == '__main__':
    main()
