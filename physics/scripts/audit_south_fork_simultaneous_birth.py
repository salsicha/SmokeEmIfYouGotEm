"""Source-locked simultaneous pressure-birth probe, NOT conservative evolution."""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import numpy as np

from audit_south_fork_nonlinear_source_block import load_original_block
from audit_south_fork_subcell_energy_flux import sha
from subcell_source_activation import assembly
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_birth_pressure import SourceBirthPressure
from subcell_source_birth_work import point_work
from subcell_point_birth_metric_force import point_metric_force
from subcell_primal_metric_rate import metric_time_force
from subcell_point_birth_connection import point_connection
from subcell_auxiliary_transport import geometric_commutator
from subcell_wet_pool_pressure_rate import WetPoolPressureRate
from subcell_point_birth_curvature import point_curvature_limit
from subcell_source_curvature import SourceCurvatureTensor
from subcell_simultaneous_birth_pressure import birth_faces, BirthLimitSystem
from subcell_source_frames import face_section
from subcell_wet_pool_primal_energy import evaluate
from subcell_wet_pool_pressure import WetPoolPressureSystem


def operator_probe(partition, candidate, limit):
    """All new columns of original Q; no inverse or accepted physical step.

    Unlike energy alone, this tests connections with zero original stress.
    Per-column scaling prevents a large steep-source column from concealing
    other original directions. Unit absolute scale also checks zero columns.
    """
    count = len(limit['source_keys'])
    old = len(partition.pools)
    system = WetPoolPressureSystem(candidate, limit['poles'][0]['beta'])
    predicted = BirthLimitSystem(limit['newborn_jet_maps'], limit['newborn_scaled_factors'],
                                limit['volume_path_coefficients'], limit['poles'][0]['beta'])
    errors = []
    for column in range(2*count):
        basis = np.zeros((old+count, 1, 2))
        basis[old+column//2, 0, column%2] = 1.
        actual = system.factor_transpose(system.factor_action(basis))[old:]
        expected = predicted.q_action(basis[old:])
        errors.append(float(np.max(abs(actual-expected)))/max(1., float(np.max(abs(expected)))))
    return dict(columns_checked=2*count, column_scaled_errors=errors, maximum_column_scaled_error=max(errors))


def metric_force_probe(partition, candidate, parameter, expected):
    """Independent original positive-water derivative, not a force update."""
    old = len(partition.pools)
    volume = np.array([p['volume'] for p in candidate.pools])
    velocity = np.array([p['momentum'] for p in candidate.pools])[:, None]/volume[:, None, None]
    vd = np.zeros((len(volume), 1))
    vd[old:, 0] = 3*volume[old:]/float(parameter)
    rate = metric_time_force(candidate, velocity, vd)
    actual = (rate['force'][:old, 0], rate['force'][old:, 0]/float(parameter))
    targets = (expected['old_force_limit'], expected['newborn_force_over_path_limit'])
    errors = []
    for value, target in zip(actual, targets):
        scale = float(np.max(abs(target)))
        if scale == 0:
            raise ValueError('Actual bank metric force probe requires nonzero vector coefficients')
        errors.append(float(np.max(abs(value-target)))/scale)
    return dict(old_force=actual[0], newborn_force_over_path=actual[1],
                old_force_max_norm_relative_error=errors[0],
                newborn_force_max_norm_relative_error=errors[1],
                metric_work=rate['metric_energy_work'],
                energy_coordinate_error=rate['direction']['energy_coordinate_error'],
                canonical_metric_local_error=rate['direction']['canonical_metric_local_error'],
                maximum_pressure_residual=max(max(p['solve_residual'], p['direction_solve']['relative_residual'])
                                               for p in rate['direction']['poles']))


def connection_probe(partition, candidate, parameter, expected):
    """Independent finite original J and T.T*J, retaining cancellation scales."""
    old = len(partition.pools)
    volume = np.array([p['volume'] for p in candidate.pools])
    momentum = np.array([p['momentum'] for p in candidate.pools])[:, None]
    root = np.sqrt(volume)[:, None, None]
    vd = np.zeros((len(volume), 1))
    vd[old:, 0] = 3*volume[old:]/float(parameter)
    primal = evaluate(candidate, momentum)
    metric = metric_time_force(candidate, momentum/volume[:, None, None], vd)
    total = .5*metric['auxiliary_force'][:, 0]
    records, errors = [], []
    scale_old = .5*float(np.max(abs(expected['metric']['old_force_limit'])))
    scale_new = .5*float(np.max(abs(expected['metric']['newborn_force_over_path_limit'])))
    for pole, target in zip(primal['poles'], expected['poles']):
        system = WetPoolPressureSystem(candidate, pole['beta'])
        w = pole['normalized_auxiliary_velocity']/root
        j = geometric_commutator(WetPoolPressureRate(system, vd), w)
        solution, stats = system.solve(j/root)
        if stats['relative_residual'] > 2e-5:
            raise ValueError('Original connection probe pullback residual gate failed')
        pulled = root*solution
        total += pole['alpha']*pulled[:, 0]
        scales = []
        record = dict(old_commutator=j[:old, 0], newborn_commutator_over_path=j[old:, 0]/float(parameter),
                      old_pulled_commutator=pulled[:old, 0],
                      newborn_pulled_commutator_over_path=pulled[old:, 0]/float(parameter),
                      pullback_residual=stats['relative_residual'], skew_work=float(np.sum(w*j)))
        if abs(record['skew_work']) > 1e-10:
            raise ValueError('Original connection probe skew-work gate failed')
        for block, suffix in [('old', ''), ('newborn', '_over_path')]:
            # A pulled or summed vector can have a zero leading coefficient.
            # Normalize by its uncancelled original terms, never by roundoff
            # in that zero and never claim componentwise relative accuracy.
            keys = [block+'_'+name+suffix for name in ('commutator', 'pulled_commutator')]
            scale = max(float(np.max(abs(target[key+'_limit']))) for key in keys)
            if scale == 0:
                raise ValueError('Original bank connection probe needs nonzero uncancelled terms')
            scales.append(scale)
            for key in keys:
                errors.append(float(np.max(abs(record[key]-target[key+'_limit'])))/scale)
        scale_old += pole['alpha']*scales[0]
        scale_new += pole['alpha']*scales[1]
        records.append(record)
    old_error = float(np.max(abs(total[:old]-expected['old_connection_limit'])))/scale_old
    new_error = float(np.max(abs(total[old:]/float(parameter)-expected['newborn_connection_over_path_limit'])))/scale_new
    errors.extend((old_error, new_error))
    return dict(poles=records, old_connection=total[:old], newborn_connection_over_path=total[old:]/float(parameter),
                old_uncancelled_scale=scale_old, newborn_uncancelled_scale=scale_new,
                old_connection_scaled_error=old_error, newborn_connection_scaled_error=new_error,
                maximum_term_scaled_error=max(errors))


def curvature_probe(partition, candidate, parameter, expected):
    """Guarded common-trace expression, not a qualified front equation."""
    momentum = np.array([p['momentum'] for p in candidate.pools])[:, None]
    volume = np.array([p['volume'] for p in candidate.pools])[:, None, None]
    root = np.sqrt(volume)
    u = momentum/volume
    primal = evaluate(candidate, momentum)
    force, residuals = np.zeros_like(momentum), []
    for pole in primal['poles']:
        system = WetPoolPressureSystem(candidate, pole['beta'])
        curvature = SourceCurvatureTensor(system)
        w = pole['normalized_auxiliary_velocity']/root
        solution, stats = system.solve(curvature.action(w, u)/root)
        residuals.extend((pole['relative_residual'], stats['relative_residual']))
        force += pole['alpha']*(root*solution-curvature.action(w, w))
    if max(residuals) > 2e-5 or not np.isfinite(force).all():
        raise ValueError('Original finite common-trace curvature solve/range gate failed')
    target = np.vstack((expected['old_force_path_squared_limit'], expected['newborn_force_path_squared_limit']))
    actual = float(parameter)**2*force[:, 0]
    scale = float(np.max(abs(target)))
    error = float(np.max(abs(actual-target)))
    return dict(force_path_squared=actual, maximum_absolute_coefficient_error=error,
                analytic_coefficient_scale=scale,
                maximum_relative_coefficient_error=error/scale if scale else None,
                maximum_solve_residual=max(residuals), unscaled_skew_work=float(np.sum(u*force)),
                unresolved_curvature_fronts=curvature.unresolved,
                common_trace_front_or_full_model_accepted=False)


def analyze(partition, receipts, assembled=None):
    before = [(p['volume'], p['momentum'].copy()) for p in partition.pools]
    keys, rates = [], []
    for receipt in receipts:
        if len(receipt['source_triangle_indices']) != 1:
            raise ValueError('Single original source receipt required')
        keys.append((receipt['parent'], int(receipt['source_triangle_indices'][0])))
        rates.append(receipt['volume_rate'])
    if not rates or not np.isfinite(rates).all() or min(rates) <= 0:
        raise ValueError('Positive original receipt rates required')
    bounded_direction = None
    if assembled is not None:
        if assembled['partition'] is not partition or assembled['new_region_rates'] is not receipts:
            raise ValueError('Matching original assembled receipt direction required')
        vd = np.r_[assembled['volume_rate'], rates]
        pd = np.vstack((assembled['momentum_rate'], [r['momentum_rate'] for r in receipts]))
        if not np.isfinite(vd).all() or not np.isfinite(pd).all():
            raise ValueError('Finite original bounded physical rates required')
        mass_error = abs(float(vd.sum()))
        momentum_error = float(np.max(abs(pd.sum(axis=0)-assembled['bed_force'].sum(axis=0)-assembled['wall_force'])))
        if max(mass_error, momentum_error) > 1e-10:
            raise ValueError('Original base mass/boundary-momentum ledger failed')
        bounded_direction = dict(volume_rate=vd, physical_momentum_rate=pd, mass_rate_error=mass_error,
                                 boundary_bed_momentum_rate_error=momentum_error)
    births = [SourceBirthGeometry(partition.patch.cells[p].subset_sources([s])) for p, s in keys]
    context = SourceBirthPressure(partition)
    paths = []
    for name, scales in [('uniform_stage', np.ones(len(keys))),
                         ('nondispersive_receipt_direction', np.cbrt(np.asarray(rates)/np.array([float(b.volume_coefficient) for b in births])))]:
        requests = [(p, s, k) for (p, s), k in zip(keys, scales)]
        work = point_work(context, requests)
        metric_force = point_metric_force(context, requests)
        connection = point_connection(context, requests)
        curvature = point_curvature_limit(context, requests)
        limit = work['limit']
        bounds = [b.next_height/F(float(k)) for b, k in zip(births, scales) if b.next_height is not None]
        lookup = {key: i for i, key in enumerate(keys)}
        for face in birth_faces(partition, keys):
            for side in ('left', 'right'):
                index = lookup.get((face[side+'_parent'], face[side+'_source']))
                if index is not None:
                    bound = births[index].face_next_height(face_section(face['segment']))
                    if bound is not None:
                        bounds.append(bound/F(float(scales[index])))
        if not bounds:
            raise ValueError('Original positive birth knot required')
        bound = min(bounds)
        expected = limit['fixed_old_state_energy_path_slope']
        rows = []
        for divisor in (100, 200, 400, 800, 1600, 3200, 6400):
            parameter = bound/divisor
            regions, added = list(partition.pools), []
            for (parent, source), birth, scale in zip(keys, births, scales):
                volume = float(birth.moments(parameter*F(float(scale)))[1])
                added.append(volume)
                regions.append(dict(parent=parent, source_triangle_indices=[source], volume=volume, momentum=np.zeros(2)))
            candidate = partition.with_regions(regions)
            metric = evaluate(candidate, np.array([p['momentum'] for p in candidate.pools])[:, None, :])
            observed = (metric['kinetic']-context.primal['kinetic'])/float(parameter)
            old = len(partition.pools)
            scaled_gradient = float(parameter)**2*metric['volume_gradient'][old:]
            scaled_canonical = float(parameter)*metric['canonical_velocity'][old:, 0]
            targets = (work['volume_gradient_path_squared_limit'], work['canonical_velocity_path_limit'])
            work_errors = []
            for actual, target in zip((scaled_gradient, scaled_canonical), targets):
                scale = float(np.max(abs(target)))
                if scale == 0:
                    raise ValueError('Actual bank work probe requires nonzero analytic coefficients')
                work_errors.append(float(np.max(abs(actual-target)))/scale)
            mass_direction_work = float(scaled_gradient@limit['volume_path_coefficients'])
            rows.append(dict(path_parameter=parameter, added_volumes=added, observed_energy_path_slope=observed,
                error=abs(observed-expected), maximum_pressure_residual=max(p['relative_residual'] for p in metric['poles']),
                positive_energy_contraction_error=metric['positive_energy_contraction_error'],
                original_newborn_operator=operator_probe(partition, candidate, limit),
                original_metric_force=metric_force_probe(partition, candidate, parameter, metric_force),
                original_connection=connection_probe(partition, candidate, parameter, connection),
                original_curvature=curvature_probe(partition, candidate, parameter, curvature),
                volume_gradient_path_squared=scaled_gradient, canonical_velocity_path=scaled_canonical,
                volume_gradient_max_norm_relative_error=work_errors[0],
                canonical_velocity_max_norm_relative_error=work_errors[1],
                fixed_old_mass_direction_scaled_work=mass_direction_work,
                mass_direction_scaled_work_error=abs(mass_direction_work-expected/3)))
            if bounded_direction is not None and name == 'nondispersive_receipt_direction':
                # The complete original base direction includes donor losses,
                # receiving momentum, and bed/wall forces. Its independent
                # mass/momentum balance does not remove the singular full work.
                scaled_work = float(parameter)**2*float(metric['volume_gradient']@vd
                    +np.sum(metric['canonical_velocity'][:, 0]*pd))
                rows[-1]['bounded_original_direction_scaled_work'] = scaled_work
                rows[-1]['bounded_original_direction_work_error'] = abs(scaled_work-expected/3)
        operator_passed = (rows[-1]['original_newborn_operator']['maximum_column_scaled_error'] < 1e-4
            and rows[-1]['original_newborn_operator']['maximum_column_scaled_error']
            < rows[0]['original_newborn_operator']['maximum_column_scaled_error']/3)
        work_passed = all(rows[-1][key] < .01 and rows[-1][key] < rows[0][key]/3 for key in (
            'volume_gradient_max_norm_relative_error', 'canonical_velocity_max_norm_relative_error'))
        work_passed &= (rows[-1]['mass_direction_scaled_work_error'] < .01*abs(expected/3)
            and rows[-1]['mass_direction_scaled_work_error'] < rows[0]['mass_direction_scaled_work_error']/3)
        if bounded_direction is not None and name == 'nondispersive_receipt_direction':
            work_passed &= (rows[-1]['bounded_original_direction_work_error'] < .01*abs(expected/3)
                and rows[-1]['bounded_original_direction_work_error'] < rows[0]['bounded_original_direction_work_error']/3)
        force_passed = all(rows[-1]['original_metric_force'][key] < .01
            and rows[-1]['original_metric_force'][key] < rows[0]['original_metric_force'][key]/3
            for key in ('old_force_max_norm_relative_error', 'newborn_force_max_norm_relative_error'))
        force_passed &= all(r['original_metric_force']['maximum_pressure_residual'] <= 2e-5
            and r['original_metric_force']['energy_coordinate_error'] <= 1e-10
            and r['original_metric_force']['canonical_metric_local_error'] <= 1e-10 for r in rows)
        connection_passed = (rows[-1]['original_connection']['maximum_term_scaled_error'] < .01
            and rows[-1]['original_connection']['maximum_term_scaled_error']
            < rows[0]['original_connection']['maximum_term_scaled_error']/3)
        cf, cl = rows[0]['original_curvature'], rows[-1]['original_curvature']
        curvature_passed = (cl['maximum_relative_coefficient_error'] < .01
            if cl['analytic_coefficient_scale'] else cl['maximum_absolute_coefficient_error'] < 1e-10)
        curvature_passed &= (cl['maximum_absolute_coefficient_error'] < cf['maximum_absolute_coefficient_error']/3
            or cl['maximum_absolute_coefficient_error'] == cf['maximum_absolute_coefficient_error'] == 0.)
        passed = bool(expected < 0 and rows[-1]['error'] < rows[0]['error']/3 and rows[-1]['error'] < .01*abs(expected)
            and all(r['maximum_pressure_residual'] <= 2e-5 and r['positive_energy_contraction_error'] <= 1e-10 for r in rows)
            and operator_passed and work_passed and force_passed and connection_passed and curvature_passed)
        paths.append(dict(name=name, limit=limit, rows=rows, original_newborn_operator_controls_passed=operator_passed,
                          analytic_pressure_work={k: v for k, v in work.items() if k != 'limit'},
                          analytic_metric_force={k: v for k, v in metric_force.items() if k != 'limit'},
                          metric_force_probe_controls_passed=bool(force_passed),
                          analytic_connection={k: v for k, v in connection.items() if k != 'metric'},
                          connection_probe_controls_passed=bool(connection_passed),
                          analytic_guarded_curvature={k: v for k, v in curvature.items() if k != 'limit'},
                          guarded_curvature_probe_controls_passed=bool(curvature_passed),
                          pressure_work_probe_controls_passed=bool(work_passed),
                          pressure_limit_probe_controls_passed=passed))
    if any(p['volume'] != v or not np.array_equal(p['momentum'], m) for p, (v, m) in zip(partition.pools, before)):
        raise ValueError('Birth analysis altered original physical water')
    return dict(receiving_region_count=len(keys), paths=paths, original_water_unchanged=True,
                bounded_original_base_direction=bounded_direction,
                pressure_limit_probe_controls_passed=all(p['pressure_limit_probe_controls_passed'] for p in paths),
                full_metric_front_force_or_time_or_gameplay_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report', required=True, type=Path)
    parser.add_argument('--atlas', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--block-col', type=int, choices=range(13), default=12)
    parser.add_argument('--block-row', type=int, choices=range(13), default=8)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    partition, source, indices, origin, authority, sampler, hashes = load_original_block(args)
    assembled = assembly(partition, face_scheme='donor')
    receipts = assembled['new_region_rates']
    result = analyze(partition, receipts, assembled)
    provenance = [dict(parent=r['parent'], original_cell=indices[r['parent']], source_ids=r['source_triangle_indices'],
        vertex_authority_codes=sorted(set(map(int, authority[sampler.faces[r['source_triangle_indices']]].ravel())))) for r in receipts]
    if any(sha(Path(path)) != digest for path, digest in hashes.items()):
        raise ValueError('Original source or implementation changed during simultaneous-birth audit')
    report = dict(schema='raftsim.south_fork.simultaneous_source_birth.v5', accepted=False,
        original_block_col_row=[args.block_col, args.block_row], original_snapshot_time_seconds=source['source_time_seconds'],
        original_pool_count=len(partition.pools), origin_registered_m=origin, provenance=provenance,
        source_sha256=hashes, result=result,
        scope='Fixed old V/P and bounded newborn velocities; added mass is a geometry probe, not conservative evolution. Receipt rates only define one probe direction, not accepted full-model flux.',
        boundary_note='Reflecting exterior block cuts, not the natural open river.',
        authority_note='1 captured DEM; 3 exposed rock; 2 submerged prior, 4 interpolation, 5 inferred flank. Exact arithmetic adds no measurement precision.',
        full_source_model_or_native_or_gameplay_accepted=False)
    def convert(v):
        if isinstance(v, F):
            return str(v)
        if isinstance(v, np.ndarray):
            return v.tolist()
        if isinstance(v, np.integer):
            return int(v)
        raise TypeError(type(v).__name__)
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False, default=convert)
    print(json.dumps(dict(receiving_region_count=result['receiving_region_count'], paths=[dict(
        name=p['name'], new_connections=len(p['limit']['immediate_newborn_connections']),
        slope=p['limit']['fixed_old_state_energy_path_slope'], independent_sum=p['limit']['independent_single_source_sum'],
        first_error=p['rows'][0]['error'], last_error=p['rows'][-1]['error'],
        final_gradient_relative_error=p['rows'][-1]['volume_gradient_max_norm_relative_error'],
        final_canonical_relative_error=p['rows'][-1]['canonical_velocity_max_norm_relative_error'],
        final_old_metric_force_error=p['rows'][-1]['original_metric_force']['old_force_max_norm_relative_error'],
        final_new_metric_force_error=p['rows'][-1]['original_metric_force']['newborn_force_max_norm_relative_error'],
        final_connection_error=p['rows'][-1]['original_connection']['maximum_term_scaled_error'],
        curvature_front_edge_scope=p['analytic_guarded_curvature']['front_edge_scope'],
        final_curvature_absolute_coefficient_error=p['rows'][-1]['original_curvature']['maximum_absolute_coefficient_error'],
        mass_direction_scaled_work=p['rows'][-1]['fixed_old_mass_direction_scaled_work'],
        controls_passed=p['pressure_limit_probe_controls_passed']) for p in result['paths']])), flush=True)
    return 0 if result['pressure_limit_probe_controls_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
