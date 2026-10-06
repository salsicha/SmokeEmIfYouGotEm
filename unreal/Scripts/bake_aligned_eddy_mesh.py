"""Bake native mesh diagnostics from preserved aligned eddy data, not acceptance."""
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
from water_feature_mesh_preflight import validate_completed_data_settings


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = Path(bpy.data.filepath).resolve()
    root = source.parent
    setup = json.loads((root/'setup.json').read_text())
    preflight = json.loads((root/'alignment-data-audit.json').read_text())
    mapping = json.loads((root/'particle-mapping-v1.json').read_text())
    base = json.loads((root/'bake-data.json').read_text())
    domain = bpy.data.objects['Feature liquid']
    settings = domain.modifiers[0].domain_settings
    cache = Path(bpy.path.abspath(settings.cache_directory)).resolve()
    output = root/'feature-mesh.blend'
    receipt, marker = root/'bake-mesh.json', root/'bake-mesh-in-progress.json'
    if (setup['case'] != 'eddy' or not setup.get('grid_aligned_domain')
            or setup.get('rejected_before_bake') or settings.cache_type != 'MODULAR'
            or setup.get('bake_schedule') != 'MODULAR'
            or Path(setup['blend']).resolve() != source or cache != root/'cache'):
        raise ValueError('Only the explicitly aligned modular eddy base is in scope')
    if not (preflight['complete'] and preflight['original_unchanged']
            and preflight['other_physical_domain_settings_match']
            and len(preflight['native_data_checks']) == 3
            and mapping['complete'] and mapping['originals_unchanged']
            and all(row['isotropic_native_positions_and_velocities_match']
                    and row['errors']['engine_field']['max_component_error_m'] <= 1e-6
                    for row in mapping['frames'])
            and base['result'] == ['FINISHED'] and base['baked_data']):
        raise ValueError('Completed native base/geometry/mapping checks required')
    transitions = validate_completed_data_settings(
        json.loads((root/'domain-settings.json').read_text()), settings_snapshot(settings),
        settings.cache_frame_end)
    if not settings.use_mesh or not settings.has_cache_baked_data:
        raise ValueError('Enabled mesh and complete loaded base data required')
    if (settings.has_cache_baked_mesh or settings.has_cache_baked_particles
            or any(p.is_file() for folder in ('mesh', 'particles') for p in (cache/folder).rglob('*'))
            or any(p.exists() for p in (output, receipt, marker, root/'bake-data-in-progress.json'))):
        raise FileExistsError('Existing stage/partial evidence: inspect, do not repeat')
    frames = range(settings.cache_frame_start, settings.cache_frame_end+1)
    data = [cache/'data'/f'fluid_data_{frame:04d}.vdb' for frame in frames]
    if len(data) != base['data_frames'] or any(not p.is_file() or p.stat().st_size == 0 for p in data):
        raise ValueError('Base frame coverage incomplete')
    if shutil.disk_usage(root).free < 6*1024**3:
        raise RuntimeError('Need 6 GiB free before diagnostic mesh stage')
    source_hash = digest(source)
    hashes = {p.name: digest(p) for p in data}
    with marker.open('x') as stream:
        json.dump(dict(pid=os.getpid(), stage='MESH', source_blend=str(source),
                       source_blend_sha256=source_hash, started_unix=time.time()), stream)
    bpy.ops.object.select_all(action='DESELECT')
    domain.select_set(True)
    bpy.context.view_layer.objects.active = domain
    start = time.monotonic()
    result = bpy.ops.fluid.bake_mesh()
    elapsed = time.monotonic()-start
    if digest(source) != source_hash or any(digest(p) != hashes[p.name] for p in data):
        raise RuntimeError('Base evidence changed; preserve diagnostic marker')
    meshes = [cache/'mesh'/f'fluid_mesh_{frame:04d}.bobj.gz' for frame in frames]
    complete = all(p.is_file() and p.stat().st_size > 0 for p in meshes)
    report = dict(stage='MESH', diagnostic_only=True, result=list(result),
                  bake_seconds=elapsed, baked_mesh=settings.has_cache_baked_mesh,
                  mesh_frames=sum(p.is_file() and p.stat().st_size > 0 for p in meshes),
                  mesh_bytes=sum(p.stat().st_size for p in meshes if p.is_file()),
                  baked_particles=settings.has_cache_baked_particles,
                  source_blend=str(source), source_blend_sha256=source_hash,
                  source_blend_unchanged=True, original_data_sha256=hashes,
                  original_data_unchanged=True, blend=str(output),
                  permitted_data_state_transitions=transitions,
                  physical_accuracy_accepted=False, visual_accuracy_accepted=False,
                  scope='Native mesh/contact diagnostic. No data rebake, mass correction, mesh clipping or secondary-phase acceptance.')
    with receipt.open('x') as stream:
        json.dump(report, stream, indent=2)
    if 'FINISHED' not in result or not settings.has_cache_baked_mesh or not complete:
        raise RuntimeError('Incomplete native mesh stage; preserve marker/evidence')
    # A fresh artifact preserves both the original base blend and its backup.
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    marker.unlink()  # This invocation's successful marker only.
    print('ALIGNED_EDDY_MESH_BAKED', json.dumps({k: v for k, v in report.items()
                                               if k != 'original_data_sha256'}), flush=True)


if __name__ == '__main__':
    main()
