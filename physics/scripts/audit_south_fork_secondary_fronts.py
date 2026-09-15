"""Original point-source secondary receipts; no coupled rational time update."""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import numpy as np

from audit_south_fork_nonlinear_source_block import load_original_block
from audit_south_fork_subcell_energy_flux import sha
from subcell_source_activation import assembly
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_curvature import original_gradient
from subcell_simultaneous_birth_pressure import birth_faces
from subcell_source_frames import face_section
from subcell_point_birth_front_flux import point_front_flux
from subcell_dry_front_flux import flux as original_flux


def analyze(part, receipts):
    before = [(p['volume'], p['momentum'].copy()) for p in part.pools]
    keys, velocity, scale = [], [], []
    for receipt in receipts:
        if (len(receipt['source_triangle_indices']) != 1 or not np.isfinite(receipt['volume_rate'])
                or receipt['volume_rate'] <= 0 or np.shape(receipt['momentum_rate']) != (2,)
                or not np.isfinite(receipt['momentum_rate']).all()):
            raise ValueError('Positive original single-source mass and finite momentum receipt required')
        key = (receipt['parent'], int(receipt['source_triangle_indices'][0]))
        birth = SourceBirthGeometry(part.patch.cells[key[0]].subset_sources([key[1]]))
        if birth.volume_power != 3:
            raise ValueError('Primary point-source receipt required')
        keys.append(key)
        velocity.append(np.asarray(receipt['momentum_rate'])/receipt['volume_rate'])
        scale.append(float(np.cbrt(receipt['volume_rate']/float(birth.volume_coefficient))))
    occupied = {(p['parent'], int(s)) for p in part.pools for s in p['source_triangle_indices']}
    if not keys or len(set(keys)) != len(keys) or any(key in occupied for key in keys):
        raise ValueError('Distinct original unowned primary sources required')
    if not np.isfinite(velocity).all() or not np.isfinite(scale).all() or min(scale) <= 0:
        raise ValueError('Original secondary receipt coefficients exceed represented range')
    lookup = {key: i for i, key in enumerate(keys)}
    records, transfers, delayed = [], [], 0
    for face in birth_faces(part, keys):
        if min(face['left_parent'], face['right_parent']) < 0:
            continue
        li = lookup.get((face['left_parent'], face['left_source']))
        ri = lookup.get((face['right_parent'], face['right_source']))
        if li is not None and face['right'] is None:
            index, normal = li, face['normal']
            target = (face['right_parent'], face['right_source'])
        elif ri is not None and face['left'] is None:
            index, normal = ri, -face['normal']
            target = (face['left_parent'], face['left_source'])
        else:
            continue
        key = keys[index]
        birth = SourceBirthGeometry(part.patch.cells[key[0]].subset_sources([key[1]]))
        section = face_section(face['segment'])
        if not birth.face_contact(section)['contact_starts_at_birth']:
            delayed += 1
            continue
        bound = birth.face_next_height(section)
        if bound is None or bound <= 0:
            raise ValueError('Original positive face knot required')
        rows = []
        for divisor in (100, 200, 400, 800, 1600, 3200, 6400):
            height = float(bound/divisor)
            predicted = point_front_flux(birth, section, height, velocity[index], normal)
            observed, info = original_flux(section, height, birth.datum, velocity[index], normal)
            errors = []
            for actual, expected in ((predicted['flux'], observed),
                    (predicted['energy_flux'], info['energy_flux']),
                    (predicted['nonadvective_momentum_flux'], info['nonadvective_momentum_flux'])):
                error = float(np.max(abs(np.asarray(actual)-expected)))
                magnitude = float(np.max(abs(np.asarray(expected))))
                errors.append(error/magnitude if magnitude else error)
            rows.append(dict(height=height, flux=predicted['flux'],
                original_flux=observed, energy_flux=predicted['energy_flux'],
                nonadvective_momentum_flux=predicted['nonadvective_momentum_flux'],
                finite_branch_widths=predicted['branch_projected_widths'],
                maximum_relative_or_zero_absolute_error=max(errors)))
        receiver = SourceBirthGeometry(part.patch.cells[target[0]].subset_sources([target[1]]))
        contact = receiver.face_contact(section)
        jump = (original_gradient(part, face['left_parent'], face['left_source'])
                != original_gradient(part, face['right_parent'], face['right_source']))
        power = predicted['mass_height_power']
        term = None
        if power is not None:
            time_power = 1+F(power)/3
            coefficient = predicted['mass_height_coefficient']*scale[index]**power/float(time_power)
            if not np.isfinite(coefficient) or coefficient <= 0:
                raise ValueError('Positive secondary mass term exceeds represented range')
            # A conditional integrated leading receipt, NOT an actual step.
            # The donor loss and target gain have exactly matching coefficients.
            term = dict(donor=list(key), receiver=list(target), volume_time_power=time_power,
                donor_volume_coefficient=-coefficient, receiver_volume_coefficient=coefficient,
                receiver_height_time_power=(time_power/receiver.volume_power
                    if contact['contact_starts_at_birth'] else None),
                receiver_placement=('minimum-connected' if contact['contact_starts_at_birth']
                                    else 'incoming-face-above-source-minimum'),
                receiver_connected_pool_update_accepted=False,
                valid_only_below_primary_height=predicted['asymptotic_branch_height_bound'])
            transfers.append(term)
        records.append(dict(donor=list(key), receiver=list(target), donor_pool_index=len(part.pools)+index,
            internal=face['internal'], curvature_jump=jump, normal=normal,
            newborn_physical_velocity=velocity[index], primary_stage_time_coefficient=scale[index],
            normal_velocity=predicted['normal_velocity'], asymptotic_branch=predicted['asymptotic_branch'],
            asymptotic_branch_height_bound=predicted['asymptotic_branch_height_bound'],
            receiver_storage_power=receiver.volume_power, receiver_birth_datum=str(receiver.datum),
            receiving_face_contact=contact, secondary_volume_term=term, rows=rows))
    if any(p['volume'] != v or not np.array_equal(p['momentum'], m) for p, (v, m) in zip(part.pools, before)):
        raise ValueError('Secondary-front analysis altered original physical water')
    ledger_error = max((abs(t['donor_volume_coefficient']+t['receiver_volume_coefficient']) for t in transfers), default=0.)
    max_error = max((r['maximum_relative_or_zero_absolute_error'] for e in records for r in e['rows']), default=0.)
    return dict(primary_source_count=len(keys), immediate_newborn_unowned_faces=len(records),
        delayed_newborn_unowned_faces=delayed, faces=records, conservative_secondary_mass_terms=transfers,
        mass_coefficient_ledger_error=ledger_error, original_water_unchanged=True,
        original_flux_integration_controls_passed=bool(records and max_error < 1e-10 and ledger_error <= 1e-10),
        maximum_original_flux_error=max_error,
        full_rational_front_or_force_or_time_or_native_or_gameplay_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source-report', 'atlas', 'report'):
        parser.add_argument('--'+name, required=True, type=Path)
    parser.add_argument('--block-col', type=int, default=12)
    parser.add_argument('--block-row', type=int, default=8)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    part, source, indices, origin, authority, sampler, hashes = load_original_block(args)
    receipts = assembly(part, face_scheme='donor')['new_region_rates']
    result = analyze(part, receipts)
    provenance = [dict(parent=p, original_cell=indices[p], source_id=s,
        authority_codes=sorted(set(map(int, authority[sampler.faces[s]].ravel()))))
        for p, s in sorted({tuple(f['receiver']) for f in result['faces']})]
    if any(sha(Path(path)) != digest for path, digest in hashes.items()):
        raise ValueError('Source or implementation changed during secondary-front audit')
    report = dict(schema='raftsim.south_fork.secondary_source_front.v1', accepted=False,
        source_sha256=hashes, original_block_col_row=[args.block_col, args.block_row],
        source_time_seconds=source['source_time_seconds'], origin_registered_m=origin,
        receiver_provenance=provenance, result=result,
        scope='Original nondispersive receipt velocities and conditional primary height k*t^(1/3). Integrated coefficients are not a coupled rational time step.',
        authority_note='1 captured DEM; 3 exposed rock; 2 submerged prior, 4 interpolation, 5 inferred flank. Exact arithmetic adds no measured precision.',
        boundary_note='Reflecting original block cuts, not the natural open river.')
    def convert(value):
        if isinstance(value, F): return str(value)
        if isinstance(value, np.ndarray): return value.tolist()
        if isinstance(value, np.integer): return int(value)
        raise TypeError(type(value).__name__)
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False, default=convert)
    curvature = [f for f in result['faces'] if f['curvature_jump']]
    print(json.dumps(dict(immediate_faces=result['immediate_newborn_unowned_faces'],
        curvature_faces=len(curvature), curvature_branches={b:sum(f['asymptotic_branch']==b for f in curvature)
            for b in ('outward-wet','zero-normal-fan','receding-dry')},
        secondary_terms=len(result['conservative_secondary_mass_terms']),
        maximum_flux_error=result['maximum_original_flux_error'],
        mass_ledger_error=result['mass_coefficient_ledger_error'],
        controls_passed=result['original_flux_integration_controls_passed'])), flush=True)
    return 0 if result['original_flux_integration_controls_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
