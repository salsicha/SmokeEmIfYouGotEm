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
    occupied = {(p['parent'], int(s)) for p in part.pools for s in p['source_triangle_indices']}
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
        incoming = tuple(sweep.full_moment(p) for p in range(4))
        base = dict(donor=list(donor), receiver=list(receiver), original_inlet_xyz=edge,
            time_root=sweep.time_root, physical_time=sweep.time_root**3,
            primary_height=height, full_incoming_moments=incoming,
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
                pieces.append(dict(parent=key[0], source_id=key[1], original_gradient=fragment.gradient,
                    initial_ownership=('wet' if key in occupied else 'primary-birth' if key in primary else 'unowned'),
                    positive_water_proven=value['lower'][1] > 0,
                    moment_lower=value['lower'], moment_upper=value['upper'],
                    bounded_switch_intervals=value['bounded_switch_intervals']))
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
        records.append(dict(base, status='source-clipped-conditional-geometry', pieces=pieces,
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
    if any(p['volume'] != v or not np.array_equal(p['momentum'], m) for p, (v, m) in zip(part.pools, before)):
        raise ValueError('Geometry routing mutated original water')
    if any(sha(Path(path)) != digest for path, digest in hashes.items()):
        raise ValueError('Source or implementation changed during inlet audit')
    routed = [r for r in records if r['status'] == 'source-clipped-conditional-geometry']
    provenance = [dict(parent=p, source_id=s, original_cell=indices[p],
        authority_codes=sorted(set(map(int, authority[sampler.faces[s]].ravel()))))
        for p, s in sorted({(p['parent'], p['source_id']) for r in routed for p in r['pieces']})]
    report = dict(schema='raftsim.south_fork.inlet_sweep_geometry.v1', accepted=False,
        source_sha256=hashes, source_time_seconds=source['source_time_seconds'],
        original_block_col_row=[args.block_col, args.block_row], origin_registered_m=origin,
        records=records, provenance=provenance, original_water_unchanged=True,
        conditional_geometry_controls_passed=bool(routed),
        maximum_relative_moment_uncertainty=max(r['maximum_relative_moment_uncertainty'] for r in routed),
        scope='Constant-velocity leading outward inlet geometry only. Independent streams are not merged or stepped. Fan, source crossings, pressure/force, time and native/gameplay integration remain open.',
        authority_note='1 captured DEM; 3 exposed rock; 2 submerged prior, 4 interpolation, 5 inferred flank. Rational coordinates add no measured precision.')
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False,
                  default=lambda value: str(value) if isinstance(value, F) else value.tolist())
    print(json.dumps(dict(routed=len(routed), total=len(records),
        maximum_moment_uncertainty=report['maximum_relative_moment_uncertainty'])), flush=True)
    return 0 if report['conditional_geometry_controls_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
