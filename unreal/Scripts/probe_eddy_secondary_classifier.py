"""Read-only native occupancy/phase mechanism probe on preserved eddy fields.

Recomputing a frozen-field local classifier is not replaying the cached frame,
fixing particle types or changing original simulation/render evidence.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import bpy
import manta
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_water_feature_solver_stages import grid_array, vector_data_address, cleanup
from water_feature_neighbor_ratio import occupancy_ratio, phase_bits
from water_feature_phase_samples import sample_centers


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def int_grid(grid, shape):
    assert (grid.getSizeX(), grid.getSizeY(), grid.getSizeZ()) == shape
    pointer = grid.getDataPointer()
    address = int(pointer, 16) if isinstance(pointer, str) else int(pointer)
    if address <= 0:
        raise ValueError('Null grid')
    return np.ctypeslib.as_array((ctypes.c_int32*int(np.prod(shape))).from_address(address)).copy().reshape(shape[::-1]).transpose(2, 1, 0)


def particles(space):
    count = space['pp_s98'].pySize()
    address = vector_data_address(space['pp_s98'].getDataPointer(), count, 16)
    return np.frombuffer(bytes((ctypes.c_ubyte*(count*16)).from_address(address)),
                         dtype=np.dtype([('pos', '<f4', 3), ('flags', '<i4')])).copy()


def frame_probe(root, setup, frame, hashes):
    bpy.context.scene.frame_set(frame)
    obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    state = obj.modifiers[0].domain_settings
    shape = tuple(state.domain_resolution)
    if state.particle_scale != 1 or state.sndparticle_potential_radius != 2:
        raise ValueError('Probe requires unchanged 1x aligned secondary grid, radius2')
    spacing = max(setup['dimensions_m'])/setup['resolution']
    origin = np.asarray(obj.matrix_world.translation)-np.array(shape)*spacing/2
    data = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
    phase = root/'cache'/'particles'/f'fluid_particles_{frame:04d}.vdb'
    hashes.update({str(p): digest(p) for p in (data, phase)})
    space, error_text, result = {}, None, None
    try:
        space['s98'] = manta.Solver(name='classifier_probe98', gridSize=manta.vec3(*shape), dim=3)
        for key, kind, name in [
            ('phi_s98', manta.LevelsetGrid, 'phi'),
            ('previous_s98', manta.LevelsetGrid, 'phi_previous'),
            ('obstacle_s98', manta.LevelsetGrid, 'phi_obstacle'),
            ('out_s98', manta.LevelsetGrid, 'phi_out'),
            ('velocity_s98', manta.MACGrid, 'velocity_previous')]:
            space[key] = space['s98'].create(kind, name=name)
        assert manta.load(name=str(data.resolve()), objects=[space[k] for k in
            ('phi_s98', 'previous_s98', 'obstacle_s98', 'out_s98', 'velocity_s98')],
            worldSize=max(setup['dimensions_m'])) == 1
        arrays = {}
        for key, name in [('phi_s98', 'phi'), ('previous_s98', 'phi_previous'),
                          ('obstacle_s98', 'phi_obstacle'), ('out_s98', 'phi_out')]:
            arrays[name] = np.empty(shape, np.float32)
            openvdb.read(str(data), name).copyToArray(arrays[name])
            np.testing.assert_array_equal(grid_array(space[key], shape), arrays[name])
        for key, kind in [('flags_s98', manta.FlagGrid), ('ratio_s98', manta.RealGrid),
                          ('air_s98', manta.RealGrid), ('crest_s98', manta.RealGrid),
                          ('energy_s98', manta.RealGrid), ('normal_s98', manta.VecGrid),
                          ('zero_velocity_s98', manta.MACGrid)]:
            space[key] = space['s98'].create(kind, name=key)
        space['zero_velocity_s98'].setConst(manta.vec3(0, 0, 0))
        space['pp_s98'] = space['s98'].create(manta.BasicParticleSystem, name='particles_secondary')
        space['velocity_pp98'] = space['pp_s98'].create(manta.PdataVec3, name='particles_velocity_secondary')
        space['life_pp98'] = space['pp_s98'].create(manta.PdataReal, name='particles_life_secondary')
        space['force_pp98'] = space['pp_s98'].create(manta.PdataVec3, name='diagnostic_force')
        assert manta.load(name=str(phase.resolve()), objects=[space[k] for k in
            ('velocity_pp98', 'life_pp98', 'pp_s98')], worldSize=max(setup['dimensions_m'])) == 1
        original = particles(space)
        count = len(original)
        assert count == sum(len(ps.particles) for ps in obj.particle_systems
                            if ps.name.lower() in ('spray', 'foam', 'bubbles'))
        positions = original['pos']*spacing+origin
        current_phi, supported = sample_centers(arrays['phi'], positions, origin, np.full(3, spacing))
        prior_phi, prior_supported = sample_centers(arrays['phi_previous'], positions, origin, np.full(3, spacing))
        assert supported.all() and prior_supported.all()
        field_rows = []
        for label, key in [('previous', 'previous_s98'), ('current', 'phi_s98')]:
            manta.setObstacleFlags(flags=space['flags_s98'], phiObs=space['obstacle_s98'],
                                   phiOut=space['out_s98'], phiIn=None, boundaryWidth=0)
            space['flags_s98'].updateFromLevelset(levelset=space[key])
            flags = int_grid(space['flags_s98'], shape)
            # Native bit counts validate the independently read integer layout.
            for bit in (1, 2, 4, 8, 16):
                assert space['flags_s98'].countCells(flag=bit) == int(((flags & bit) != 0).sum())
            manta.flipComputeSecondaryParticlePotentials(potTA=space['air_s98'],
                potWC=space['crest_s98'], potKE=space['energy_s98'],
                neighborRatio=space['ratio_s98'], flags=space['flags_s98'],
                v=space['velocity_s98'], normal=space['normal_s98'], phi=space[key],
                radius=2, tauMinTA=5, tauMaxTA=20, tauMinWC=2, tauMaxWC=8,
                tauMinKE=1, tauMaxKE=5, scaleFromManta=spacing/2.5)
            ratio = grid_array(space['ratio_s98'], shape)
            reference, _, active = occupancy_ratio(flags, 2, 1, 2 | 8 | 16)
            np.testing.assert_allclose(ratio, reference, atol=1e-7, rtol=1e-7)
            # Run only classification/transport on a disposable copy; no emission,
            # cache-write or force-field substitution in the actual simulation.
            assert manta.load(name=str(phase.resolve()), objects=[space[k] for k in
                ('velocity_pp98', 'life_pp98', 'pp_s98')], worldSize=max(setup['dimensions_m'])) == 1
            space['force_pp98'].setConst(manta.vec3(0, 0, 0))
            manta.flipUpdateSecondaryParticles(mode='linear', pts_sec=space['pp_s98'],
                v_sec=space['velocity_pp98'], l_sec=space['life_pp98'], f_sec=space['force_pp98'],
                flags=space['flags_s98'], v=space['zero_velocity_s98'],
                neighborRatio=space['ratio_s98'], radius=2, gravity=manta.vec3(0, 0, 0),
                scale=False, k_b=.5, k_d=.6, c_s=.4, c_b=.77, dt=1e-8)
            updated = particles(space)
            if len(updated) != count:
                raise ValueError('Frozen classifier probe lost particles; no order comparison allowed')
            deltas = np.max(np.abs(updated['pos']-original['pos']), axis=1)
            if float(deltas.max())*spacing > 1e-5:
                raise ValueError('Diagnostic timestep displacement exceeds10 micrometres')
            observed = updated['flags'] & (2 | 4 | 8)
            cast_matches = {}
            for cast, ids in [('floor', np.floor(original['pos']).astype(int)),
                              ('nearest', np.floor(original['pos']+.5).astype(int))]:
                if np.any(ids < 0) or np.any(ids >= np.array(shape)):
                    cast_matches[cast] = None
                    continue
                expected = phase_bits(ratio[tuple(ids.T)])
                cast_matches[cast] = float(np.mean(expected == observed))
            if max(v or 0 for v in cast_matches.values()) != 1:
                raise ValueError('Neither independent cell cast reproduces native phase classification')
            phases = []
            cell_ids = np.floor(original['pos']).astype(int)
            cell_flags = flags[tuple(cell_ids.T)]
            cell_ratio = ratio[tuple(cell_ids.T)]
            kernel_supported = np.all((cell_ids >= 2) & (cell_ids < np.array(shape)-2), axis=1)
            cell_fluid = (cell_flags & 1) != 0
            for name, bit in [('spray', 2), ('bubbles', 4), ('foam', 8)]:
                selected = (original['flags'] & bit) != 0
                phases.append(dict(name=name, original_count=int(selected.sum()),
                    original_type_matches_frozen_classifier_fraction=float(np.mean(observed[selected] == bit)),
                    floor_cell_fluid_fraction=float(np.mean(cell_fluid[selected])),
                    floor_cell_obstacle_fraction=float(np.mean((cell_flags[selected] & 2) != 0)),
                    unsupported_kernel_fluid_fraction=float(np.mean((~kernel_supported & cell_fluid)[selected])),
                    zero_occupancy_ratio_fraction=float(np.mean(cell_ratio[selected] == 0)),
                    occupancy_ratio_quantiles=np.quantile(cell_ratio[selected], [.05, .5, .95]).tolist(),
                    frozen_spray_negative_current_phi_fraction=float(np.mean(((observed == 2) & (current_phi < 0))[selected])),
                    position_z_m_quantiles=np.quantile(positions[selected, 2], [.05, .5, .95]).tolist(),
                    frozen_classified_counts={str(b): int(np.sum(observed[selected] == b)) for b in (2, 4, 8)},
                    original_positions_current_phi_negative_fraction=float(np.mean(current_phi[selected] < 0)),
                    original_positions_previous_phi_negative_fraction=float(np.mean(prior_phi[selected] < 0)),
                    current_phi_cells_quantiles=np.quantile(current_phi[selected], [.05, .5, .95]).tolist(),
                    previous_phi_cells_quantiles=np.quantile(prior_phi[selected], [.05, .5, .95]).tolist()))
            field_rows.append(dict(field=label, native_ratio_matches_independent_reference=True,
                maximum_ratio_error=float(np.max(np.abs(ratio-reference))),
                native_classifier_matches_cell_cast_fraction=cast_matches,
                maximum_local_step_displacement_m=float(deltas.max())*spacing,
                active_ratio_cell_count=int(active.sum()), phases=phases))
        result = dict(frame=frame, count=count, fields=field_rows,
                      scalar_layout_matches_original_vdb=True)
    except Exception as error:
        error_text = f'{type(error).__name__}: {error}'
        error.__traceback__ = None
    finally:
        cleanup(space, '98')
    if error_text:
        raise RuntimeError(error_text)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[168, 192, 214])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    assert not manta.DOUBLEPRECISION
    root = Path(bpy.data.filepath).resolve().parent
    setup = json.loads((root/'setup.json').read_text())
    bake = json.loads((root/'bake-particles.json').read_text())
    if setup['case'] != 'eddy' or not bake['baked_particles'] or Path(bake['blend']).resolve() != Path(bpy.data.filepath).resolve():
        raise ValueError('Completed independent eddy secondary stage required')
    hashes = {bpy.data.filepath: digest(Path(bpy.data.filepath))}
    rows = []
    for frame in args.frames:
        rows.append(frame_probe(root, setup, frame, hashes))
        print('CLASSIFIER_FRAME', json.dumps(rows[-1]), flush=True)
    if any(digest(Path(path)) != value for path, value in hashes.items()):
        raise ValueError('Preserved input changed')
    with args.output.open('x') as stream:
        json.dump(dict(complete=True, accepted=False, originals_unchanged=True, frames=rows,
            original_file_sha256=hashes,
            scope='Independent occupancy and installed frozen-field phase-update mechanism. Previous/current field comparison, not actual emission/time-step replay, calibrated bubble forces, physical interface correction, optical or hydraulic acceptance.'), stream, indent=2)


if __name__ == '__main__':
    main()
