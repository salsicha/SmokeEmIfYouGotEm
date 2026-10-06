"""Compare native resumed particle coordinates with Blender's displayed positions."""
import argparse
import ctypes
import json
from pathlib import Path
import sys

import bpy
import numpy as np
import manta

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_water_feature_solver_stages import vector_data_address, cleanup
from audit_water_feature_stage_volumes import sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(bpy.data.filepath).parent
    setup = json.loads((root/'setup.json').read_text())
    rows = []
    assert not manta.DOUBLEPRECISION
    for frame in args.frames:
        bpy.context.scene.frame_set(frame)
        obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        state = obj.modifiers[0].domain_settings
        shape = tuple(state.domain_resolution)
        native_ps = next(ps for ps in obj.particle_systems if ps.name.lower() == 'liquid')
        count = len(native_ps.particles)
        positions, velocities = np.empty(count*3, np.float32), np.empty(count*3, np.float32)
        native_ps.particles.foreach_get('location', positions)
        native_ps.particles.foreach_get('velocity', velocities)
        positions, velocities = positions.reshape(-1, 3), velocities.reshape(-1, 3)
        path = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        before = sha256(path)
        space, error_text = {}, None
        try:
            space['s99'] = manta.Solver(name='particle_mapping_diagnostic99', gridSize=manta.vec3(*shape), dim=3)
            space['pp_s99'] = space['s99'].create(manta.BasicParticleSystem, name='particles')
            space['pVel_pp99'] = space['pp_s99'].create(manta.PdataVec3, name='particles_velocity')
            # Match Blender's generated liquid_data_dict_final order: loading
            # the particle system last populates its attached Pdata attributes.
            assert manta.load(name=str(path), objects=[space['pVel_pp99'], space['pp_s99']],
                              worldSize=max(setup['dimensions_m'])) == 1
            assert space['pp_s99'].pySize() == count and count > 0
            address = vector_data_address(space['pp_s99'].getDataPointer(), count, 16)
            raw = bytes((ctypes.c_ubyte*(count*16)).from_address(address))
            coordinates = np.frombuffer(raw, dtype=np.dtype([('pos', '<f4', 3), ('flags', '<i4')]))['pos']
            isotropic_spacing = max(setup['dimensions_m'])/setup['resolution']
            isotropic_origin = np.asarray(obj.matrix_world.translation)-np.array(shape)*isotropic_spacing/2
            candidates = dict(isotropic_object_centered=coordinates*isotropic_spacing+isotropic_origin,
                engine_field=coordinates*np.asarray(state.cell_size)+np.asarray(obj.matrix_world @ state.start_point))
            errors = {name: dict(max_component_error_m=float(np.max(np.abs(p-positions))),
                                 rms_component_error_m=float(np.sqrt(np.mean((p-positions)**2))))
                      for name, p in candidates.items()}
            np.testing.assert_allclose(candidates['isotropic_object_centered'], positions, atol=1e-6, rtol=1e-6)
            address = vector_data_address(space['pVel_pp99'].getDataPointer(), count, 12)
            raw_velocity = np.ctypeslib.as_array((ctypes.c_float*(count*3)).from_address(address)).copy().reshape(-1, 3)
            np.testing.assert_allclose(raw_velocity/setup['resolution'], velocities, atol=1e-6, rtol=1e-6)
            rows.append(dict(frame=frame, primary_count=count, errors=errors,
                             isotropic_native_positions_and_velocities_match=True,
                             original_vdb_sha256=before))
        except Exception as error:
            error_text = f'{type(error).__name__}: {error}'
            error.__traceback__ = None
        finally:
            cleanup(space, '99')
        if error_text:
            raise RuntimeError(error_text)
        if sha256(path) != before:
            raise ValueError('Original VDB changed')
        print('PARTICLE_MAPPING', json.dumps(rows[-1]), flush=True)
    with args.output.open('x') as stream:
        json.dump(dict(complete=True, accepted=False, frames=rows, originals_unchanged=True,
                       scope='Particle display coordinate mapping only. Does not establish dense-grid hydraulic accuracy, physical collision clearance, conserved mass or closed eddy trajectories.'), stream, indent=2)


if __name__ == '__main__':
    main()
