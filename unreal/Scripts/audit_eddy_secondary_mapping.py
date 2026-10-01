"""Independently load native secondary coordinates/type flags and match Blender API."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import bpy
import manta
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_water_feature_solver_stages import vector_data_address, cleanup


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[168, 192, 214])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(bpy.data.filepath).parent
    setup = json.loads((root/'setup.json').read_text())
    bake = json.loads((root/'bake-particles.json').read_text())
    if setup['case'] != 'eddy' or not bake['baked_particles'] or Path(bake['blend']).resolve() != Path(bpy.data.filepath).resolve():
        raise ValueError('Completed native eddy secondary stage required')
    assert not manta.DOUBLEPRECISION
    rows, hashes = [], {bpy.data.filepath: digest(Path(bpy.data.filepath))}
    # Installed/native flags are independently confirmed against each API phase
    # count and every position/velocity, not accepted from labels alone.
    flags_by_name = {'spray': 2, 'bubbles': 4, 'foam': 8}
    for frame in args.frames:
        bpy.context.scene.frame_set(frame)
        obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        state = obj.modifiers[0].domain_settings
        if state.particle_scale != 1:
            raise ValueError('This diagnostic requires the authored 1x secondary grid')
        shape = tuple(state.domain_resolution)
        phase_systems = {p.name.lower(): p for p in obj.particle_systems if p.name.lower() in flags_by_name}
        path = root/'cache'/'particles'/f'fluid_particles_{frame:04d}.vdb'
        hashes[str(path)] = digest(path)
        space, error_text = {}, None
        try:
            space['s98'] = manta.Solver(name='secondary_mapping98', gridSize=manta.vec3(*shape), dim=3)
            space['pp_s98'] = space['s98'].create(manta.BasicParticleSystem, name='particles_secondary')
            space['pVel_pp98'] = space['pp_s98'].create(manta.PdataVec3, name='particles_velocity_secondary')
            space['pLife_pp98'] = space['pp_s98'].create(manta.PdataReal, name='particles_life_secondary')
            assert manta.load(name=str(path), objects=[space['pVel_pp98'], space['pLife_pp98'], space['pp_s98']],
                              worldSize=max(setup['dimensions_m'])) == 1
            count = space['pp_s98'].pySize()
            assert count == sum(len(p.particles) for p in phase_systems.values()) and count > 0
            address = vector_data_address(space['pp_s98'].getDataPointer(), count, 16)
            data = np.frombuffer(bytes((ctypes.c_ubyte*(count*16)).from_address(address)),
                                dtype=np.dtype([('pos', '<f4', 3), ('flags', '<i4')])).copy()
            address = vector_data_address(space['pVel_pp98'].getDataPointer(), count, 12)
            raw_velocity = np.ctypeslib.as_array((ctypes.c_float*(count*3)).from_address(address)).copy().reshape(-1, 3)
            spacing = max(setup['dimensions_m'])/setup['resolution']
            origin = np.asarray(obj.matrix_world.translation)-np.array(shape)*spacing/2
            phases = []
            for name, bit in flags_by_name.items():
                selected = (data['flags'] & bit) != 0
                ps = phase_systems[name]
                assert int(selected.sum()) == len(ps.particles)
                pos, vel = np.empty(len(ps.particles)*3, np.float32), np.empty(len(ps.particles)*3, np.float32)
                ps.particles.foreach_get('location', pos)
                ps.particles.foreach_get('velocity', vel)
                pos, vel = pos.reshape(-1, 3), vel.reshape(-1, 3)
                reconstructed = data['pos'][selected]*spacing+origin
                np.testing.assert_allclose(reconstructed, pos, atol=1e-6, rtol=1e-6)
                np.testing.assert_allclose(raw_velocity[selected]/setup['resolution'], vel, atol=1e-6, rtol=1e-6)
                phases.append(dict(name=name, type_bit=bit, count=len(pos), all_positions_and_velocities_match=True,
                    maximum_position_component_error_m=float(np.max(np.abs(reconstructed-pos))),
                    positions_sha256=hashlib.sha256(pos.ravel().tobytes()).hexdigest()))
            rows.append(dict(frame=frame, count=count, phases=phases))
        except Exception as error:
            error_text = f'{type(error).__name__}: {error}'
            error.__traceback__ = None
        finally:
            cleanup(space, '98')
        if error_text:
            raise RuntimeError(error_text)
        print('SECONDARY_MAPPING', json.dumps(rows[-1]), flush=True)
    if any(digest(Path(path)) != value for path, value in hashes.items()):
        raise ValueError('Original evidence changed')
    with args.output.open('x') as stream:
        json.dump(dict(complete=True, accepted=False, originals_unchanged=True, frames=rows,
            original_file_sha256=hashes,
            scope='Independent native cache/type/coordinate/API-velocity equality. Not calibrated secondary physical velocities, pressure/phase coupling, air-water classification, mass conservation or optical acceptance.'), stream, indent=2)


if __name__ == '__main__':
    main()
