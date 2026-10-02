"""Matched geometry-preparation/native steps: cached versus closest-mesh fields.

Diagnostic only: exact installed step code, private grids/particles, no host
emission/pre-step replay or replacement of a preserved/native-playable cache.
Closest-node distances still have trilinear corner error; no acceptance implied.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy
import manta
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_water_feature_native_transport import actual_space, make_owned, load_and_verify, scalar_view
from probe_water_feature_solver_stages import cleanup, grid_array, vector_data_address
from audit_water_feature_native_mac_extension import native_view
from water_feature_cache_stages import decode_configuration
from water_feature_geometry import world_coordinates
from audit_water_feature_mesh_contact import topology, contact, interior_distance
from water_feature_field_surface import sample_centers, regularize_exact_mesh
from water_feature_native_field_mesh import extract
from water_feature_cell_volume import reconstructed_volume


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def nearest_union(shape, origin, h, solids):
    result = np.empty(shape, np.float32)
    started = time.perf_counter()
    for i in range(shape[0]):
        for j in range(shape[1]):
            for k in range(shape[2]):
                p = origin+(np.array([i, j, k])+.5)*h; values = []
                for lo, hi, tree in solids.values():
                    _, _, _, distance = tree.find_nearest(Vector(p))
                    if distance is None:
                        raise ValueError('Missing closest authored collider')
                    inside = np.all(p > lo+1e-6) and np.all(p < hi-1e-6) and interior_distance(tree, p) > 0
                    values.append(-distance if inside else distance)
                result[i, j, k] = min(values)/h
    return result, time.perf_counter()-started


def primary(space, identifier, origin, h):
    particles = space[f'pp_s{identifier}']; count = particles.pySize()
    ptr = vector_data_address(particles.getDataPointer(), count, 16)
    records = np.frombuffer(bytes((ctypes.c_ubyte*(count*16)).from_address(ptr)),
        dtype=np.dtype([('position', '<f4', 3), ('flags', '<i4')]))
    values, counts = np.unique(records['flags'], return_counts=True)
    return records['position']*h+origin, dict(zip(map(str, values), map(int, counts)))


def measure(space, identifier, shape, origin, h, solids):
    p, flags = primary(space, identifier, origin, h)
    phi = grid_array(space[f'phi_s{identifier}'], shape)
    obs = grid_array(space[f'phiObs_s{identifier}'], shape)
    return dict(primary_count=len(p), all_particle_flags=flags,
        primary_authored_contact={name: contact(p, solid) for name, solid in solids.items()},
        primary_obstacle_interpolation_minimum_cells=float(sample_centers(obs, (p-origin)/h).min()),
        liquid_field_volume=reconstructed_volume(phi, obs, (h, h, h), 8),
        finite_phi=bool(np.isfinite(phi).all()),
        physical_native_clock=dict(frame=space[f's{identifier}'].frame,
            time_total_native=space[f's{identifier}'].timeTotal,
            time_per_frame_native=space[f's{identifier}'].timePerFrame))


def run(source, identifier, root, frame, shape, origin, h, solids, displayed_p, displayed_v,
        replacement, folder, hashes):
    owned = {}; error = None; row = None
    try:
        owned, calls, created, proof = make_owned(source, identifier, shape, owned)
        geometry_grids = []
        # These are used by actual native pre-step obstacle flag construction,
        # not necessarily reachable from liquid_step. Allocate and load them
        # explicitly; never share a live native grid or invent absent globals.
        for prefix, cache_name in (('phiOut', 'phi_out'), ('phiIn', 'phi_inflow')):
            key = f'{prefix}_s{identifier}'
            if key in owned:
                continue
            value = source.get(key)
            if type(value).__name__ != 'LevelsetGrid':
                raise ValueError('Actual geometry-input level set missing: '+key)
            owned[key] = owned[f's{identifier}'].create(manta.LevelsetGrid, name=cache_name)
            geometry_grids.append(dict(name=key, cache_name=cache_name))
        data = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        config_path = root/'cache'/'config'/f'config_{frame:04d}.uni'
        for p in (data, config_path):
            hashes[str(p.resolve())] = digest(p)
        verification = load_and_verify(owned, identifier, shape, data, 6.75,
            displayed_p, displayed_v, origin, h, 90)
        config = decode_configuration(config_path.read_bytes())
        solver = owned[f's{identifier}']; state = bpy.data.objects['Feature liquid'].modifiers[0].domain_settings
        solver.frameLength = .1*25/24
        solver.timestepMin = solver.frameLength/state.timesteps_max
        solver.timestepMax = solver.frameLength/state.timesteps_min
        solver.cfl = state.cfl_condition; solver.frame = frame+1
        solver.timePerFrame = 0; solver.timeTotal = config['time_total_native']
        solver.adaptTimestep(owned[f'vel_s{identifier}'].getMax())
        dt = solver.timestep; del solver
        original_flags = native_view(owned[f'flags_s{identifier}'], shape, integer=True).copy()
        fractional = bool(source[f'using_fractions_s{identifier}'])
        original_fractions = native_view(owned[f'fractions_s{identifier}'], shape).copy() if fractional else None
        row = dict(frame=frame, replacement=replacement is not None, exact_binding=proof,
            additional_geometry_flag_grids=geometry_grids,
            resume_verification=verification, native_timestep=dt, physical_substep_seconds=dt/2.5,
            before=measure(owned, identifier, shape, origin, h, solids))
        if replacement is not None:
            for prefix in ('phiObs', 'phiObsIn'):
                view = scalar_view(owned[f'{prefix}_s{identifier}'], shape)
                view[:] = replacement; del view
        # BOTH controls receive the same native geometry preparation protocol.
        # Fractions are not cached; restoring them is mandatory before pressure.
        # Cached final/input obstacle fields remain distinct in the baseline.
        if fractional:
            manta.updateFractions(flags=owned[f'flags_s{identifier}'],
                phiObs=owned[f'phiObs_s{identifier}'], fractions=owned[f'fractions_s{identifier}'],
                boundaryWidth=source[f'boundaryWidth_s{identifier}'],
                fracThreshold=source[f'fracThreshold_s{identifier}'])
        manta.setObstacleFlags(flags=owned[f'flags_s{identifier}'],
            phiObs=owned[f'phiObs_s{identifier}'], phiOut=owned[f'phiOut_s{identifier}'],
            fractions=owned[f'fractions_s{identifier}'] if fractional else None,
            phiIn=owned[f'phiIn_s{identifier}'])
        row['matched_native_geometry_preparation'] = True
        row['uncached_fractions_reconstructed'] = fractional
        row['changed_flag_cells'] = int(np.count_nonzero(original_flags != native_view(owned[f'flags_s{identifier}'], shape, integer=True)))
        row['changed_fraction_scalars'] = int(np.count_nonzero(original_fractions != native_view(owned[f'fractions_s{identifier}'], shape))) if fractional else 0
        row['after_geometry_before_step'] = measure(owned, identifier, shape, origin, h, solids)
        started = time.perf_counter(); owned[f'liquid_step_{identifier}']()
        row['step_seconds'] = time.perf_counter()-started
        row['after_native_step'] = measure(owned, identifier, shape, origin, h, solids)
        outputs = {}; arrays = {}
        phi = grid_array(owned[f'phi_s{identifier}'], shape)
        obs = grid_array(owned[f'phiObs_s{identifier}'], shape)
        for name, array in (('phi', phi), ('obstacle', obs),
            ('velocity', native_view(owned[f'vel_s{identifier}'], shape).copy()),
            ('pressure', grid_array(owned[f'pressure_s{identifier}'], shape))):
            if not np.isfinite(array).all():
                raise ValueError('Nonfinite actual native step output')
            path = folder/f'{name}.npy'
            with path.open('xb') as stream:
                np.save(stream, array, allow_pickle=False)
            outputs[str(path.resolve())] = digest(path); arrays[name] = str(path.resolve())
        row.update(arrays=arrays, outputs_sha256=outputs)
        print('CORNER_EVOLUTION_STEP', root.name, frame, bool(replacement is not None),
              row['before']['primary_count'], row['after_native_step']['primary_count'], flush=True)
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'; exc.__traceback__ = None
    finally:
        if f'liquid_step_{identifier}' in owned:
            owned[f'liquid_step_{identifier}'].__globals__.clear()
        cleanup(owned, identifier)
    if error:
        raise RuntimeError(error)
    # Native extraction owns separate parents, after the private pressure solve
    # has been freed. Preserve the resulting still-unaccepted surface unchanged.
    path = folder/'surface.obj'; raw, triangles, extraction = extract(phi, obs, 2, path)
    v, triangles, exact = regularize_exact_mesh(raw, triangles)
    world = origin+(v.astype(float)/2+extraction['base_coordinate_offset_cells'])*h
    row['derived_contact'] = {name: dict(vertices=contact(world, solid),
        triangle_centers=contact(world[triangles].mean(1), solid)) for name, solid in solids.items()}
    row['derived_topology'] = topology(triangles); row['exact_cleanup'] = exact
    row['outputs_sha256'][str(path.resolve())] = digest(path)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    audit = json.loads(args.audit.read_text()); control = audit['controls'][0]
    source_blend = Path(control['source_blend']); root = source_blend.parent
    if Path(bpy.data.filepath).resolve() != source_blend.resolve() or not audit['complete'] or audit['accepted']:
        raise ValueError('Exact completed unaccepted source required')
    shape = tuple(control['shape']); origin = np.array(control['origin_m']); h = control['cell_m']
    if shape != (90, 31, 42) or abs(h-.075) > 1e-9:
        raise ValueError('Explicit physical-wall control required')
    hashes = {str(p.resolve()): digest(p) for p in (Path(__file__), args.audit, source_blend)}
    for name in ('probe_water_feature_native_transport.py', 'probe_water_feature_solver_stages.py',
        'audit_water_feature_native_mac_extension.py', 'water_feature_cache_stages.py',
        'water_feature_geometry.py', 'audit_water_feature_mesh_contact.py', 'water_feature_field_surface.py',
        'water_feature_native_field_mesh.py', 'water_feature_cell_volume.py', 'water_feature_private_step.py'):
        p = Path(__file__).with_name(name); hashes[str(p.resolve())] = digest(p)
    domain = bpy.data.objects['Feature liquid']
    domain.modifiers[0].domain_settings.cache_directory = str(root/'cache')
    bpy.context.scene.frame_set(169); source, identifier = actual_space(shape)
    solids = {}
    for entry in control['colliders']:
        obj = bpy.data.objects[entry['name']].evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = obj.to_mesh()
        try:
            mesh.calc_loop_triangles()
            v = world_coordinates([p.co[:] for p in mesh.vertices], obj.matrix_world)
            t = np.array([p.vertices[:] for p in mesh.loop_triangles], np.int64)
            if topology(t) != dict(boundary_edges=0, nonmanifold_edges=0):
                raise ValueError('Closed collider required')
            if hashlib.sha256(v.tobytes()+t.tobytes()).hexdigest() != entry['geometry_sha256']:
                raise ValueError('Pinned geometry changed')
            solids[entry['name']] = (v.min(0), v.max(0), BVHTree.FromPolygons(v.tolist(), t.tolist(), all_triangles=True))
        finally:
            obj.to_mesh_clear()
    if len(solids) != 8:
        raise ValueError('All original physical walls required')
    corrected, cost = nearest_union(shape, origin, h, solids)
    args.output.mkdir(); path = args.output/'closest-mesh-obstacle.npy'
    with path.open('xb') as stream:
        np.save(stream, corrected, allow_pickle=False)
    outputs = {str(path.resolve()): digest(path)}
    print('CORNER_CLOSEST_FIELD_READY', root.name, cost, flush=True)
    rows = []; live_rows = []
    for frame in (145, 169, 191):
        bpy.context.scene.frame_set(frame); source, identifier = actual_space(shape)
        def fingerprint():
            return {n: hashlib.sha256((native_view(source[f'{n}_s{identifier}'], shape).copy()
                if n.startswith('vel') else scalar_view(source[f'{n}_s{identifier}'], shape).copy()).tobytes()).hexdigest()
                for n in ('phi', 'phiTmp', 'phiObs', 'phiObsIn', 'vel', 'velTmp')}
        before = fingerprint()
        for prefix in ('forces', 'obvel'):
            if np.count_nonzero(native_view(source[f'{prefix}_s{identifier}'], shape)):
                raise ValueError('Nonzero uncached force/solid velocity requires separate recovery')
        particles = next(p for p in domain.evaluated_get(bpy.context.evaluated_depsgraph_get()).particle_systems if p.name.lower() == 'liquid')
        count = len(particles.particles); p = np.empty(count*3, np.float32); v = np.empty(count*3, np.float32)
        particles.particles.foreach_get('location', p); particles.particles.foreach_get('velocity', v)
        for label, replacement in (('cached', None), ('closest-mesh', corrected)):
            folder = args.output/f'{frame:04d}-{label}'; folder.mkdir()
            row = run(source, identifier, root, frame, shape, origin, h, solids, p.reshape(-1, 3),
                      v.reshape(-1, 3), replacement, folder, hashes)
            row['label'] = label; rows.append(row); outputs.update(row['outputs_sha256'])
        if fingerprint() != before:
            raise ValueError('Private geometry evolution changed engine fields')
        live_rows.append(dict(frame=frame, unchanged=True))
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Private evolution changed preserved inputs')
    report = dict(complete=True, accepted=False, originals_unchanged=True, dependency_sha256=hashes,
        outputs_sha256=outputs, source_blend=str(source_blend.resolve()), shape=list(shape), origin_m=origin.tolist(),
        cell_m=h, closest_mesh_field_seconds=cost, live_fields=live_rows, rows=rows, scope=__doc__,
        caveats='Partial native-step experiment, not full scene chronology or a repaired bake. No emission/solid pre-step rebuild, external moving-solid force, secondary particles or new hydraulic acceptance. Both controls reconstruct native geometry flags and uncached fractions before the exact installed step; final/input cached distances stay distinct in the baseline. Pressure/contact/fractions consume corrected distances together on owned resources. Exact node sampling still interpolates corners and is not exact subcell geometry.')
    with (args.output/'report.json').open('x') as stream:
        json.dump(report, stream, indent=2)
    print('CORNER_FIELD_EVOLUTION_COMPLETE', root.name, len(rows), flush=True)


if __name__ == '__main__':
    error = None
    try:
        main()
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'; exc.__traceback__ = None
    if error:
        print('CORNER_FIELD_EVOLUTION_FAILED', error, flush=True); raise SystemExit(1)
