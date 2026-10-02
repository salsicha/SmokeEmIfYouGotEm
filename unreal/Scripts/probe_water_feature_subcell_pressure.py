"""Owned native pressure only: distance-segment versus geometric face areas.

Not a coupled solver repair: cached SDF wall normals, particle contact, liquid
surface and cell volumes are unchanged. No host emission or timestep replay.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy
import manta
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_water_feature_native_transport import actual_space, scalar_view
from probe_water_feature_solver_stages import cleanup, grid_array
from audit_water_feature_native_mac_extension import native_view
from water_feature_mac_divergence import mac_divergence


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def summary(array, mask):
    values = np.asarray(array, float)[mask]
    return dict(cells=len(values), rms=float(np.sqrt(np.mean(values*values))) if len(values) else None,
                maximum_absolute=float(np.max(np.abs(values))) if len(values) else None,
                signed_sum=float(values.sum()))


def metrics(velocity, fractions, flags, geometry, fluid_type):
    # Native lower-face indices, physical seconds: u_world = u_native*h*2.5.
    mask = (flags[:-1, :-1, :-1] & fluid_type) != 0
    mask[0] = False; mask[:, 0] = False; mask[:, :, 0] = False
    adjacent = np.zeros_like(mask)
    isolated = np.ones_like(mask)
    for axis in range(3):
        low = geometry[:-1, :-1, :-1, axis]
        slices = [slice(0, -1)]*3; slices[axis] = slice(1, None)
        high = geometry[tuple(slices)+(axis,)]
        adjacent |= ((low > 0) & (low < 1)) | ((high > 0) & (high < 1))
        isolated &= (low == 0) & (high == 0)
    own = mac_divergence(velocity*fractions, (1, 1, 1))*2.5
    actual = mac_divergence(velocity*geometry, (1, 1, 1))*2.5
    return dict(own_weighted_divergence_per_second=summary(own, mask),
        geometric_weighted_divergence_per_second=summary(actual, mask),
        geometric_cut_cell_divergence_per_second=summary(actual, mask & adjacent),
        geometric_closed_fluid_cells=int(np.count_nonzero(mask & isolated)),
        finite_velocity=bool(np.isfinite(velocity).all()))


def run(label, fields, geometry, shape, settings, fixed_flags, folder):
    scope = {}; row = dict(label=label); error = None; outputs = {}; arrays = {}
    try:
        scope['s99'] = manta.Solver(name='owned_subcell_pressure', gridSize=manta.vec3(*shape), dim=3)
        for prefix, kind in (('flags', manta.FlagGrid), ('vel', manta.MACGrid), ('fractions', manta.MACGrid),
            ('phi', manta.LevelsetGrid), ('phiObs', manta.LevelsetGrid), ('phiIn', manta.LevelsetGrid),
            ('phiOut', manta.LevelsetGrid), ('pressure', manta.RealGrid), ('rhs', manta.RealGrid)):
            scope[prefix+'_s99'] = scope['s99'].create(kind, name='owned_'+prefix)
        for prefix, name in (('phi', 'phi'), ('phiObs', 'phi_obstacle'), ('phiIn', 'phi_inflow'), ('phiOut', 'phi_out')):
            view = scalar_view(scope[prefix+'_s99'], shape); view[:] = fields[name]; del view
            np.testing.assert_array_equal(grid_array(scope[prefix+'_s99'], shape), fields[name])
        view = native_view(scope['vel_s99'], shape); view[:] = fields['velocity']; del view
        view = native_view(scope['flags_s99'], shape, integer=True); view[:] = fields['flags']; del view
        scope['pressure_s99'].setConst(0.); scope['rhs_s99'].setConst(0.)
        if label == 'native-distance-segment':
            manta.updateFractions(flags=scope['flags_s99'], phiObs=scope['phiObs_s99'],
                fractions=scope['fractions_s99'], boundaryWidth=settings['boundaryWidth'],
                fracThreshold=settings['fracThreshold'])
        else:
            view = native_view(scope['fractions_s99'], shape); view[:] = geometry; del view
        if fixed_flags is None:
            manta.setObstacleFlags(flags=scope['flags_s99'], phiObs=scope['phiObs_s99'],
                fractions=scope['fractions_s99'], phiOut=scope['phiOut_s99'], phiIn=scope['phiIn_s99'])
            scope['flags_s99'].updateFromLevelset(scope['phi_s99'])
        else:
            view = native_view(scope['flags_s99'], shape, integer=True); view[:] = fixed_flags; del view
        flags = native_view(scope['flags_s99'], shape, integer=True).copy()
        fractions = native_view(scope['fractions_s99'], shape).copy()
        if not np.isfinite(fractions).all() or np.any(fractions < 0) or np.any(fractions > 1):
            raise ValueError('Invalid actual native fractions')
        row['flag_cells_changed_from_cached'] = int(np.count_nonzero(flags != fields['flags']))
        row['flags_sha256'] = hashlib.sha256(flags.tobytes()).hexdigest()
        row['before_wall'] = metrics(fields['velocity'], fractions, flags, geometry, settings['FlagFluid'])
        # Native wall operation uses cached SDF normals, even with geometric areas.
        manta.setWallBcs(flags=scope['flags_s99'], vel=scope['vel_s99'],
            fractions=scope['fractions_s99'], phiObs=scope['phiObs_s99'])
        before = native_view(scope['vel_s99'], shape).copy()
        row['before_pressure'] = metrics(before, fractions, flags, geometry, settings['FlagFluid'])
        manta.computePressureRhs(rhs=scope['rhs_s99'], vel=scope['vel_s99'], pressure=scope['pressure_s99'],
            flags=scope['flags_s99'], phi=scope['phi_s99'], fractions=scope['fractions_s99'])
        rhs = grid_array(scope['rhs_s99'], shape)
        independent = -mac_divergence(before*fractions, (1, 1, 1))
        interior = (slice(1, -1),)*3
        fluid = (flags[interior] & settings['FlagFluid']) != 0
        # Divergence has N-1 cells; its last index is the native N-2 cell.
        delta = rhs[interior][fluid]-independent[(slice(1, None),)*3][fluid]
        row['independent_rhs_maximum_difference_native'] = float(np.max(np.abs(delta)))
        if row['independent_rhs_maximum_difference_native'] > 5e-5:
            raise ValueError('Native RHS versus independent lower-face arithmetic mismatch')
        started = time.perf_counter()
        # Explicit projection experiment, NOT native liquid_step or a CFD frame.
        manta.solvePressure(vel=scope['vel_s99'], pressure=scope['pressure_s99'], flags=scope['flags_s99'],
            phi=scope['phi_s99'], fractions=scope['fractions_s99'], cgAccuracy=1e-6, cgMaxIterFac=6.)
        row['pressure_seconds'] = time.perf_counter()-started
        after = native_view(scope['vel_s99'], shape).copy(); pressure = grid_array(scope['pressure_s99'], shape)
        if not np.isfinite(after).all():
            raise ValueError('Nonfinite native pressure velocity')
        row['after_pressure'] = metrics(after, fractions, flags, geometry, settings['FlagFluid'])
        manta.setWallBcs(flags=scope['flags_s99'], vel=scope['vel_s99'],
            fractions=scope['fractions_s99'], phiObs=scope['phiObs_s99'])
        final = native_view(scope['vel_s99'], shape).copy()
        row['after_final_wall'] = metrics(final, fractions, flags, geometry, settings['FlagFluid'])
        row['final_wall_maximum_velocity_change_native'] = float(np.max(np.abs(final-after)))
        for name, array in (('flags', flags), ('fractions', fractions), ('rhs', rhs), ('velocity-before', before),
                ('velocity-projected', after), ('velocity-final-wall', final), ('pressure', pressure)):
            path = folder/(name+'.npy')
            with path.open('xb') as stream:
                np.save(stream, array, allow_pickle=False)
            arrays[name] = str(path.resolve()); outputs[str(path.resolve())] = digest(path)
        row.update(complete=True, arrays=arrays, outputs_sha256=outputs)
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'; exc.__traceback__ = None
        row.update(complete=False, error=error)
    finally:
        cleanup(scope, '99')
    (folder/'report.json').write_text(json.dumps(row, indent=2)+'\n')
    print('SUBCELL_PRESSURE', label, row.get('after_final_wall', error), flush=True)
    return row, flags if error is None else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--apertures', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    exported = json.loads(args.inputs.read_text()); apertures = json.loads(args.apertures.read_text())
    if not exported['complete'] or not apertures['complete'] or Path(bpy.data.filepath).resolve() != Path(exported['source_blend']).resolve():
        raise ValueError('Exact native host scene and completed exports required')
    hashes = {**exported['dependency_sha256'], **exported['outputs_sha256'], **apertures['dependency_sha256'],
        **apertures['outputs_sha256'], **{str(p.resolve()): digest(p) for p in (args.inputs, args.apertures, Path(__file__))}}
    for name in ('probe_water_feature_native_transport.py', 'probe_water_feature_solver_stages.py',
                 'audit_water_feature_native_mac_extension.py', 'water_feature_mac_divergence.py'):
        p = Path(__file__).with_name(name); hashes[str(p.resolve())] = digest(p)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned pressure inputs changed')
    shape = tuple(exported['shape']); h = exported['cell_m']
    geometry = np.empty((*shape, 3), np.float32)
    for axis, path in enumerate(apertures['arrays']):
        area = np.load(path, allow_pickle=False); slices = [slice(None)]*3; slices[axis] = slice(0, shape[axis])
        geometry[..., axis] = area[tuple(slices)]/(h*h)
    fields = {name: np.load(path, allow_pickle=False) for name, path in exported['fields'].items()}
    # Read-only frame evaluation supplies exact native boundary constants.
    bpy.context.scene.frame_set(exported['frame']); source, identifier = actual_space(shape)
    settings = dict(boundaryWidth=source[f'boundaryWidth_s{identifier}'],
        fracThreshold=source[f'fracThreshold_s{identifier}'], FlagFluid=int(source['FlagFluid']))
    def fingerprint():
        return {name: hashlib.sha256(scalar_view(source[f'{name}_s{identifier}'], shape).copy().tobytes()).hexdigest()
                for name in ('phi', 'phiTmp', 'phiObs', 'phiObsIn')}
    original = fingerprint(); args.output.mkdir(); rows = []; baseline = None
    for label in ('native-distance-segment', 'geometry-fixed-native-flags', 'geometry-native-rebuilt-flags'):
        if label == 'geometry-fixed-native-flags' and baseline is None:
            raise ValueError('No valid baseline flags for matched operator comparison')
        folder = args.output/label; folder.mkdir()
        row, flags = run(label, fields, geometry, shape, settings,
                         baseline if label == 'geometry-fixed-native-flags' else None, folder)
        rows.append(row)
        if label == 'native-distance-segment':
            baseline = flags
    if fingerprint() != original or any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Owned native pressure changed source input')
    outputs = {p: sha for row in rows for p, sha in row.get('outputs_sha256', {}).items()}
    report = dict(complete=all(r['complete'] for r in rows), accepted=False, originals_unchanged=True,
        frame=exported['frame'], shape=shape, cell_m=h, source_blend=exported['source_blend'], native_settings=settings,
        explicit_projection=dict(cgAccuracy=1e-6, cgMaxIterFac=6., pressure_initial=0., phi='unchanged cached liquid',
            velocity_initial='unchanged cached MAC', physical_velocity_scale=h*2.5),
        blender_build_hash=bpy.app.build_hash.decode(), rows=rows, dependency_sha256=hashes, outputs_sha256=outputs,
        scope=__doc__, primary_particles_advanced=False, liquid_surface_changed=False,
        caveat='Same-state pressure-only operator experiment. No geometric volume/inertia, source chronology, particle collision or new surface coupling. Native final wall still uses cached distance normals. Does not qualify a bake, animation or playable scene.')
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
