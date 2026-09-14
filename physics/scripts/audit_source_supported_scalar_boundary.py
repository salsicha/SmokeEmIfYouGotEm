"""Actual captured boundary forcing comparison, not an evolving-solver pass."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from audit_pressure_stencil_source import decode, audit
from audit_live_temporal_evolution import observations, boundary_provider
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate, kinematic_forcing
from directional_pressure_geometry import DirectionalPressureGeometry
from difference_scalar_gradient_reference import difference_scalar_gradients
from source_supported_scalar_boundary import SourceSupportedScalarBoundary
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def compare(raw, endpoint, trace, full_source_rate):
    full, full_bed, metadata = decode(raw)
    state, bed, dx = endpoint['state'][..., :3], endpoint['bed'], endpoint['cell_meters']
    with exact_endpoint_cuts():
        fv, cfl = bank.rate(state, bed, dx, second_order=True, shoreline_limiter='unscaled',
            exterior=(endpoint['exterior_state'], endpoint['exterior_bed']))
    g = ReconstructedPressureGeometry(state[..., 0], bed, dx,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom',
        exterior_bed=endpoint['exterior_bed'])
    full_rate = full_source_rate.copy(); full_rate[3:-3, 3:-3] = fv
    activating = (g.h == 0)&(fv[..., 0] > 0)
    # Actual FV entering momentum/mass ray, never source-reset interior rates.
    if np.any(activating):
        g = DirectionalPressureGeometry(g, fv[..., 0]); tangent = g.tangent
    else:
        tangent = PressureGeometryRate(g, bed, fv[..., 0])
    boundary = SourceSupportedScalarBoundary(g, state, full[..., :3], full_bed, full_rate=full_rate)
    u = boundary.velocity[boundary.core]
    with difference_scalar_gradients():
        old = kinematic_forcing(g, tangent, u, boundary_velocity=trace)
    new = boundary.forcing(tangent, trace)
    differences = []
    for name, a, b in zip(('quadratic', 'curvature', 'advective'), old, new):
        delta = b-a
        # Reconstructed scalar coefficients touch two boundary cells. Applying
        # unchanged D/E to that advective field adds one more neighbor layer.
        radius = 2 if name == 'advective' else 3
        interior_exact = np.array_equal(a[radius:-radius, radius:-radius], b[radius:-radius, radius:-radius])
        if not interior_exact:
            raise AssertionError('Boundary change escaped its derived stencil support: '+name)
        differences.append(dict(field=name, maximum_change=float(abs(delta).max()),
            changed_entries=int(np.count_nonzero(delta)), boundary_support_cells=radius,
            beyond_boundary_support_exact=interior_exact))
    # Scalar work identity on a restricted extended domain: external scalar
    # work, changed scalar geometry, and constant-null correction are distinct.
    f = g.h+g.bed
    full_f = full[..., 0]+full_bed
    full_u = np.zeros_like(boundary.velocity); full_u[boundary.core] = u
    ext_d, _ = boundary.extended.kinematic_components(full_u)
    original_d, _ = g.kinematic_components(u)
    sigma = boundary.extended.scalar_gradient(np.ones(full.shape[:2]))[boundary.core]
    actual_work = float(np.sum(u*boundary.gradient(f, full_f))+np.sum(f*original_d))
    mask = np.ones(full.shape[:2], dtype=bool); mask[boundary.core] = False
    exterior_work = float(-np.sum(full_f[mask]*ext_d[mask]))
    geometry_work = float(-np.sum(f*(ext_d[boundary.core]-original_d)))
    constant_work = float(-np.sum(f*np.sum(u*sigma, axis=-1)))
    predicted = exterior_work+geometry_work+constant_work
    error = abs(actual_work-predicted)
    tolerance = 1e-10*max(1., abs(actual_work), abs(predicted))
    if error > tolerance:
        raise AssertionError('Restricted scalar work identity does not close')
    return dict(source=metadata, original_fv_rate_sha256=hashlib.sha256(fv.tobytes()).hexdigest(),
        cfl_s=cfl, activating_dry_cells=int(np.sum((g.h == 0)&(fv[..., 0] > 0))),
        forcing_changes=differences, scalar_work=dict(actual=actual_work, exterior=exterior_work,
            changed_scalar_geometry=geometry_work, constant_null_correction=constant_work,
            predicted=predicted, identity_error=error),
        mechanical_energy_qualified=False, wetting_front_qualified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    raw = args.input.read_bytes(); record = json.loads(raw)
    source_audit = audit(record)
    a, b = observations(record); duration, at_time = boundary_provider(a, b)
    first_full, _, _ = decode(record['first']); second_full, _, _ = decode(record['second'])
    full_source_rate = (second_full[..., :3]-first_full[..., :3])/duration
    cases = []
    for name, endpoint, elapsed in (('first', a, 0.), ('second', b, duration)):
        result = compare(record[name], endpoint, at_time(elapsed, 0)[2], full_source_rate)
        cases.append(result)
        print(json.dumps(dict(event='source_supported_forcing_compared', **result)), flush=True)
    result = dict(input=str(args.input.resolve()), input_sha256=hashlib.sha256(raw).hexdigest(),
        source_audit_passed=source_audit['passed'], endpoint_cases=cases,
        implementation_hashes={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('source_supported_scalar_boundary.py', 'audit_source_supported_scalar_boundary.py',
                         'reconstructed_pressure_geometry.py', 'reconstructed_pressure_rates.py',
                         'difference_scalar_gradient_reference.py', 'total_depth_bank_replay.py')},
        captured_forcing_evaluated=True, evolved_interval_completed=False,
        pressure_boundary_qualified=False, native_or_gameplay_accepted=False,
        limitations='Two actual source endpoints, not evolving states. Scalar boundary support is supplied; '
        'original interior pressure D/E and independent affine face traces remain unchanged. '
        'The scalar work decomposition is not a closed mechanical-energy balance or outgoing-wave condition. '
        'Dry-front limits, nonlinear histories, native performance and visuals remain open.')
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
