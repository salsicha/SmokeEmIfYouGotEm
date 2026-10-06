"""Fresh native same-duration eddy controls, including host sources/obstacles.

Copy only the resumable seed; never hard-link or free an original cache. Native
data and mesh stages write only to a newly created dedicated laboratory child.
Observations do not change step inputs/code or substitute foam particles.
"""
import argparse
import gc
import hashlib
import json
import re
from pathlib import Path
import shutil
import sys
import time
import types

import bpy
import manta
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_modular_water_feature import settings_snapshot
from probe_water_feature_native_transport import actual_space, CACHE_NAMES
from probe_water_feature_solver_stages import grid_array
from audit_water_feature_native_mac_extension import native_view, digest
from water_feature_cache_stages import decode_configuration


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--subdivision', type=int, choices=(1,2,4), required=True)
    parser.add_argument('--seed-frame', type=int, default=192)
    parser.add_argument('--frames', type=int, default=48)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    started = time.perf_counter()
    source = Path(bpy.data.filepath).resolve()
    root = source.parent
    lab = Path(__file__).resolve().parents[2]/'tmp'/'water-feature-lab'
    output = args.output.resolve()
    setup = json.loads((root/'setup.json').read_text())
    if (output.parent != lab or output.exists() or not output.name.startswith('eddy-temporal-resume-')
            or source.name != 'feature.blend' or setup['case'] != 'eddy'
            or not setup['grid_aligned_domain'] or setup['fractional_obstacles']
            or bpy.app.build_hash != b'fbe6228777e7' or args.seed_frame != 192
            or not 1 <= args.frames <= 48 or args.seed_frame+args.frames > setup['frames']):
        raise ValueError('Fresh bounded aligned native eddy control required')
    if shutil.disk_usage(lab).free < 4*1024**3:
        raise RuntimeError('Need4GiB reserve for fresh native controls')
    domain = bpy.data.objects['Feature liquid']
    state = domain.modifiers[0].domain_settings
    if (state.cache_type != 'MODULAR' or not state.cache_resumable or state.simulation_method != 'FLIP'
            or not state.has_cache_baked_data or state.has_cache_baked_mesh or state.has_cache_baked_particles
            or state.timesteps_min != 2 or state.timesteps_max != 8 or state.time_scale != 1.
            or bpy.context.scene.render.fps != 24 or bpy.context.scene.render.fps_base != 1.):
        raise ValueError('Completed original base with exact FLIP/cache/clock required')
    # Pin every original input touched by the time window; old path provenance
    # in setup/receipts remains unchanged rather than silently re-authored.
    seed_data = root/'cache'/'data'/f'fluid_data_{args.seed_frame:04d}.vdb'
    seed_config = root/'cache'/'config'/f'config_{args.seed_frame:04d}.uni'
    inputs = [source,root/'setup.json',seed_data,seed_config]
    for frame in range(args.seed_frame+1,args.seed_frame+args.frames+1):
        inputs += [root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb',
                   root/'cache'/'config'/f'config_{frame:04d}.uni',
                   root/'cache'/'mesh'/f'fluid_mesh_{frame:04d}.bobj.gz']
    hashes = {str(p.resolve()):digest(p) for p in inputs}
    modules = [Path(__file__),Path(__file__).with_name('probe_water_feature_native_transport.py'),
        Path(__file__).with_name('probe_water_feature_solver_stages.py'),
        Path(__file__).with_name('audit_water_feature_native_mac_extension.py'),
        Path(__file__).with_name('water_feature_cache_stages.py'),
        Path(__file__).with_name('prepare_modular_water_feature.py')]
    code = {str(p.resolve()):digest(p) for p in modules}
    before = settings_snapshot(state)
    output.mkdir()
    # Redirect before changing cache settings; no operator/free action ever
    # receives the original cache directory as a write target.
    state.cache_directory = str(output/'cache')
    state.cache_frame_end = args.seed_frame+args.frames
    state.timesteps_min = 2*args.subdivision
    state.timesteps_max = 8*args.subdivision
    # RNA setting changes invalidate and delete the redirected cache. Install
    # the verified independent seed only AFTER these invalidations complete.
    for folder in ('data','config'):
        (output/'cache'/folder).mkdir(parents=True,exist_ok=True)
    for p in (seed_data,seed_config):
        shutil.copy2(p,output/'cache'/p.parent.name/p.name)
        if digest(output/'cache'/p.parent.name/p.name) != hashes[str(p.resolve())]:
            raise ValueError('Independent seed copy failed')
    state.cache_frame_pause_data = args.seed_frame+1
    after = settings_snapshot(state)
    allowed = {'cache_frame_end','cache_frame_pause_data','timesteps_min','timesteps_max',
        'has_cache_baked_data','has_cache_baked_any','has_cache_baked_mesh','has_cache_baked_particles'}
    changes = {k:[before[k],after[k]] for k in before if before[k] != after[k]}
    if set(changes)-allowed:
        raise ValueError('Unrequested physical/cache change: '+str(changes))
    # Playback can still leave resumable fields initialized. Restore the full
    # seed explicitly in this fresh control process, then demand VDB equality.
    # The host resume subsequently rebuilds actual scene sources/obstacles.
    bpy.context.scene.frame_set(args.seed_frame)
    if not (output/'cache'/'data'/seed_data.name).is_file():
        raise ValueError('RNA/playback invalidation removed the independent seed')
    native = domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
    shape = tuple(native.modifiers[0].domain_settings.domain_resolution)
    if shape != tuple(setup['grid_alignment']['expected_grid_cells']):
        raise ValueError('Native seed resolution mismatch')
    space,identifier = actual_space(shape)
    # All grids precede primary attributes/system. The generic merged native
    # dictionary interposes the particle system before liquid resume grids;
    # it returned zero in the failed v2 preflight. Separate typed loads were
    # independently verified for every field and particle count, exit0.
    for keys in (list(CACHE_NAMES), ['pVel_pp'+identifier,'pp_s'+identifier]):
        object_keys = ([f'{key}_s{identifier}' for key in keys]
            if keys == list(CACHE_NAMES) else keys)
        result = manta.load(name=str(output/'cache'/'data'/seed_data.name),
            objects=[space[key] for key in object_keys],worldSize=max(setup['dimensions_m']))
        if result != 1:
            raise ValueError('Typed full native seed load failed')
    field_map = CACHE_NAMES
    seed_checks = []
    for prefix,name in field_map.items():
        grid = openvdb.read(str(seed_data),name)
        vector, integer = prefix.startswith('vel'), prefix=='flags'
        expected = np.empty((*shape,3) if vector else shape,np.int32 if integer else np.float32)
        grid.copyToArray(expected)
        actual = (native_view(space[f'{prefix}_s{identifier}'],shape,integer=integer).copy()
            if vector or integer else grid_array(space[f'{prefix}_s{identifier}'],shape))
        np.testing.assert_array_equal(actual,expected)
        seed_checks.append(dict(field=name,native_vdb_bitexact=True,scalar_count=actual.size))
    report = dict(complete=False,accepted=False,source_blend=str(source),output=str(output),
        original_input_sha256=hashes,source_code_sha256=code,subdivision=args.subdivision,
        seed_frame=args.seed_frame,first_frame=args.seed_frame+1,last_frame=args.seed_frame+args.frames,
        playback_duration_s=args.frames/24.,fps=24,time_scale=1.,cache_settings_changes=changes,
        seed_fields_verified=seed_checks,full_seed_loaded_explicitly=True,scope=__doc__,steps=[],arrays={})
    original_step = space[f'liquid_step_{identifier}']
    active = {}
    snapshots = output/'observed-stages'; snapshots.mkdir()
    def capture(label,row,native_space,native_id):
        # Full spatial payloads for the first resumed frame; every later step
        # still has clocks/counts observed, without hundreds of duplicate arrays.
        if row['frame'] != args.seed_frame+1:
            return
        record = dict(label=label,fields={})
        for name,prefix in (('phi','phi'),('flags','flags'),('velocity','vel')):
            values = (grid_array(native_space[f'{prefix}_s{native_id}'],shape) if name=='phi' else
                native_view(native_space[f'{prefix}_s{native_id}'],shape,integer=name=='flags').copy())
            if not np.isfinite(values).all():
                raise ValueError('Nonfinite observed native field')
            path = snapshots/f'{row["index"]:03d}-{label}-{name}.npy'
            with path.open('xb') as stream:
                np.save(stream,values,allow_pickle=False)
            sha = digest(path); report['arrays'][str(path.resolve())] = sha
            record['fields'][name] = dict(path=str(path.resolve()),sha256=sha)
        row['stages'].append(record)
    def observe(frame,event,arg):
        match = re.fullmatch(r'liquid_step_(\d+)',frame.f_code.co_name)
        if not match or frame.f_globals.get('__file__') != '<manta_namespace>':
            return
        native_id = match[1]
        native_space = frame.f_globals
        if event == 'call':
            solver = native_space[f's{native_id}']
            row = dict(index=len(report['steps']),native_id=native_id,
                frame=solver.frame,dt_native=solver.timestep,
                time_per_frame_native=solver.timePerFrame,time_total_native=solver.timeTotal,
                primary_before=native_space[f'pp_s{native_id}'].pySize(),stages=[])
            del solver
            report['steps'].append(row)
            active[native_id] = row
            capture('before_liquid_step',row,native_space,native_id)
        elif event == 'return' and native_id in active:
            row = active.pop(native_id)
            row['primary_after'] = native_space[f'pp_s{native_id}'].pySize()
            capture('after_liquid_step',row,native_space,native_id)
    profiles = {}
    def pre_frame(scene,*unused):
        # Native bake may reallocate/recompile the solver in its job thread.
        # Install read-only profiling in that calling thread before evaluation;
        # no liquid-step or native operation is replaced or reimplemented.
        thread = __import__('threading').get_ident()
        profiles[thread] = sys.getprofile()
        sys.setprofile(observe)
    def post_frame(scene,*unused):
        thread = __import__('threading').get_ident()
        if thread in profiles:
            sys.setprofile(profiles.pop(thread))
    report['compiled_step_code_sha256'] = hashlib.sha256(__import__('marshal').dumps(original_step.__code__)).hexdigest()
    error_text = None
    try:
        bpy.app.handlers.frame_change_pre.append(pre_frame)
        bpy.app.handlers.frame_change_post.append(post_frame)
        bpy.ops.object.select_all(action='DESELECT'); domain.select_set(True)
        bpy.context.view_layer.objects.active = domain
        write_new(output/'preflight.json',dict(report,domain_settings=after))
        bake_start = time.perf_counter()
        result = bpy.ops.fluid.bake_data()
        report.update(data_result=list(result),data_bake_seconds=time.perf_counter()-bake_start)
        if 'FINISHED' not in result or not state.has_cache_baked_data or not report['steps']:
            raise ValueError('Native resumed bake or observer did not complete')
        expected = list(range(args.seed_frame+1,args.seed_frame+args.frames+1))
        if sorted({r['frame'] for r in report['steps']}) != expected:
            raise ValueError('Observed native frame coverage differs from requested interval')
        for frame in expected:
            if not (output/'cache'/'data'/f'fluid_data_{frame:04d}.vdb').is_file():
                raise ValueError('Missing resumed frame '+str(frame))
        if any(digest(p)!=sha for p,sha in hashes.items()):
            raise ValueError('Original input changed during resumed bake')
        if digest(output/'cache'/'data'/seed_data.name) != hashes[str(seed_data.resolve())] or digest(output/'cache'/'config'/seed_config.name) != hashes[str(seed_config.resolve())]:
            raise ValueError('Copied resumable seed was overwritten')
    except Exception as exc:
        error_text = f'{type(exc).__name__}: {exc}'
        report['error'] = error_text
        exc.__traceback__ = None
    finally:
        # These modifications are observational and scoped to this fresh case's
        # process. Do not leave patched native operations during mesh baking.
        bpy.app.handlers.frame_change_pre.remove(pre_frame)
        bpy.app.handlers.frame_change_post.remove(post_frame)
        thread = __import__('threading').get_ident()
        if thread in profiles:
            sys.setprofile(profiles.pop(thread))
        active.clear()
        report['originals_unchanged'] = all(digest(p)==sha for p,sha in hashes.items())
        report['executed_modules_unchanged'] = all(digest(p)==sha for p,sha in code.items())
    if error_text:
        write_new(output/'failed-native-resume.json',report)
        raise RuntimeError(error_text)
    # Mesh only over the newly evolved interval, not copied/history frames.
    state.cache_frame_pause_mesh = args.seed_frame+1
    mesh_start = time.perf_counter()
    result = bpy.ops.fluid.bake_mesh()
    report.update(mesh_result=list(result),mesh_bake_seconds=time.perf_counter()-mesh_start)
    expected_meshes = [output/'cache'/'mesh'/f'fluid_mesh_{frame:04d}.bobj.gz' for frame in expected]
    if 'FINISHED' not in result or not state.has_cache_baked_mesh or any(not p.is_file() for p in expected_meshes):
        write_new(output/'failed-native-mesh.json',report)
        raise ValueError('Native resumed mesh coverage incomplete')
    blend = output/'feature.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    setup.update(blend=str(blend),staged_from_blend=str(source),native_resumed_seed_frame=args.seed_frame,
        frames=args.seed_frame+args.frames,first_available_frame=args.seed_frame+1,
        native_temporal_subdivision=args.subdivision,physical_accuracy_accepted=False,
        visual_accuracy_accepted=False,game_integrated=False)
    write_new(output/'setup.json',setup)
    report.update(complete=True,elapsed_s=time.perf_counter()-started,blend=str(blend),
        original_seed_unchanged=True,originals_unchanged=all(digest(p)==sha for p,sha in hashes.items()),
        output_cache_sha256={str(p.relative_to(output)):digest(p) for p in (output/'cache').rglob('*') if p.is_file()},
        limitations='Actual host-backed native resume from serialized frame192, not proof of uninterrupted-bake identity. Timestep minimum/maximum multiplied together; spatial resolution and authored boundaries unchanged. Mesh is native original recipe. Secondary phases still unbaked/unaccepted; no foam workaround. Native bake/render cost is not gameFPS.')
    if not report['originals_unchanged']:
        raise ValueError('Original source changed')
    write_new(output/'native-temporal-resume.json',report)
    print('NATIVE_TEMPORAL_RESUME_COMPLETE',args.subdivision,len(report['steps']),report['elapsed_s'],flush=True)


if __name__ == '__main__':
    # Never keep borrowed native resources alive through traceback locals
    # while Blender frees their owning parent at process teardown.
    error = None
    try:
        main()
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
        exc.__traceback__ = None
    if error:
        print('NATIVE_TEMPORAL_RESUME_FAILED', error, flush=True)
        raise SystemExit(1)
