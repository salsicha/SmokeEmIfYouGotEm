"""Instrument one native liquid step from preserved cached state, not a new bake.

Only the exported liquid-step body runs. Scene/source/pre-step rebuilding is
not replayed, so this is a local mechanism experiment, not a frame reproduction.
"""
import argparse
import ast
import ctypes
import gc
import hashlib
import json
from pathlib import Path
import re
import sys

import bpy
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_cell_volume import reconstructed_volume
from water_feature_stage_instrumentation import Instrument


def grid_array(grid, shape):
    """Read the native RealGrid ABI; validate against VDB before any step.

    Manta's public getDataPointer plus grid sizes and DOUBLEPRECISION determine
    the contiguous x-fastest scalar layout. The returned ndarray owns a copy.
    """
    import manta
    assert (grid.getSizeX(), grid.getSizeY(), grid.getSizeZ()) == tuple(shape)
    pointer = grid.getDataPointer()
    if isinstance(pointer, str):
        if not re.fullmatch(r'(?:0x)?[0-9a-fA-F]+', pointer):
            raise ValueError('Unexpected native pointer format')
        address = int(pointer, 16)  # Windows getter emits bare hexadecimal.
    else:
        address = int(pointer)
    if address <= 0:
        raise ValueError('Null native grid pointer')
    scalar = ctypes.c_double if manta.DOUBLEPRECISION else ctypes.c_float
    buffer = (scalar*int(np.prod(shape))).from_address(address)
    result = np.ctypeslib.as_array(buffer).copy().reshape(shape[::-1]).transpose(2, 1, 0)
    if not np.isfinite(result).all():
        raise ValueError('Nonfinite native grid readback')
    return result


def vector_data_address(pointer, count, stride):
    """Read this MSVC release build's std::vector header, not its payload.

    Particle getDataPointer returns &mData (unlike Grid's scalar pointer).
    Refuse any layout whose length/capacity does not match the native count.
    """
    address = int(pointer, 16) if isinstance(pointer, str) else int(pointer)
    begin, end, capacity = (ctypes.c_void_p*3).from_address(address)
    if not begin or not end or not capacity or end-begin != count*stride or capacity < end:
        raise ValueError('Particle vector header does not match the supported release ABI')
    return begin


def cleanup(space, identifier):
    """Manta requires children/aliases to be released before their solvers."""
    import manta
    for name in list(space):
        if '_dict_' in name and isinstance(space[name], dict):
            space[name].clear()
    if f's{identifier}' in space:
        manta.releaseMG(space[f's{identifier}'])
    for pattern in (rf'_(pp|mesh){identifier}$', rf'_(s|sm|sp){identifier}$'):
        for name in list(space):
            if re.search(pattern, name):
                del space[name]
        gc.collect()
    for name in (f'sm{identifier}', f'sp{identifier}', f's{identifier}'):
        space.pop(name, None)
    gc.collect()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script', type=Path, required=True)
    parser.add_argument('--case-dir', type=Path, required=True)
    parser.add_argument('--frame', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--save-interface-stages', action='store_true',
                        help='Preserve six observed interface fields for independent quadrature/bounds')
    parser.add_argument('--save-extrapolation-stages', action='store_true',
                        help='Also save both liquid level-set extrapolation checkpoints')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.save_extrapolation_stages and not args.save_interface_stages:
        parser.error('--save-extrapolation-stages requires --save-interface-stages')
    if args.output.exists():
        raise FileExistsError(args.output)
    import manta
    source = args.script.read_text()
    identifier = re.search(r'^dim_s(\d+)\s*=', source, re.M).group(1)
    prefix = source.split('## MAIN', 1)[0]
    # The exported main loop has a Windows path literal that is not executable
    # Python. It is excluded entirely, including all cache-write helpers.
    prefix, omitted = re.subn(r'^vdb(?:Compression|Precision)_s\d+.*$',
                              '# Unused export-only I/O enum omitted', prefix, flags=re.M)
    assert omitted == 2
    prefix = prefix.replace(f"'solver_base{identifier}'", f"'diagnostic_solver_base{identifier}'")
    prefix = prefix.replace(f"'solver_mesh{identifier}'", f"'diagnostic_solver_mesh{identifier}'")
    prefix = prefix.replace(f"'solver_particles{identifier}'", f"'diagnostic_solver_particles{identifier}'")
    tree = ast.parse(prefix)
    instrument = Instrument(identifier)
    tree = instrument.visit(tree)
    ast.fix_missing_locations(tree)
    # Vec3Grid is Blender's injected alias for the public VecGrid type.
    # IntRK4=2 follows the upstream integrator enum, not an independent test of
    # this build's RK4 accuracy. No other integrator call is substituted.
    space = dict(__name__='water_stage_probe', Vec3Grid=manta.VecGrid, IntRK4=2)
    setup = json.loads((args.case_dir/'setup.json').read_text())
    original = args.case_dir/'cache'/'data'/f'fluid_data_{args.frame:04d}.vdb'
    original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    if Path(bpy.data.filepath).resolve() != (args.case_dir/'feature.blend').resolve():
        raise ValueError('Open the original case scene for independent native particle checks')
    bpy.context.scene.frame_set(args.frame)
    native_obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    native_state = native_obj.modifiers[0].domain_settings
    native_ps = next(ps for ps in native_obj.particle_systems if ps.name.lower() == 'liquid')
    native_count = len(native_ps.particles)
    native_positions = np.empty(native_count*3, np.float32)
    native_ps.particles.foreach_get('location', native_positions)
    native_positions = native_positions.reshape(-1, 3)
    native_velocities = np.empty(native_count*3, np.float32)
    native_ps.particles.foreach_get('velocity', native_velocities)
    native_velocities = native_velocities.reshape(-1, 3)
    native_origin = np.asarray(native_obj.matrix_world @ native_state.start_point)
    native_spacing = np.asarray(native_state.cell_size)
    native_center = np.asarray(native_obj.matrix_world.translation)
    stage_dir = args.output.with_suffix('')
    if args.save_interface_stages:
        stage_dir.mkdir(exist_ok=False)
    rows = []
    report = dict(complete=False, accepted=False, frame=args.frame,
                  source_script_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  original_vdb_sha256=original_hash,
                  extra_extrapolation_checkpoints=args.save_extrapolation_stages,
                  scope=__doc__, adaptations=['Exclude main/cache loop', 'Omit unused VDB I/O enums',
                    'Unique solver object names', 'Vec3Grid=VecGrid', 'IntRK4=2',
                    'Exact fps-derived frame length', 'Ordered cleanup',
                    'Read-only MSVC particle-vector ABI validated against native API',
                    'Separate isotropic particle and rounded-grid field mappings'], rows=rows)
    error_text = None
    try:
        exec(compile(tree, str(args.script), 'exec'), space)
        assert space[f'res_s{identifier}'] == setup['resolution']
        assert abs(space[f'radiusFactor_s{identifier}']-setup['liquid_particle_radius_cells']) < 1e-6
        assert not space[f'using_apic_s{identifier}'] and not space[f'using_fractions_s{identifier}']
        dictionaries = [space[f'{name}_s{identifier}'] for name in
                        ('fluid_data_dict_final', 'fluid_data_dict_resume',
                         'liquid_data_dict_final', 'liquid_data_dict_resume')]
        objects = [value for dictionary in dictionaries for value in dictionary.values()]
        assert manta.load(name=str(original.resolve()), objects=objects,
                          worldSize=space[f'domainSize_s{identifier}']) == 1
        del objects, dictionaries
        phi = openvdb.read(str(original), 'phi')
        shape = tuple(phi.metadata['file_base_resolution'])
        expected = np.empty(shape, np.float32)
        phi.copyToArray(expected)
        np.testing.assert_array_equal(grid_array(space[f'phi_s{identifier}'], shape), expected)
        solid_grid = openvdb.read(str(original), 'phi_obstacle')
        solids = np.empty(shape, np.float32)
        solid_grid.copyToArray(solids)
        np.testing.assert_array_equal(grid_array(space[f'phiObs_s{identifier}'], shape), solids)
        report['native_scalar_layout_verified_against_original_vdb'] = True
        solver = space[f's{identifier}']
        assert tuple(int(x) for x in (space[f'gs_s{identifier}'].x,
                                      space[f'gs_s{identifier}'].y, space[f'gs_s{identifier}'].z)) == shape
        spacing = np.array(setup['dimensions_m'])/np.array(shape)
        solver.frameLength = .1*25/setup['fps']
        assert space[f'timestepsMax_s{identifier}'] == native_state.timesteps_max
        assert space[f'timestepsMin_s{identifier}'] == native_state.timesteps_min
        solver.timestepMin = solver.frameLength/native_state.timesteps_max
        solver.timestepMax = solver.frameLength/native_state.timesteps_min
        solver.cfl = native_state.cfl_condition
        solver.frame = args.frame+1
        solver.timePerFrame = 0.
        solver.adaptTimestep(space[f'vel_s{identifier}'].getMax())
        report['one_substep_seconds'] = solver.timestep/2.5
        del solver
        parts = space[f'pp_s{identifier}'].pySize()
        if parts <= 0:
            raise ValueError('Cached primary particles did not load')
        report['initial_primary_particle_count'] = parts
        assert parts == native_count
        # This build's getPos wrapper fails Vec3 return conversion. Read the
        # public data pointer instead, with its float3 + int BasicParticleData
        # ABI independently verified against Blender's native particle API.
        assert not manta.DOUBLEPRECISION
        point_pointer = space[f'pp_s{identifier}'].getDataPointer()
        point_address = vector_data_address(point_pointer, parts, 16)
        point_bytes = bytes((ctypes.c_ubyte*(parts*16)).from_address(point_address))
        point_data = np.frombuffer(point_bytes, dtype=np.dtype([('pos', '<f4', 3), ('flags', '<i4')]))
        resumed = point_data['pos']
        # Native particle display uses an isotropic, object-centered mapping,
        # unlike RNA's rounded-resolution engine cell-size mapping for fields.
        particle_spacing = setup['dimensions_m'][2]/setup['resolution']
        particle_origin = native_center-np.array(shape)*particle_spacing/2
        np.testing.assert_allclose(resumed*particle_spacing+particle_origin,
                                   native_positions, atol=1e-6, rtol=1e-6)
        report['native_particle_mapping'] = dict(isotropic_cell_size_m=particle_spacing,
             object_centered_origin_m=particle_origin.tolist(),
             field_engine_cell_size_m=native_spacing.tolist(), field_engine_origin_m=native_origin.tolist())
        velocity_pointer = space[f'pVel_pp{identifier}'].getDataPointer()
        address = vector_data_address(velocity_pointer, parts, 12)
        scalar = ctypes.c_double if manta.DOUBLEPRECISION else ctypes.c_float
        resumed_velocities = np.ctypeslib.as_array((scalar*(parts*3)).from_address(address)).copy().reshape(parts, 3)
        np.testing.assert_allclose(resumed_velocities/setup['resolution'], native_velocities,
                                   atol=1e-6, rtol=1e-6)
        report['resumed_primary_matches_native_count_positions_and_velocities'] = True

        def capture(label):
            array = grid_array(space[f'phi_s{identifier}'], shape)
            row = dict(stage=label, outside_solid_sign_volume_m3=float(np.sum((array < 0)&(solids >= 0))*np.prod(spacing)),
                       primary_particle_count=space[f'pp_s{identifier}'].pySize())
            if (label == 'before_liquid_step' or 'advectSemiLagrange' in label and 'grid=phi_' in label
                    or '.addConst(' in label or '.join(' in label or '.setBoundNeumann(' in label
                    or 'adjustNumber(' in label or args.save_extrapolation_stages
                    and f'extrapolateLsSimple(phi=phi_s{identifier},' in label):
                row['partial_cell_volume_m3'] = reconstructed_volume(array, solids, spacing, 8)['volume_m3']
                if args.save_interface_stages:
                    path = stage_dir/f'phi-stage-{len(rows):02d}.npy'
                    np.save(path, array)
                    row.update(interface_file=str(path),
                               interface_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            rows.append(row)
            args.output.write_text(json.dumps(report, indent=2))
            print('LIQUID_STAGE', json.dumps(row), flush=True)

        space['capture'] = capture
        if args.save_interface_stages:
            np.save(stage_dir/'solid.npy', solids)
            report['engine_cell_size_m'] = spacing.tolist()
            report['solid_file'] = str(stage_dir/'solid.npy')
        space[f'liquid_step_{identifier}']()
        report['complete'] = True
    except Exception as error:
        # Native grids may be retained by Python traceback frames. Do not free
        # their parent solver while such frames still reference its children.
        error_text = f'{type(error).__name__}: {error}'
        report['error'] = error_text
        args.output.write_text(json.dumps(report, indent=2))
        print('STAGE_PROBE_ERROR', error_text, flush=True)
        error.__traceback__ = None
    finally:
        args.output.write_text(json.dumps(report, indent=2))
        cleanup(space, identifier)
        report['original_vdb_unchanged'] = hashlib.sha256(original.read_bytes()).hexdigest() == original_hash
        args.output.write_text(json.dumps(report, indent=2))
    if error_text:
        raise RuntimeError(error_text)


if __name__ == '__main__':
    main()
