"""Actual native velocity response versus consistent pressure/flux reference.

Owned grids only; no source/domain/cache mutation or full fluid step. Native
response is checked against prior saved projection, not inferred from a name.
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
from water_feature_consistent_pressure import PressureBoundary, flux_divergence
from probe_water_feature_solver_stages import cleanup, grid_array
from probe_water_feature_native_transport import scalar_view
from audit_water_feature_native_mac_extension import native_view


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def stats(array, mask):
    a = np.asarray(array, float)[mask]
    return dict(cells=len(a), rms=float(np.sqrt(np.mean(a*a))) if len(a) else None,
                maximum_absolute=float(np.max(np.abs(a))) if len(a) else None)


def cohorts(flags, fractions, fluid_type, empty_type, outflow_type):
    masks = dict(all=(flags & fluid_type) != 0)
    empty = np.zeros(flags.shape, bool); out = empty.copy(); cut = empty.copy()
    for axis in range(3):
        low = [slice(None)]*3; high = list(low); low[axis] = slice(None, -1); high[axis] = slice(1, None)
        low, high = tuple(low), tuple(high)
        empty[low] |= (flags[high] & empty_type) != 0; empty[high] |= (flags[low] & empty_type) != 0
        out[low] |= (flags[high] & outflow_type) != 0; out[high] |= (flags[low] & outflow_type) != 0
        f = fractions[high+(axis,)]; partial = (f > 0) & (f < 1)
        cut[low] |= partial; cut[high] |= partial
    fluid = masks['all']
    masks.update(outflow_adjacent=fluid & out, free_surface_nonoutflow=fluid & empty & ~out,
        cut_free_surface_nonoutflow=fluid & empty & cut & ~out, no_empty_neighbor=fluid & ~empty,
        cut_no_empty_neighbor=fluid & cut & ~empty)
    return masks


def native_response(flags, phi, fractions, velocity, pressure, use_phi, candidate=None):
    shape = flags.shape; scope = {}; error = None; output = None; rhs = None
    try:
        scope['s99'] = manta.Solver(name='owned_pressure_boundary_response', gridSize=manta.vec3(*shape), dim=3)
        for name, kind in (('flags', manta.FlagGrid), ('phi', manta.LevelsetGrid), ('fractions', manta.MACGrid),
                           ('vel', manta.MACGrid), ('pressure', manta.RealGrid), ('rhs', manta.RealGrid)):
            scope[name+'_s99'] = scope['s99'].create(kind, name='owned_'+name)
        for name, array in (('phi', phi), ('pressure', pressure)):
            view = scalar_view(scope[name+'_s99'], shape); view[:] = array; del view
            np.testing.assert_array_equal(grid_array(scope[name+'_s99'], shape), array.astype(np.float32))
        view = native_view(scope['flags_s99'], shape, integer=True); view[:] = flags; del view
        for name, array in (('fractions', fractions), ('vel', velocity if candidate is None else candidate)):
            view = native_view(scope[name+'_s99'], shape); view[:] = array; del view
        if candidate is None:
            manta.correctVelocity(vel=scope['vel_s99'], pressure=scope['pressure_s99'], flags=scope['flags_s99'],
                phi=scope['phi_s99'] if use_phi else None, fractions=scope['fractions_s99'])
        output = native_view(scope['vel_s99'], shape).copy()
        if not np.isfinite(output).all():
            raise ValueError('Nonfinite native corrected velocity')
        scope['rhs_s99'].setConst(0.)
        manta.computePressureRhs(rhs=scope['rhs_s99'], vel=scope['vel_s99'], pressure=scope['pressure_s99'],
            flags=scope['flags_s99'], phi=scope['phi_s99'], fractions=scope['fractions_s99'])
        rhs = grid_array(scope['rhs_s99'], shape)
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'; exc.__traceback__ = None
    finally:
        cleanup(scope, '99')
    if error:
        raise RuntimeError(error)
    return output, rhs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--pressure', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    inputs = json.loads(args.inputs.read_text()); receipt = json.loads(args.pressure.read_text())
    if Path(bpy.data.filepath).resolve() != Path(inputs['source_blend']).resolve():
        raise ValueError('Exact native scene host required before importing manta')
    hashes = {**inputs['dependency_sha256'], **inputs['outputs_sha256'],
        **receipt['dependency_sha256'], **receipt['outputs_sha256'],
        **{str(p.resolve()): digest(p) for p in (args.inputs, args.pressure, Path(__file__))}}
    for name in ('water_feature_consistent_pressure.py', 'probe_water_feature_solver_stages.py',
                 'probe_water_feature_native_transport.py', 'audit_water_feature_native_mac_extension.py'):
        p = Path(__file__).with_name(name); hashes[str(p.resolve())] = digest(p)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned original pressure evidence changed')
    # Initialize native namespace read-only; never set a Domain RNA property.
    bpy.context.scene.frame_set(inputs['frame'])
    from probe_water_feature_native_transport import actual_space
    source, identifier = actual_space(tuple(inputs['shape']))
    fluid_type, empty_type, outflow_type = (int(source[k]) for k in ('FlagFluid', 'FlagEmpty', 'FlagOutflow'))
    initial_host = {k: hashlib.sha256(scalar_view(source[f'{k}_s{identifier}'], tuple(inputs['shape'])).copy().tobytes()).hexdigest()
                    for k in ('phi', 'phiTmp', 'phiObs', 'phiObsIn')}
    phi = np.load(inputs['fields']['phi'], allow_pickle=False)
    args.output.mkdir(); rows = []; outputs = {}

    def save(folder, name, array):
        path = folder/(name+'.npy')
        with path.open('xb') as stream:
            np.save(stream, array, allow_pickle=False)
        outputs[str(path.resolve())] = digest(path)
        return str(path.resolve())

    for previous in receipt['rows']:
        if not previous['complete']:
            continue  # Retained singular control is not rerun or silently fixed.
        folder = args.output/previous['label']; folder.mkdir()
        flags, fractions, velocity, pressure, projected = (np.load(previous['arrays'][k], allow_pickle=False)
            for k in ('flags', 'fractions', 'velocity-before', 'pressure', 'velocity-projected'))
        masks = cohorts(flags, fractions, fluid_type, empty_type, outflow_type)
        native, rhs = native_response(flags, phi, fractions, velocity, pressure, True)
        np.testing.assert_array_equal(native, projected)
        plain, _ = native_response(flags, phi, fractions, velocity, pressure, False)
        try:
            model = PressureBoundary(flags, phi, fractions, fluid_type, empty_type, outflow_type)
        except ValueError as exc:
            if 'Uncoupled fluid cell has no pressure response' not in str(exc):
                raise
            # Preserve the actual unsupported baseline; do not remove fluid or
            # fabricate constraints to make its physical projection pass.
            error = str(exc); exc.__traceback__ = None
            checkpoints = dict(before=velocity, native_projected=native, native_without_ghost_fluid=plain)
            rows.append(dict(label=previous['label'], reference_complete=False,
                reference_rejection=error, original_native_projection_bitexact=True,
                flux_cohorts={name: {label: stats(flux_divergence(v, fractions)*2.5, mask)
                                    for label, mask in masks.items()} for name, v in checkpoints.items()},
                arrays={name: save(folder, name, v) for name, v in checkpoints.items()}))
            print('CONSISTENT_PRESSURE_REJECTED_INPUT', previous['label'], error, flush=True)
            continue
        target_rhs = -flux_divergence(velocity, fractions); target_rhs[~model.fluid] = 0
        matrix_residual = target_rhs-model.apply(pressure.astype(float))
        at_old_pressure = model.correct(velocity, pressure.astype(float))
        identity = flux_divergence(at_old_pressure, fractions)+matrix_residual
        identity_error = float(np.max(np.abs(identity[model.fluid])))
        if identity_error > 5e-12:
            raise ValueError('Actual-state gradient/matrix/flux identity failed')
        started = time.perf_counter()
        candidate, new_pressure, solve = model.project(velocity)
        elapsed = time.perf_counter()-started
        cast, candidate_rhs = native_response(flags, phi, fractions, velocity, new_pressure, False, candidate)
        candidate_error = float(np.max(np.abs(candidate_rhs[model.fluid])))
        if candidate_error > 5e-5:
            raise ValueError('Native float32 candidate RHS failed fixed 5e-5 residual allowance')
        preserved_outflow = model.inverse_distance == 0
        np.testing.assert_array_equal(cast[preserved_outflow], velocity[preserved_outflow])
        checkpoints = dict(before=velocity, native_projected=native, native_without_ghost_fluid=plain,
            consistent_at_old_pressure=at_old_pressure, consistent_projected_float64=candidate, consistent_native_float32=cast)
        flow = {name: {label: stats(flux_divergence(v, fractions)*2.5, mask) for label, mask in masks.items()}
                for name, v in checkpoints.items()}
        arrays = {name: save(folder, name, v) for name, v in checkpoints.items()}
        arrays.update(pressure_consistent=save(folder, 'pressure-consistent', new_pressure),
            matrix_residual_at_native_pressure=save(folder, 'matrix-residual-at-native-pressure', matrix_residual),
            native_candidate_rhs=save(folder, 'native-candidate-rhs', candidate_rhs))
        row = dict(label=previous['label'], reference_complete=True, original_native_projection_bitexact=True, boundary_model=model.proof,
            flux_cohorts=flow, residual_at_original_pressure=stats(matrix_residual, model.fluid),
            matrix_gradient_flux_identity_maximum_error=identity_error, projection=solve, reference_seconds=elapsed,
            native_candidate_maximum_rhs=candidate_error, fixed_native_rhs_allowance=5e-5,
            frozen_response_faces_bitexact=True, arrays=arrays,
            maximum_active_velocity_native_before=float(np.max(np.abs(velocity[model.inverse_distance > 0]))),
            maximum_active_velocity_native_after=float(np.max(np.abs(cast[model.inverse_distance > 0]))))
        rows.append(row)
        print('CONSISTENT_PRESSURE_RESULT', row['label'], elapsed, solve['iterations'], candidate_error,
              flow['consistent_native_float32']['all'], flush=True)
    if len(rows) != 2 or any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Expected preserved two complete pressure controls')
    if any(hashlib.sha256(scalar_view(source[f'{k}_s{identifier}'], tuple(inputs['shape'])).copy().tobytes()).hexdigest() != sha
           for k, sha in initial_host.items()):
        raise ValueError('Owned pressure-response probe changed host fields')
    report = dict(complete=True, accepted=False, source_unchanged=True, frame=inputs['frame'],
        blender_build_hash=bpy.app.build_hash.decode(), rows=rows, dependency_sha256=hashes, outputs_sha256=outputs,
        physical_velocity_scale=inputs['cell_m']*2.5, physical_divergence_scale=2.5,
        native_matrix_internal_readback=False, pressure_reference_not_native_cfd=True,
        scope=__doc__, caveat='Only matched uniform-density pressure impulse and native float32 RHS readbacks. Source/mass/contact/cell-volume/refinement/surface/foam/bake/animation/playable acceptance remain unfinished. No prescribed source flux is fitted and no liquid state is changed to pass.')
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
