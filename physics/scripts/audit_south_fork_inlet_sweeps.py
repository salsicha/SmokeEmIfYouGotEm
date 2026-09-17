"""Route conditional inlet sweeps over original South Fork source geometry.

Independent streams are NOT combined into physical water. All split-source
moments and out-of-block mass bounds are retained. Fan and rational-force
coupling remain prerequisites, not hidden behind this geometry control.
"""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import math

import numpy as np

from audit_south_fork_nonlinear_source_block import load_original_block
from audit_south_fork_secondary_fronts import analyze
from audit_south_fork_subcell_energy_flux import sha
from subcell_exact_geometry import SourceFragment
from subcell_inlet_sweep_geometry import InletSweep, shared_inlet_edge
from subcell_inlet_contact_time import initial_wet_contact
from subcell_inlet_stream_overlap import simultaneous_pairs, signed_area
from subcell_inlet_face_transport import source_transport_balance
from subcell_inlet_hydrostatic_force import source_hydrostatic_force
from subcell_inlet_lateral_flux import lateral_flux
from subcell_source_activation import assembly


def original_fragments(part):
    """Place exact local polygons in one frame using their ORIGINAL centers."""
    result = {}
    for parent, cell in enumerate(part.patch.cells):
        row, col = divmod(parent, part.patch.shape[1])
        center = tuple(map(F, map(float, part.origin+part.patch.spacing*[col, row])))
        for fragment in cell.fragments:
            polygon = tuple((p[0]+center[0], p[1]+center[1], p[2]) for p in fragment.polygon)
            key = (parent, fragment.source_id)
            if key in result:
                raise ValueError('Duplicate original source fragment ownership')
            result[key] = SourceFragment(fragment.source_id, polygon, fragment.gradient)
    return result


def route(part, fronts, on_face=None):
    fragments = original_fragments(part)
    occupied = {}
    for pool_index, pool in enumerate(part.pools):
        for source_id in pool['source_triangle_indices']:
            key = (pool['parent'], int(source_id))
            if key in occupied:
                raise ValueError('Duplicate original wet-pool source ownership')
            occupied[key] = (pool_index, pool['form'])
    primary = {tuple(f['donor']) for f in fronts['faces']}
    records = []
    for front in fronts['faces']:
        if front['asymptotic_branch'] != 'outward-wet':
            records.append(dict(donor=front['donor'], receiver=front['receiver'],
                status='receding-or-fan-requires-coupled-front-law', physical_update_accepted=False))
            continue
        donor, receiver = tuple(front['donor']), tuple(front['receiver'])
        edge = shared_inlet_edge(fragments[donor], fragments[receiver])
        k = F(front['primary_stage_time_coefficient'])
        u = tuple(map(F, map(float, front['newborn_physical_velocity'])))
        dx, dy = (edge[1][j]-edge[0][j] for j in range(2))
        jacobian = abs(dx*u[1]-dy*u[0])
        branch_bound = jacobian**2/(F(9.81)*(dx*dx+dy*dy))
        # Stay below EVERY already-checked original storage/face knot, and
        # both represented-normal and exact-geometry outward branch bounds.
        height = min(F(front['rows'][0]['height']),
                     front['asymptotic_branch_height_bound'], branch_bound)/100
        sweep = InletSweep(edge, u, k, height/k)
        sweep.validate_receiver(fragments[receiver])
        donor_transport = source_transport_balance(sweep, fragments[donor], birth_donor=True)
        incoming = tuple(sweep.full_moment(p) for p in range(4))
        root_limit = min(F(front['rows'][0]['height']), F(front['asymptotic_branch_height_bound']),
                         branch_bound, sweep.bed_span)/k
        base = dict(donor=list(donor), receiver=list(receiver), original_inlet_xyz=edge,
            constant_inlet_velocity_mps=u, primary_height_scale=k,
            original_isolated_geometry_time_root_limit=root_limit,
            original_isolated_geometry_time_limit=root_limit**3,
            time_root=sweep.time_root, physical_time=sweep.time_root**3,
            primary_height=height, full_incoming_moments=incoming,
            original_donor_transport=donor_transport,
            original_receiver_lateral_flux=lateral_flux(sweep, fragments[receiver]),
            above_receiver_minimum=not front['receiving_face_contact']['contact_starts_at_birth'],
            physical_update_accepted=False)
        if float(incoming[1]) == 0 or float(sweep.time_root**3) == 0:
            records.append(dict(base, status='positive-exact-sweep-below-float-time-or-volume-range'))
            if on_face: on_face(records[-1])
            continue
        # Conservative XY bound from all inlet-fraction and age extrema.
        corners = [tuple(sweep.edge[0][j]+s*sweep.delta[j]+u[j]*age for j in range(2))
                   for s in (F(0), height/sweep.bed_span) for age in (F(0), sweep.time_root**3)]
        bounds = [(min(p[j] for p in corners), max(p[j] for p in corners)) for j in range(2)]
        pieces = []
        for key, fragment in fragments.items():
            if any(max(p[j] for p in fragment.polygon) < lo or min(p[j] for p in fragment.polygon) > hi
                   for j, (lo, hi) in enumerate(bounds)):
                continue
            value = sweep.moments(fragment)
            if value['upper'][1] > 0:
                piece = dict(parent=key[0], source_id=key[1], original_gradient=fragment.gradient,
                    initial_ownership=('wet' if key in occupied else 'primary-birth' if key in primary else 'unowned'),
                    positive_water_proven=value['lower'][1] > 0,
                    moment_lower=value['lower'], moment_upper=value['upper'],
                    bounded_switch_intervals=value['bounded_switch_intervals'],
                    conditional_face_transport=(donor_transport if key == donor else source_transport_balance(sweep, fragment)))
                if key != donor:
                    piece['conditional_hydrostatic_force'] = source_hydrostatic_force(sweep, fragment)
                    piece['conditional_lateral_flux'] = lateral_flux(sweep, fragment)
                if key in occupied:
                    pool_index, form = occupied[key]
                    piece['initial_wet_support'] = dict(pool_index=pool_index,
                        **sweep.initial_wet_support_moments(fragment, form['stage_offset'], form['datum']))
                pieces.append(piece)
        lower = tuple(sum((p['moment_lower'][j] for p in pieces), F(0)) for j in range(4))
        upper = tuple(sum((p['moment_upper'][j] for p in pieces), F(0)) for j in range(4))
        if any(lower[j] > incoming[j] or upper[j]-lower[j] > F(1, 10**10)*incoming[j] for j in range(4)):
            raise ValueError('Original source coverage overlaps or combined integration bound failed')
        outside = tuple((max(F(0), incoming[j]-upper[j]), incoming[j]-lower[j]) for j in range(4))
        target = [p for p in pieces if (p['parent'], p['source_id']) == receiver]
        target_mass = tuple(sum((p[name][1] for p in target), F(0)) for name in ('moment_lower', 'moment_upper'))
        length = math.hypot(float(dx), float(dy))
        geometry_flux_error = abs(float(jacobian)/length-front['normal_velocity'])/abs(front['normal_velocity'])
        if geometry_flux_error > 1e-10:
            raise ValueError('Exact source sweep and original represented normal flux disagree')
        contacts = []
        # A future contact may lie OUTSIDE the current sweep bounding box.
        # Inspect every originally wet source, not just current routed pieces.
        for key, (pool_index, form) in occupied.items():
            contact = initial_wet_contact(sweep, fragments[key], form['stage_offset'], form['datum'])
            if contact['positive_contact_possible']:
                contacts.append(dict(parent=key[0], source_id=key[1], pool_index=pool_index, **contact))
        first_contact = (dict(lower=min(c['time_lower'] for c in contacts),
                              upper=min(c['time_upper'] for c in contacts)) if contacts else None)
        time_limit = root_limit**3
        if first_contact and sweep.time_root**3 < first_contact['lower']:
            if any(p.get('initial_wet_support', {}).get('positive_initial_wet_overlap_possible', False) for p in pieces):
                raise ValueError('First-contact bound conflicts with actual wet-support intersection')
        records.append(dict(base, status='source-clipped-conditional-geometry', pieces=pieces,
            initial_wet_contacts=contacts, first_initial_wet_contact_time=first_contact,
            original_isolated_geometry_time_limit=time_limit,
            first_contact_proven_inside_isolated_window=bool(first_contact and first_contact['upper'] < time_limit),
            first_contact_possible_inside_isolated_window=bool(first_contact and first_contact['lower'] < time_limit),
            enters_initially_owned_source=any(p['initial_ownership'] == 'wet' for p in pieces),
            initial_wet_overlap_proven=any(p.get('initial_wet_support', {}).get(
                'positive_initial_wet_overlap_proven', False) for p in pieces),
            initial_wet_overlap_possible=any(p.get('initial_wet_support', {}).get(
                'positive_initial_wet_overlap_possible', False) for p in pieces),
            receiver_mass_fraction_bounds=tuple(v/incoming[1] for v in target_mass),
            out_of_block_moment_bounds=outside,
            maximum_relative_moment_uncertainty=max(float((upper[j]-lower[j])/incoming[j]) for j in range(4)),
            original_normal_flux_relative_error=geometry_flux_error))
        if on_face: on_face(records[-1])
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source-report', 'atlas', 'report'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--block-col', type=int, default=12)
    parser.add_argument('--block-row', type=int, default=8)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    part, source, indices, origin, authority, sampler, hashes = load_original_block(args)
    before = [(p['volume'], p['momentum'].copy()) for p in part.pools]
    fronts = analyze(part, assembly(part, face_scheme='donor')['new_region_rates'])
    records = route(part, fronts, on_face=lambda r: print(json.dumps(dict(
        donor=r['donor'], receiver=r['receiver'], status=r['status'], pieces=len(r.get('pieces', [])))), flush=True))
    fragments = original_fragments(part)
    lows = [min(p[j] for f in fragments.values() for p in f.polygon) for j in range(2)]
    highs = [max(p[j] for f in fragments.values() for p in f.polygon) for j in range(2)]
    domain = ((lows[0], lows[1]), (highs[0], lows[1]), (highs[0], highs[1]), (lows[0], highs[1]))
    if sum((f.area for f in fragments.values()), F(0)) != signed_area(domain):
        raise ValueError('Original source fragments do not cover the rectangular pair-audit domain')
    pairs = simultaneous_pairs(records, domain=domain)
    closure_pairs = simultaneous_pairs(records, domain=domain, window_closure=True)
    witness_sources = set()
    for pair in pairs['pairs']+closure_pairs['pairs']:
        if pair['witness_xy'] is None:
            continue
        x, y = pair['witness_xy']
        owners = []
        for key, fragment in fragments.items():
            xy = tuple(p[:2] for p in fragment.polygon)
            sign = 1 if signed_area(xy) > 0 else -1
            if all(sign*((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])) >= 0
                   for a, b in zip(xy, xy[1:]+xy[:1])):
                owners.append(key)
                witness_sources.add(key)
        if not owners:
            raise ValueError('Positive overlap witness lacks an original source owner')
        pair['witness_original_sources'] = owners
    if any(p['volume'] != v or not np.array_equal(p['momentum'], m) for p, (v, m) in zip(part.pools, before)):
        raise ValueError('Geometry routing mutated original water')
    if any(sha(Path(path)) != digest for path, digest in hashes.items()):
        raise ValueError('Source or implementation changed during inlet audit')
    routed = [r for r in records if r['status'] == 'source-clipped-conditional-geometry']
    provenance = [dict(parent=p, source_id=s, original_cell=indices[p],
        authority_codes=sorted(set(map(int, authority[sampler.faces[s]].ravel()))))
        for p, s in sorted({(p['parent'], p['source_id']) for r in routed for p in r['pieces']} | witness_sources)]
    report = dict(schema='raftsim.south_fork.inlet_sweep_geometry.v1', accepted=False,
        source_sha256=hashes, source_time_seconds=source['source_time_seconds'],
        original_block_col_row=[args.block_col, args.block_row], origin_registered_m=origin,
        records=records, provenance=provenance, original_water_unchanged=True,
        simultaneous_stream_pairs=pairs, pair_domain_original_xy=domain,
        isolated_window_stream_pair_bounds=closure_pairs,
        pair_closure_scope='At each common original window limit, footprint closures enclose ALL earlier conditional footprints. Zero upper overlap area proves separation throughout that common window. Positive witnesses are also verified at an explicitly earlier time. This does not evolve pressure or extend the law beyond its original window.',
        pair_time_scope='Each pair uses the earlier of its two original valid observation times. This is not one evolved global multi-stream state. Sub-float positive exact streams are retained; receding/fan streams remain unsupported.',
        conditional_geometry_controls_passed=bool(routed),
        maximum_relative_moment_uncertainty=max(r['maximum_relative_moment_uncertainty'] for r in routed),
        maximum_relative_face_balance_width=max(
            p['conditional_face_transport']['maximum_relative_balance_width'] for r in routed for p in r['pieces']),
        face_transport_scope='Time-integrated conditional advective flux on every original edge of every routed source; incoming minus outgoing balances the non-horizontal stored profile. Original inlet inflow requires coupled donor debit. No pressure, bed-force, receding/fan or physical time-step acceptance.',
        hydrostatic_force_scope='Instantaneous interior-trace hydrostatic/bed momentum residual of the non-horizontal profile, including finite-depth lateral-front pressure jumps. Boundary-aligned wet/dry traces are NOT a common numerical flux. Lateral spreading/front law and nonhydrostatic/curvature/time coupling remain unaccepted.',
        initially_owned_source_streams=sum(r['enters_initially_owned_source'] for r in routed),
        proven_initial_wet_overlap_streams=sum(r['initial_wet_overlap_proven'] for r in routed),
        possible_initial_wet_overlap_streams=sum(r['initial_wet_overlap_possible'] for r in routed),
        initial_ownership_scope='Source membership only; initial_wet_support separately clips at each original pool stage.',
        contact_time_scope='First positive-overlap infimum for the conditional constant-velocity sweep against STATIC original wet support. All wet sources tested, including outside the current footprint. Does not evolve the existing pool, couple pressure or merge streams.',
        scope='Constant-velocity leading outward inlet geometry only. Exact initial wet-support intersections do not merge or step independent streams. Fan, source crossings, pressure/force, time and native/gameplay integration remain open.',
        authority_note='1 captured DEM; 3 exposed rock; 2 submerged prior, 4 interpolation, 5 inferred flank. Rational coordinates add no measured precision.')
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False,
                  default=lambda value: str(value) if isinstance(value, F) else value.tolist())
    print(json.dumps(dict(routed=len(routed), total=len(records),
        maximum_moment_uncertainty=report['maximum_relative_moment_uncertainty'])), flush=True)
    return 0 if report['conditional_geometry_controls_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
