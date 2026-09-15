"""Original bank-front birth geometry; no water update or solver promotion."""
import argparse
from fractions import Fraction as F
import json
import math
from pathlib import Path
import numpy as np

from audit_south_fork_nonlinear_source_block import load_original_block
from audit_south_fork_subcell_energy_flux import sha
from subcell_source_activation import assembly, faces
from subcell_source_birth_geometry import SourceBirthGeometry, value
from subcell_source_birth_pressure import SourceBirthPressure
from subcell_wet_pool_primal_energy import evaluate
from subcell_source_frames import face_section
from subcell_dry_front_flux import flux as dry_flux


def analyze(partition, assembled):
    """Resolve actual receiving IDs and compare exact independent integrals.

    The supplied nondispersive receipt rate locates candidate source regions;
    it is NOT assumed to be the full-model physical/energy flux at birth.
    """
    if assembled['partition'] is not partition:
        raise ValueError('Original matching source-front assembly required')
    occupied = {(p['parent'], int(s)) for p in partition.pools for s in p['source_triangle_indices']}
    births, records = {}, {}
    comparisons = 0
    for receipt in assembled['new_region_rates']:
        ids, parent = receipt['source_triangle_indices'], receipt['parent']
        if (len(ids) != 1 or (parent, ids[0]) in occupied
                or not math.isfinite(receipt['volume_rate']) or receipt['volume_rate'] <= 0):
            raise ValueError('Explicit unowned original receiving source with positive receipt required')
        key = parent, int(ids[0])
        if key in births:
            raise ValueError('Repeated original receiving source')
        birth = SourceBirthGeometry(partition.patch.cells[parent].subset_sources(ids))
        births[key] = birth
        bound = birth.next_height if birth.next_height is not None else F(1)
        for divisor in (7, 19, 101):
            height = bound/divisor
            expected = tuple(sum(f.depth_moments(birth.datum+height)[k] for f in birth.fragments) for k in range(4))
            if birth.moments(height) != expected:
                raise ValueError('Birth polynomial disagrees with independent original clipping')
            comparisons += 4
        records[key] = dict(parent=parent, **birth.record(),
            nondispersive_receipt_volume_rate=receipt['volume_rate'], incoming_faces=[])
    received = {key: [] for key in births}
    for face in faces(partition):
        li, ri = face['left'], face['right']
        if min(face['left_parent'], face['right_parent']) < 0 or (li is None) == (ri is None):
            continue
        parent = face['left_parent'] if li is None else face['right_parent']
        source = face['left_source'] if li is None else face['right_source']
        key = parent, int(source)
        if key not in births:
            continue
        owner, normal = (ri, -face['normal']) if li is None else (li, face['normal'])
        pool = partition.pools[owner]
        form, section = pool['form'], face_section(face['segment'])
        flux, _ = dry_flux(section, form['stage_offset'], form['datum'], pool['momentum']/pool['volume'],
                           normal, assembled['gravity'], assembled['reference_datum_m'])
        if flux[0] == 0:
            continue
        received[key].append(float(flux[0]))
        birth = births[key]
        polynomial = birth.face_area_polynomial(section)
        bound = birth.face_next_height(section)
        bound = F(1) if bound is None else bound
        # Exact endpoint integration independent of the storage triangulation.
        for divisor in (7, 19, 101):
            height = bound/divisor
            expected = F(0)
            for first, second in section.source_segments:
                a, b = sorted((first[1]-birth.datum, second[1]-birth.datum))
                width = second[0]-first[0]
                if height <= a:
                    continue
                if height >= b:
                    expected += width*(height-(a+b)/2)
                else:
                    expected += width*(height-a)**2/(2*(b-a))
            if value(polynomial, height) != expected:
                raise ValueError('Birth face polynomial disagrees with exact source endpoints')
            comparisons += 1
        contact = birth.face_contact(section)
        records[key]['incoming_faces'].append(dict(wet_pool=owner, internal=face['internal'],
            wet_source_face=face['right_source'] if li is None else face['left_source'],
            normal=normal, original_source_segments=section.source_segments,
            nondispersive_volume_flux=float(flux[0]),
            newborn_area_polynomial={str(k): str(v) for k, v in polynomial.items()},
            next_positive_face_height=birth.face_next_height(section),
            scaled_newborn_area_over_volume_limit=birth.scaled_face_divergence_limit(section), **contact))
    receipt_error = 0.
    for key, record in records.items():
        if not record['incoming_faces']:
            raise ValueError('Receiving source has no resolved original incoming face')
        receipt_error = max(receipt_error, abs(math.fsum(received[key])-record['nondispersive_receipt_volume_rate']))
    if receipt_error > 1e-12:
        raise ValueError('Reassembled exact source-face receipts disagree')
    all_faces = [face for record in records.values() for face in record['incoming_faces']]
    return dict(receiving_regions=list(records.values()), receiving_region_count=len(records),
        storage_birth_power_counts={str(p): sum(b.volume_power == p for b in births.values()) for p in (1, 2, 3)},
        incoming_face_count=len(all_faces), delayed_contact_incoming_faces=sum(not f['contact_starts_at_birth'] for f in all_faces),
        regions_with_no_immediate_incoming_contact=sum(not any(f['contact_starts_at_birth'] for f in r['incoming_faces']) for r in records.values()),
        exact_rational_integral_comparisons=comparisons, receipt_reassembly_error=receipt_error,
        full_metric_flux_or_evolution_or_gameplay_accepted=False)


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
    pools, source, indices, origin, authority, sampler, hashes = load_original_block(args)
    before = [(p['volume'], p['momentum'].copy()) for p in pools.pools]
    assembled = assembly(pools, face_scheme='donor')
    result = analyze(pools, assembled)
    pressure = SourceBirthPressure(pools)
    for record in result['receiving_regions']:
        record['original_cell'] = indices[record['parent']]
        record['vertex_authority_codes'] = sorted(set(map(int,
            authority[sampler.faces[list(record['source_triangle_indices'])]].ravel())))
        record['point_pressure_limit'] = pressure.point_limit(record['parent'], record['source_triangle_indices'][0])
    # Test the most strongly coupled original receiving source, chosen from
    # the analytic coefficients before seeing any finite-volume result.
    strongest = min(result['receiving_regions'],
        key=lambda r: r['point_pressure_limit']['fixed_old_state_energy_height_slope']) if result['receiving_regions'] else None
    if strongest is not None:
        parent, source_id = strongest['parent'], strongest['source_triangle_indices'][0]
        birth = SourceBirthGeometry(pools.patch.cells[parent].subset_sources([source_id]))
        heights = [birth.next_height]
        for face in strongest['incoming_faces']:
            if face['next_positive_face_height'] is not None:
                heights.append(face['next_positive_face_height'])
        bound = min(h for h in heights if h is not None)
        expected = strongest['point_pressure_limit']['fixed_old_state_energy_height_slope']
        rows = []
        for divisor in (100, 200, 400, 800, 1600, 3200, 6400):
            height = bound/divisor
            volume = float(birth.moments(height)[1])
            candidate = pools.with_regions(list(pools.pools)+[dict(parent=parent,
                source_triangle_indices=[source_id], volume=volume, momentum=np.zeros(2))])
            energy = evaluate(candidate, np.array([p['momentum'] for p in candidate.pools])[:, None, :])
            observed = (energy['kinetic']-pressure.primal['kinetic'])/float(height)
            rows.append(dict(height=height, added_volume=volume, observed_energy_height_slope=observed,
                error=abs(observed-expected), maximum_pressure_residual=max(p['relative_residual'] for p in energy['poles']),
                positive_energy_contraction_error=energy['positive_energy_contraction_error']))
        result['single_source_pressure_probe'] = dict(parent=parent, source_id=source_id,
            analytic_energy_height_slope=expected, rows=rows,
            pressure_limit_probe_controls_passed=bool(expected < 0 and rows[-1]['error'] < rows[0]['error']/3
                and rows[-1]['error'] < .01*abs(expected)
                and all(r['maximum_pressure_residual'] <= 2e-5 and r['positive_energy_contraction_error'] <= 1e-10 for r in rows)),
            scope='Independent positive-water pressure energies at fixed old V/P; added water is a geometry probe, NOT a conservative time step.')
    if any(p['volume'] != v or not np.array_equal(p['momentum'], m) for p, (v, m) in zip(pools.pools, before)):
        raise ValueError('Geometry analysis changed the original water')
    if any(sha(Path(path)) != digest for path, digest in hashes.items()):
        raise ValueError('Source or implementation changed during original bank birth analysis')
    report = dict(schema='raftsim.south_fork.source_birth_geometry.v1', accepted=False,
        original_block_col_row=[args.block_col, args.block_row], origin_registered_m=origin,
        original_snapshot_time_seconds=source['source_time_seconds'], original_pools=len(pools.pools),
        original_water_unchanged=True, result=result, source_sha256=hashes,
        boundary_note='Original block with reflecting exterior cuts; not the natural open river.',
        authority_note='1 captured DEM; 3 exposed rock; 2 submerged prior, 4 interpolation, 5 inferred flank. Exact rational arithmetic adds no measurement precision.',
        full_source_model_or_native_or_gameplay_accepted=False)
    def converter(v):
        if isinstance(v, F):
            return str(v)
        if isinstance(v, np.ndarray):
            return v.tolist()
        if isinstance(v, np.integer):
            return int(v)
        raise TypeError(type(v).__name__)
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False, default=converter)
    print(json.dumps({k: v for k, v in result.items() if k != 'receiving_regions'}, default=converter), flush=True)
    return 0 if result.get('single_source_pressure_probe', {}).get('pressure_limit_probe_controls_passed', False) else 1


if __name__ == '__main__':
    raise SystemExit(main())
