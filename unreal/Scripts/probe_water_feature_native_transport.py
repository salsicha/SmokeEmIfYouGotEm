"""Observe an exact native liquid-step body on private resumed eddy resources.

Not a full cached-frame replay: host emissions, pre-step source/solid rebuilding,
effectors, mesh extraction and secondary evolution are deliberately not run.
Every observed array is fresh diagnostic output, never a replacement cache.
"""
import argparse
import ctypes
import gc
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import types

import bpy
import manta
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_private_step import bind_owned, global_names
from audit_water_feature_native_mac_extension import native_view, digest
from probe_water_feature_solver_stages import grid_array, vector_data_address, cleanup
from water_feature_cache_stages import decode_configuration

GRID_TYPES = {'FlagGrid': manta.FlagGrid, 'MACGrid': manta.MACGrid,
    'LevelsetGrid': manta.LevelsetGrid, 'Grid_Real': manta.RealGrid,
    'Grid_Vec3': manta.VecGrid, 'Grid_int': manta.IntGrid}
CACHE_NAMES = {'flags': 'flags', 'vel': 'velocity', 'velTmp': 'velocity_previous',
    'phi': 'phi', 'phiTmp': 'phi_previous', 'phiParts': 'phi_particles',
    'phiObs': 'phi_obstacle', 'phiObsIn': 'phi_obstacle_inflow',
    'phiIn': 'phi_inflow', 'phiOut': 'phi_out', 'phiOutIn': 'phi_out_inflow'}
OBSERVED_CALLS = ('advectSemiLagrange', 'unionParticleLevelset', 'extrapolateLsSimple',
    'mapPartsToMAC', 'combineGridVel', 'addGravity', 'extrapolateMACSimple',
    'setWallBcs', 'solvePressure', 'adjustNumber', 'flipVelocityUpdate')


def scalar_view(grid, shape):
    if manta.DOUBLEPRECISION or (grid.getSizeX(), grid.getSizeY(), grid.getSizeZ()) != shape:
        raise ValueError('Matched float32 grid required')
    pointer = grid.getDataPointer()
    if not isinstance(pointer, str) or not re.fullmatch(r'(?:0x)?[0-9a-fA-F]+', pointer):
        raise ValueError('Unsupported scalar grid pointer')
    address = int(pointer, 16)
    if address <= 0:
        raise ValueError('Null scalar payload')
    return np.ctypeslib.as_array((ctypes.c_float*int(np.prod(shape))).from_address(address)).reshape(shape[::-1]).transpose(2, 1, 0)


def advection_controls():
    """Independent affine material-transport checks of the native scalar kernel."""
    shape = (17, 15, 13)
    xyz = np.stack(np.meshgrid(*[np.arange(n)+.5 for n in shape], indexing='ij'), axis=-1)
    velocity = np.array([1.25, -.75, .5])
    rows, space, error_text = [], {}, None
    try:
        space['s99'] = manta.Solver(name='owned_transport_control', gridSize=manta.vec3(*shape), dim=3)
        space['flags_s99'] = space['s99'].create(manta.FlagGrid, name='flags')
        space['vel_s99'] = space['s99'].create(manta.MACGrid, name='velocity')
        space['phi_s99'] = space['s99'].create(manta.LevelsetGrid, name='phi')
        view = native_view(space['flags_s99'], shape, integer=True); view[:] = 1; del view
        space['vel_s99'].setConst(manta.vec3(*velocity))
        for normal in (np.array([0., 0., 1.]), np.array([.3, -.2, .7])):
            for dt in (.013, .025, .052):
                space['s99'].timestep = dt
                before = (xyz@normal-5.).astype(np.float32)
                view = scalar_view(space['phi_s99'], shape); view[:] = before; del view
                np.testing.assert_array_equal(grid_array(space['phi_s99'], shape), before)
                manta.advectSemiLagrange(flags=space['flags_s99'], vel=space['vel_s99'], grid=space['phi_s99'], order=1)
                after = grid_array(space['phi_s99'], shape)
                expected = xyz@normal-5.-dt*(velocity@normal)
                interior = (slice(2, -2),)*3
                error = float(np.max(np.abs(after[interior]-expected[interior])))
                if error > 2e-5:
                    raise ValueError('Native affine material transport failed its fixed float32 allowance')
                rows.append(dict(normal=normal.tolist(), dt_native=dt,
                    maximum_interior_phi_error_cells=error, fixed_allowance_cells=2e-5,
                    scalar_count=after[interior].size))
    except Exception as exc:
        error_text = f'{type(exc).__name__}: {exc}'
        exc.__traceback__ = None
    finally:
        cleanup(space, '99')
    if error_text:
        raise RuntimeError(error_text)
    return rows


def actual_space(shape):
    spaces = [x.__dict__ for x in gc.get_objects() if isinstance(x, types.ModuleType)
              and x.__dict__.get('__file__') == '<manta_namespace>']
    if len(spaces) != 1:
        raise ValueError('Exactly one native namespace required')
    source = spaces[0]
    ids = [k[1:] for k in source if re.fullmatch(r's\d+', k)
           and tuple(int(getattr(source['gs_'+k], a)) for a in 'xyz') == shape]
    if len(ids) != 1:
        raise ValueError('Exactly one actual base solver required')
    return source, ids[0]


def make_owned(source, identifier, shape, space):
    """Allocate by native type; never share an engine grid/particle or parent."""
    function = source[f'liquid_step_{identifier}']
    needed = global_names(function)
    calls, created = {}, []
    space[f's{identifier}'] = manta.Solver(name='owned_eddy_stage_transport', gridSize=manta.vec3(*shape), dim=3)
    # Allocate the primary system before its attached velocity attribute.
    space[f'pp_s{identifier}'] = space[f's{identifier}'].create(manta.BasicParticleSystem, name='particles')
    space[f'pVel_pp{identifier}'] = space[f'pp_s{identifier}'].create(manta.PdataVec3, name='particles_velocity')
    for name in needed:
        if name in space or name not in source:
            continue
        value = source[name]
        kind = type(value).__name__
        if isinstance(value, types.BuiltinFunctionType):
            calls[name] = value
        elif isinstance(value, (type(None), bool, int, float, str)):
            space[name] = value
        elif kind == 'vec3':
            space[name] = manta.vec3(value.x, value.y, value.z)
        elif kind in GRID_TYPES:
            prefix = name.removesuffix('_s'+identifier)
            space[name] = space[f's{identifier}'].create(GRID_TYPES[kind], name=CACHE_NAMES.get(prefix, 'owned_'+prefix))
            created.append(dict(global_name=name, kind=kind, cache_name=CACHE_NAMES.get(prefix)))
        elif kind == 'ParticleIndexSystem':
            space[name] = space[f's{identifier}'].create(manta.ParticleIndexSystem, name='owned_particle_index')
        else:
            raise ValueError('Unrecognized reachable native global '+name+': '+kind)
    bound, proof = bind_owned(function, space, calls, {'float': float, 'str': str})
    # No private children/call wrappers may escape parent cleanup through bound.
    space[f'liquid_step_{identifier}'] = bound
    return space, calls, created, proof


def load_and_verify(space, identifier, shape, path, world_size, native_positions, native_velocities, origin, spacing, resolution):
    objects = []
    for prefix in CACHE_NAMES:
        key = f'{prefix}_s{identifier}'
        if key in space:
            objects.append(space[key])
    objects += [space[f'pVel_pp{identifier}'], space[f'pp_s{identifier}']]
    if manta.load(name=str(path.resolve()), objects=objects, worldSize=world_size) != 1:
        raise ValueError('Native resume load failed')
    del objects
    rows = []
    for prefix, cache_name in CACHE_NAMES.items():
        key = f'{prefix}_s{identifier}'
        if key not in space:
            continue
        grid = openvdb.read(str(path), cache_name)
        if tuple(grid.metadata['file_base_resolution']) != shape:
            raise ValueError('Wrong resumed grid dimensions')
        kind = type(space[key]).__name__
        vector, integer = kind in ('MACGrid', 'Grid_Vec3'), kind in ('FlagGrid', 'Grid_int')
        expected = np.empty((*shape, 3) if vector else shape, np.int32 if integer else np.float32)
        grid.copyToArray(expected)
        actual = (native_view(space[key], shape, integer=integer).copy()
                  if vector or integer else grid_array(space[key], shape))
        np.testing.assert_array_equal(actual, expected)
        rows.append(dict(field=cache_name, scalar_count=actual.size, native_vdb_bitexact=True))
    count = space[f'pp_s{identifier}'].pySize()
    if count != len(native_positions) or count <= 0:
        raise ValueError('Native resumed primary count mismatch')
    pointer = vector_data_address(space[f'pp_s{identifier}'].getDataPointer(), count, 16)
    data = bytes((ctypes.c_ubyte*(count*16)).from_address(pointer))
    positions = np.frombuffer(data, dtype=np.dtype([('pos', '<f4', 3), ('flags', '<i4')]))['pos']
    np.testing.assert_allclose(positions*spacing+origin, native_positions, atol=1e-6, rtol=1e-6)
    pointer = vector_data_address(space[f'pVel_pp{identifier}'].getDataPointer(), count, 12)
    velocities = np.ctypeslib.as_array((ctypes.c_float*(count*3)).from_address(pointer)).copy().reshape(-1, 3)
    np.testing.assert_allclose(velocities/resolution, native_velocities, atol=1e-6, rtol=1e-6)
    return dict(grids=rows, primary_count=count, primary_positions_velocities_match_native=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frame', type=int, default=192)
    parser.add_argument('--timestep-fraction', type=float, choices=(1., .5, .25), default=1.,
                        help='Declared local convergence control, not cache retiming or a replacement bake')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = Path(bpy.data.filepath).resolve().parent
    setup = json.loads((root/'setup.json').read_text())
    shape = tuple(setup['grid_alignment']['expected_grid_cells'])
    if bpy.app.build_hash != b'fbe6228777e7' or setup['case'] != 'eddy' or not setup['grid_aligned_domain'] or setup['fractional_obstacles']:
        raise ValueError('Exact aligned eddy FLIP case required')
    if args.output.exists() or args.output.with_suffix('').exists():
        raise FileExistsError('Fresh receipt and array directory required')
    inputs = [Path(bpy.data.filepath), root/'setup.json', root/'cache'/'data'/f'fluid_data_{args.frame:04d}.vdb',
              root/'cache'/'config'/f'config_{args.frame:04d}.uni']
    hashes = {str(p.resolve()): digest(p) for p in inputs}
    code = {str(Path(__file__).resolve()): digest(__file__)}
    for name in ('water_feature_private_step.py', 'test_water_feature_private_step.py',
                 'probe_water_feature_solver_stages.py', 'audit_water_feature_native_mac_extension.py', 'water_feature_cache_stages.py'):
        p = Path(__file__).with_name(name); code[str(p.resolve())] = digest(p)
    obj = bpy.data.objects['Feature liquid']
    # Relocate only this unsaved playback process; historical blend/cache bytes
    # and embedded old path provenance remain untouched after the drive move.
    obj.modifiers[0].domain_settings.cache_directory = str(root/'cache')
    bpy.context.scene.frame_set(args.frame)
    native = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    state = native.modifiers[0].domain_settings
    if tuple(state.domain_resolution) != shape or state.simulation_method != 'FLIP' or state.time_scale != 1.:
        raise ValueError('Actual resumed case mismatch')
    ps = next(p for p in native.particle_systems if p.name.lower() == 'liquid')
    count = len(ps.particles)
    positions, velocities = np.empty(count*3, np.float32), np.empty(count*3, np.float32)
    ps.particles.foreach_get('location', positions); ps.particles.foreach_get('velocity', velocities)
    positions, velocities = positions.reshape(-1, 3), velocities.reshape(-1, 3)
    spacing = max(setup['dimensions_m'])/setup['resolution']
    origin = np.asarray(native.matrix_world.translation)-np.array(shape)*spacing/2
    source, identifier = actual_space(shape)
    # Preserve actual loaded engine arrays, including initialized resumable
    # values; explicit private loads must not be confused with engine loading.
    def live_fingerprint():
        return {name: hashlib.sha256((native_view(source[f'{name}_s{identifier}'], shape).copy()
                if name.startswith('vel') else grid_array(source[f'{name}_s{identifier}'], shape)).tobytes()).hexdigest()
                for name in ('phi', 'phiTmp', 'vel', 'velTmp')}
    live_before = live_fingerprint()
    controls = advection_controls()
    folder = args.output.with_suffix(''); folder.mkdir()
    report = dict(complete=False, accepted=False, original_input_sha256=hashes, source_code_sha256=code,
        native_advection_controls=controls, scope=__doc__, frame=args.frame,
        playback_cache_relocated_in_memory_only=True, stages=[], arrays={})
    space, error_text = {}, None
    started = time.perf_counter()
    try:
        space, calls, created, proof = make_owned(source, identifier, shape, space)
        report.update(exact_function_binding=proof, owned_grid_allocations=created)
        report['resume_verification'] = load_and_verify(space, identifier, shape, inputs[2], max(setup['dimensions_m']),
            positions, velocities, origin, spacing, setup['resolution'])
        config = decode_configuration(inputs[3].read_bytes())
        solver = space[f's{identifier}']
        solver.frameLength = .1*25/setup['fps']
        solver.timestepMin = solver.frameLength/state.timesteps_max
        solver.timestepMax = solver.frameLength/state.timesteps_min
        solver.cfl = state.cfl_condition
        solver.frame = args.frame+1; solver.timePerFrame = 0.
        solver.timeTotal = config['time_total_native']
        solver.adaptTimestep(space[f'vel_s{identifier}'].getMax())
        report['native_adapted_timestep_before_control'] = solver.timestep
        report['declared_timestep_fraction'] = args.timestep_fraction
        solver.timestep = solver.timestep*args.timestep_fraction
        report['private_clock'] = {k: getattr(solver, k) for k in ('frame','frameLength','timestep','timePerFrame','timeTotal')}
        report['physical_substep_seconds'] = solver.timestep/2.5
        del solver
        # Stationary solid velocity/forces are not cached. Refuse a nonzero
        # native playback input instead of pretending it was restored.
        for prefix in ('forces', 'obvel'):
            if np.count_nonzero(native_view(source[f'{prefix}_s{identifier}'], shape)):
                raise ValueError('Uncached nonzero force/obstacle input requires separate recovery')
        report['uncached_force_and_solid_velocity'] = 'Explicit private zero; live playback zero verified, not saved bake chronology'
        def capture(label):
            index = len(report['stages'])
            fields = {'phi': grid_array(space[f'phi_s{identifier}'], shape),
                'phi_particles': grid_array(space[f'phiParts_s{identifier}'], shape),
                'velocity': native_view(space[f'vel_s{identifier}'], shape).copy(),
                'flags': native_view(space[f'flags_s{identifier}'], shape, integer=True).copy()}
            row = dict(index=index, label=label, primary_count=space[f'pp_s{identifier}'].pySize(), fields={})
            for name, array in fields.items():
                if not np.isfinite(array).all():
                    raise ValueError('Nonfinite native stage '+label)
                path = folder/f'{index:02d}-{name}.npy'
                with path.open('xb') as stream:
                    np.save(stream, array, allow_pickle=False)
                sha = digest(path); report['arrays'][str(path.resolve())] = sha
                row['fields'][name] = dict(path=str(path.resolve()), sha256=sha, minimum=float(array.min()), maximum=float(array.max()))
            report['stages'].append(row)
            print('OWNED_TRANSPORT_STAGE', index, label, row['primary_count'], flush=True)
        def observer(name, call):
            def observed(*call_args, **kwargs):
                target = kwargs.get('grid')
                suffix = '_phi' if target is space[f'phi_s{identifier}'] else '_velocity' if target is space[f'vel_s{identifier}'] else ''
                capture('before_'+name+suffix)
                result = call(*call_args, **kwargs)
                capture('after_'+name+suffix)
                return result
            return observed
        for name in OBSERVED_CALLS:
            if name in calls:
                space[f'liquid_step_{identifier}'].__globals__[name] = observer(name, calls[name])
        capture('before_liquid_step')
        space[f'liquid_step_{identifier}']()
        capture('after_liquid_step')
        report['complete'] = True
    except Exception as exc:
        error_text = f'{type(exc).__name__}: {exc}'
        report['error'] = error_text
        exc.__traceback__ = None
    finally:
        # Drop private-function globals/wrappers before native child cleanup.
        if f'liquid_step_{identifier}' in space:
            space[f'liquid_step_{identifier}'].__globals__.clear()
        cleanup(space, identifier)
        report['live_engine_fields_unchanged'] = live_fingerprint() == live_before
        report['originals_unchanged'] = all(digest(p) == h for p,h in hashes.items())
        report['executed_modules_unchanged'] = all(digest(p) == h for p,h in code.items())
        report['elapsed_s'] = time.perf_counter()-started
        with args.output.open('x') as stream:
            json.dump(report, stream, indent=2)
    if error_text:
        raise RuntimeError(error_text)
    if not all(report[k] for k in ('live_engine_fields_unchanged','originals_unchanged','executed_modules_unchanged')):
        raise ValueError('Source or engine state changed')
    print('OWNED_TRANSPORT_COMPLETE', len(report['stages']), report['elapsed_s'], flush=True)


if __name__ == '__main__':
    main()
