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
from subcell_simultaneous_birth_pressure import point_limits, birth_faces, BirthLimitSystem
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


def analyze(partition, receipts):
    before = [(p['volume'], p['momentum'].copy()) for p in partition.pools]
    keys, rates = [], []
    for receipt in receipts:
        if len(receipt['source_triangle_indices']) != 1:
            raise ValueError('Single original source receipt required')
        keys.append((receipt['parent'], int(receipt['source_triangle_indices'][0])))
        rates.append(receipt['volume_rate'])
    if not rates or not np.isfinite(rates).all() or min(rates) <= 0:
        raise ValueError('Positive original receipt rates required')
    births = [SourceBirthGeometry(partition.patch.cells[p].subset_sources([s])) for p, s in keys]
    context = SourceBirthPressure(partition)
    paths = []
    for name, scales in [('uniform_stage', np.ones(len(keys))),
                         ('nondispersive_receipt_direction', np.cbrt(np.asarray(rates)/np.array([float(b.volume_coefficient) for b in births])))]:
        requests = [(p, s, k) for (p, s), k in zip(keys, scales)]
        limit = point_limits(context, requests)
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
            rows.append(dict(path_parameter=parameter, added_volumes=added, observed_energy_path_slope=observed,
                error=abs(observed-expected), maximum_pressure_residual=max(p['relative_residual'] for p in metric['poles']),
                positive_energy_contraction_error=metric['positive_energy_contraction_error'],
                original_newborn_operator=operator_probe(partition, candidate, limit)))
        operator_passed = (rows[-1]['original_newborn_operator']['maximum_column_scaled_error'] < 1e-4
            and rows[-1]['original_newborn_operator']['maximum_column_scaled_error']
            < rows[0]['original_newborn_operator']['maximum_column_scaled_error']/3)
        passed = bool(expected < 0 and rows[-1]['error'] < rows[0]['error']/3 and rows[-1]['error'] < .01*abs(expected)
            and all(r['maximum_pressure_residual'] <= 2e-5 and r['positive_energy_contraction_error'] <= 1e-10 for r in rows)
            and operator_passed)
        paths.append(dict(name=name, limit=limit, rows=rows, original_newborn_operator_controls_passed=operator_passed,
                          pressure_limit_probe_controls_passed=passed))
    if any(p['volume'] != v or not np.array_equal(p['momentum'], m) for p, (v, m) in zip(partition.pools, before)):
        raise ValueError('Birth analysis altered original physical water')
    return dict(receiving_region_count=len(keys), paths=paths, original_water_unchanged=True,
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
    receipts = assembly(partition, face_scheme='donor')['new_region_rates']
    result = analyze(partition, receipts)
    provenance = [dict(parent=r['parent'], original_cell=indices[r['parent']], source_ids=r['source_triangle_indices'],
        vertex_authority_codes=sorted(set(map(int, authority[sampler.faces[r['source_triangle_indices']]].ravel())))) for r in receipts]
    if any(sha(Path(path)) != digest for path, digest in hashes.items()):
        raise ValueError('Original source or implementation changed during simultaneous-birth audit')
    report = dict(schema='raftsim.south_fork.simultaneous_source_birth.v1', accepted=False,
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
        controls_passed=p['pressure_limit_probe_controls_passed']) for p in result['paths']])), flush=True)
    return 0 if result['pressure_limit_probe_controls_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
