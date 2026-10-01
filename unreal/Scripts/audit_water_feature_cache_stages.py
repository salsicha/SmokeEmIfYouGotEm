"""Trace exact compiled eddy functions and preserved cache clocks/stage pairs.

Read-only native inspection, not a bake/resume, field correction or foam driver.
The engine's private Manta namespace is located by its exact source-defined
module filename; no engine function is called or replaced.
"""
import argparse
import dis
import gc
import hashlib
import json
import marshal
from pathlib import Path
import re
import sys
import time
import types

import bpy
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_cache_stages import decode_configuration, interval_clock, beginning_frame_snapshot
from audit_water_feature_native_mac_extension import native_view
from probe_water_feature_solver_stages import grid_array


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def quantiles(values):
    return np.quantile(np.asarray(values), [0, .05, .5, .95, 1]).tolist() if len(values) else None


def read_grid(path, name, shape, vector=False, integer=False):
    grid = openvdb.read(str(path), name)
    if tuple(grid.metadata['file_base_resolution']) != shape:
        raise ValueError('Captured grid shape mismatch')
    if vector and grid.metadata['class'] != 'staggered':
        raise ValueError('Native staggered vector required')
    array = np.empty((*shape, 3) if vector else shape, np.int32 if integer else np.float32)
    grid.copyToArray(array)
    if not np.isfinite(array).all():
        raise ValueError('Nonfinite captured field')
    return array, dict(grid.metadata)


def native_function_records(space, identifier):
    report = {}
    for key in (f'liquid_adaptive_step_{identifier}', f'liquid_step_{identifier}',
                f'liquid_step_mesh_{identifier}', f'liquid_step_particles_{identifier}',
                f'liquid_load_data_{identifier}'):
        function = space[key]
        if not isinstance(function, types.FunctionType) or function.__code__.co_filename != '<string>':
            raise ValueError('Actual compiled native function required')
        instructions = [dict(offset=i.offset, opname=i.opname, argrepr=i.argrepr,
            starts_line=i.starts_line, jump_target=i.is_jump_target)
            for i in dis.get_instructions(function)]
        report[key] = dict(code_sha256=hashlib.sha256(marshal.dumps(function.__code__)).hexdigest(),
            referenced_names=list(function.__code__.co_names), instructions=instructions)
    return report


def live_case_readback(shape):
    spaces = [x.__dict__ for x in gc.get_objects() if isinstance(x, types.ModuleType)
              and x.__dict__.get('__file__') == '<manta_namespace>']
    if len(spaces) != 1:
        raise ValueError('Exactly one actual native Manta namespace required')
    space = spaces[0]
    identifiers = []
    for key in space:
        match = re.fullmatch(r's(\d+)', key)
        if match:
            identifier = match.group(1)
            size = space[f'gs_s{identifier}']
            if tuple(map(int, (size.x, size.y, size.z))) == shape:
                identifiers.append(identifier)
    if len(identifiers) != 1:
        raise ValueError('Exactly one matched base solver required')
    identifier = identifiers[0]
    names = {label: f'{prefix}{identifier}' for label, prefix in (
        ('solver', 's'), ('phi', 'phi_s'), ('velocity', 'vel_s'),
        ('phi_previous', 'phiTmp_s'), ('velocity_previous', 'velTmp_s'))}
    snapshot = beginning_frame_snapshot(space[f'liquid_step_{identifier}'],
        names['solver'], names['phi'], names['velocity'], names['phi_previous'], names['velocity_previous'])
    settings = {k: space[f'{k}_s{identifier}'] for k in (
        'dim', 'res', 'using_fractions', 'using_apic', 'using_sndparts', 'using_mesh',
        'using_final_mesh', 'upres_sp', 'domainSize', 'timeTotal', 'timePerFrame',
        'frameLength', 'timeScale', 'dt0', 'timestepsMin', 'timestepsMax', 'cflCond')
        if f'{k}_s{identifier}' in space}
    # upres_sp is stored under the secondary-solver suffix, not base suffix.
    settings['secondary_upres'] = space[f'upres_sp{identifier}']
    solver = space[names['solver']]
    clock = {k: getattr(solver, k) for k in ('frame', 'frameLength', 'timestep', 'timeTotal', 'timePerFrame')}
    del solver
    arrays = dict(phi=grid_array(space[names['phi']], shape),
        phi_previous=grid_array(space[names['phi_previous']], shape),
        velocity=native_view(space[names['velocity']], shape).copy(),
        velocity_previous=native_view(space[names['velocity_previous']], shape).copy())
    # Only owning ndarray copies, primitives and bytecode records leave here;
    # no native child aliases survive a later frame reload or solver destruction.
    return dict(identifier=identifier, snapshot_guard=snapshot, settings=settings,
                playback_loader_solver_clock=clock, functions=native_function_records(space, identifier)), arrays


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[168, 190, 191, 192, 193, 194, 214])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    started = time.perf_counter()
    source = Path(bpy.data.filepath)
    root = source.parent
    setup = json.loads((root/'setup.json').read_text())
    reference = json.loads(args.reference.read_text())
    if (source.name != 'feature-mesh.blend' or bpy.app.build_hash != b'fbe6228777e7'
            or setup['case'] != 'eddy' or not setup['grid_aligned_domain']
            or setup['fractional_obstacles'] or not reference['complete']
            or not reference['originals_unchanged'] or reference['accepted']
            or not set(args.frames).issubset(range(2, setup['frames']+1))
            or len(set(args.frames)) != len(args.frames)):
        raise ValueError('Exact matched captured eddy and incomplete acceptance reference required')
    hashes = dict(reference['original_input_sha256'])
    for path in (source, root/'setup.json', args.reference):
        hashes[str(path.resolve())] = digest(path)
    modules = [Path(__file__), Path(__file__).with_name('water_feature_cache_stages.py'),
        Path(__file__).with_name('test_water_feature_cache_stages.py'),
        Path(__file__).with_name('audit_water_feature_native_mac_extension.py'),
        Path(__file__).with_name('probe_water_feature_solver_stages.py')]
    code_hashes = {str(p.resolve()): digest(p) for p in modules}
    if any(digest(path) != sha for path, sha in hashes.items()):
        raise ValueError('Preserved input changed')
    shape = tuple(setup['grid_alignment']['expected_grid_cells'])
    h = max(setup['dimensions_m'])/setup['resolution']
    configs, intervals = [], []
    for frame in range(1, setup['frames']+1):
        path = root/'cache'/'config'/f'config_{frame:04d}.uni'
        hashes[str(path.resolve())] = digest(path)
        config = decode_configuration(path.read_bytes())
        if (tuple(config['resolution']) != shape or tuple(config['base_resolution']) != shape
                or config['resolution_min'] != [0, 0, 0] or tuple(config['resolution_max']) != shape
                or abs(config['dimensionless_dx']-1/setup['resolution']) > 1e-8):
            raise ValueError('Unexpected native cached configuration mapping')
        config['frame'] = frame
        if configs:
            intervals.append(dict(frame_before=frame-1, frame_after=frame,
                **interval_clock(configs[-1], config, 1, setup['fps'], 1.)))
        configs.append(config)
    rows, live = [], None
    for frame in args.frames:
        before_path = root/'cache'/'data'/f'fluid_data_{frame-1:04d}.vdb'
        after_path = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        for path in (before_path, after_path):
            hashes[str(path.resolve())] = digest(path)
        before_velocity, _ = read_grid(before_path, 'velocity', shape, vector=True)
        before_phi, _ = read_grid(before_path, 'phi', shape)
        previous_velocity, velocity_meta = read_grid(after_path, 'velocity_previous', shape, vector=True)
        previous_phi, phi_meta = read_grid(after_path, 'phi_previous', shape)
        final_flags, _ = read_grid(after_path, 'flags', shape, integer=True)
        delta = np.abs(previous_phi.astype(float)-before_phi)
        band = (np.abs(previous_phi) <= 3) | (np.abs(before_phi) <= 3)
        changed_flag_values, changed_flag_counts = np.unique(final_flags[previous_phi != before_phi], return_counts=True)
        row = dict(frame=frame, interval=interval_clock(configs[frame-2], configs[frame-1], 1, setup['fps']),
            previous_velocity_equals_previous_frame_final=bool(np.array_equal(previous_velocity, before_velocity)),
            velocity_different_scalars=int(np.count_nonzero(previous_velocity != before_velocity)),
            velocity_maximum_raw_difference=float(np.abs(previous_velocity-before_velocity).max()),
            previous_phi_equals_previous_frame_final=bool(np.array_equal(previous_phi, before_phi)),
            phi_different_scalars=int(np.count_nonzero(previous_phi != before_phi)),
            phi_difference_band_cells=int(band.sum()),
            phi_absolute_difference_m_in_three_cell_band_quantiles=quantiles(delta[band]*h),
            phi_sign_changed_cells=int(np.count_nonzero((previous_phi < 0) != (before_phi < 0))),
            phi_different_cells_by_cached_final_flag=dict(zip(map(str, changed_flag_values), map(int, changed_flag_counts))),
            velocity_previous_metadata=velocity_meta, phi_previous_metadata=phi_meta,
            accepted=False)
        if frame == 192:
            bpy.context.scene.frame_set(frame)
            native = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
            state = native.modifiers[0].domain_settings
            if (state.time_scale != 1. or state.simulation_method != 'FLIP'
                    or tuple(state.domain_resolution) != shape
                    or bpy.context.scene.render.fps != setup['fps']
                    or bpy.context.scene.render.fps_base != 1.):
                raise ValueError('Matched actual native scene/clock required')
            live, native_arrays = live_case_readback(shape)
            live['native_grid_load_comparisons'] = {}
            for label, values in native_arrays.items():
                cached, _ = read_grid(after_path, label, shape, vector=label.startswith('velocity'))
                live['native_grid_load_comparisons'][label] = dict(
                    matches_vdb_bitexact=bool(np.array_equal(values, cached)),
                    different_scalars=int(np.count_nonzero(values != cached)),
                    maximum_absolute_raw_difference=float(np.abs(values.astype(float)-cached).max()),
                    native_minimum=float(values.min()), native_maximum=float(values.max()),
                    cached_minimum=float(cached.min()), cached_maximum=float(cached.max()))
            np.testing.assert_array_equal(native_arrays['velocity'], np.asarray(state.velocity_grid[:]).reshape((*shape[::-1], 3)).transpose(2, 1, 0, 3))
            if not live['native_grid_load_comparisons']['velocity']['matches_vdb_bitexact']:
                raise ValueError('Native final velocity did not load the measured captured field')
            live['all_four_native_fields_match_vdb_bitexact'] = all(
                r['matches_vdb_bitexact'] for r in live['native_grid_load_comparisons'].values())
            if (live['settings']['res'] != setup['resolution'] or live['settings']['using_apic']
                    or live['settings']['using_fractions'] or live['settings']['domainSize'] != max(setup['dimensions_m'])):
                raise ValueError('Actual live solver is not the matched FLIP case')
            row['live_case_inspected'] = True
        rows.append(row)
        print('CACHE_STAGE_PAIR', json.dumps({k: v for k, v in row.items() if not k.endswith('_metadata')}), flush=True)
    if live is None:
        raise ValueError('Require frame192 for exact live-case compiled function inspection')
    if any(digest(path) != sha for path, sha in {**hashes, **code_hashes}.items()):
        raise ValueError('Captured input or executed module changed during audit')
    report = dict(complete=True, accepted=False, originals_unchanged=True,
        blender=bpy.app.version_string, python=sys.version, frames=rows, configurations=configs,
        live_case=live, intervals=intervals, original_input_sha256=hashes, source_code_sha256=code_hashes,
        clock_summary=dict(configuration_count=len(configs), monotone_intervals=len(intervals),
            native_interval_error_quantiles=quantiles([i['native_interval_error'] for i in intervals]),
            last_substep_native_quantiles=quantiles([c['last_timestep_native'] for c in configs]),
            maximum_absolute_total_time_error_native=max(abs(c['time_total_native']-.1*25*c['frame']/setup['fps']) for c in configs),
            source_clock_scale_native_per_physical_second=2.5,
            playback_solver_clock_is_not_cache_timestamp=True),
        elapsed_s=time.perf_counter()-started,
        primary_layout_url='https://raw.githubusercontent.com/blender/blender/fbe6228777e7/intern/mantaflow/intern/MANTA_main.cpp',
        primary_field_types_url='https://raw.githubusercontent.com/blender/blender/fbe6228777e7/source/blender/makesdna/DNA_fluid_types.h',
        limitations='Exact loaded-case compiled function inspection and preserved cache-stage/clock measurements only. Beginning-frame phi includes pre-step source/solid changes; velocity_previous is not an arbitrary final-substep snapshot. No prior-substep flags/timestamps or intermediate advection/reconstruction fields are recovered. Playback-loaded solver clock is not bake chronology. No compiled engine function called/replaced, bake/resume/retiming, geometry/cache/scene edit, foam driver, render/clip or physical/visual acceptance.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print('CACHE_STAGE_RESULT', json.dumps(dict(complete=True, accepted=False, originals_unchanged=True,
        pairs=len(rows), clock_summary=report['clock_summary'], elapsed_s=report['elapsed_s'])), flush=True)


if __name__ == '__main__':
    main()
