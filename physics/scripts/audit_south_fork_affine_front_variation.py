"""Verify saved prescribed-pressure states and primitive work on original sources.

Reuses the qualified canonical and auxiliary velocities; it never re-solves
their physical momentum system. Metric construction still solves its geometry
and prescribed boundary shifts. This is not a conservative nonlinear step.
"""
import argparse
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import sys
import time

import numpy as np

from audit_south_fork_front_auxiliary_transport import digest, exact, number
from audit_south_fork_affine_front_metric import verify_protected
from exact_rational_json import json_default
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_affine_dry_fan import AffineDryFan, Radical, _clip
from subcell_exact_geometry import SourceFragment
from subcell_front_prescribed_trace import FrontPrescribedTrace
from subcell_affine_moving_pressure import AffineMovingPressureMetric
from subcell_affine_front_variation import AffineFrontPressureVariation


def numeric(x):
    return x if isinstance(x, (Radical, F)) else number(x)


def pairs(values):
    return tuple(tuple(map(numeric, row)) for row in values)


def check_saved(trace, metric, saved):
    """Check original equations and both coordinate chain rules without a solve."""
    m = metric
    p, pt = pairs(saved['physical_momentum']), pairs(saved['physical_momentum_rate'])
    old = saved['result']
    state = dict(canonical_velocity=pairs(old['canonical_velocity']), poles=[dict(
        length=numeric(s['length']), weight=numeric(s['weight']),
        auxiliary_velocity=pairs(s['auxiliary_velocity'])) for s in old['poles']])
    # This validates original pole order/constants, every original equation,
    # boundary shifts and p=Bv+q. No stored success boolean is trusted.
    variation = AffineFrontPressureVariation(trace, m, p, solved_state=state)
    v, vt = m.vector(state['canonical_velocity']), m.vector(pairs(old['canonical_velocity_rate']))
    mv = tuple(mi*x for mi, x in zip(m.mass, v))
    mvt = tuple(mt*x+mi*xt for mt, x, mi, xt in zip(m.mass_rate, v, m.mass, vt))
    if m.pairs(mv) != pairs(old['canonical_momentum']) or m.pairs(mvt) != pairs(old['canonical_momentum_rate']):
        raise ValueError('Saved canonical momentum or time derivative changed')
    if (pairs(saved['boundary_momentum_shift']) != m.pairs(m.offset)
            or pairs(saved['boundary_momentum_shift_rate']) != m.pairs(m.offset_rate)
            or numeric(saved['boundary_energy_constant']) != -m.dual_constant
            or numeric(saved['boundary_energy_constant_rate']) != -m.dual_constant_rate):
        raise ValueError('Saved prescribed boundary shift or energy changed')
    reconstructed_rate = [m.constant*x for x in mvt]
    positive = [m.constant*m.dot(v, mv)/2]
    for pole, stored in zip(m.poles, old['poles']):
        a = m.vector(pairs(stored['auxiliary_velocity']))
        at = m.vector(pairs(stored['auxiliary_velocity_rate']))
        lhs = tuple(x+y for x, y in zip(m.action(pole['matrix'], at), m.action(pole['matrix_rate'], a)))
        if lhs != tuple(x-pole['length']*y for x, y in zip(mvt, m.linear_rate)):
            raise ValueError('Original prescribed pole time equation changed')
        for i in range(len(m.mass)):
            reconstructed_rate[i] += pole['weight']*(m.mass_rate[i]*a[i]+m.mass[i]*at[i])
        # Independent original local-jet energy, not the stored quadratic sum.
        local = trace.evaluate(m.pairs(a), m.pairs(at))
        positive.append(pole['weight']*(sum((mi*x*x for mi, x in zip(m.mass, a)), m.zero)/2
                                         +pole['length']*local['kinetic_energy']))
    if m.pairs(reconstructed_rate) != pt:
        raise ValueError('Original physical momentum time reconstruction changed')
    energy = sum(positive, m.zero)
    if tuple(positive) != tuple(map(numeric, old['positive_energy_terms'])) or energy != numeric(old['kinetic_energy']):
        raise ValueError('Original positive kinetic energy changed')
    physical = variation.time_work(pt)
    canonical = variation.time_work(m.pairs(mvt), momentum_coordinate='canonical')
    if (physical['energy_direction'] != numeric(old['kinetic_energy_rate'])
            or canonical['energy_direction'] != physical['energy_direction']
            or numeric(old['positive_auxiliary_energy_rate']) != physical['energy_direction']):
        raise ValueError('Complete affine primitive time work changed')
    if (physical['momentum_work'] != numeric(old['momentum_work'])
            or sum((physical[k] for k in ('depth_moment_work', 'face_column_work', 'boundary_flux_work')), m.zero)
               != numeric(old['geometry_time_work'])
            or physical['bed_gradient_work'] != 0 or canonical['bed_gradient_work'] != 0):
        raise ValueError('Prescribed momentum/geometry/boundary work split changed')
    return dict(physical_time_work=physical, canonical_time_work=canonical,
                primitive_gradients=variation.gradients, exact_saved_state_and_pullback=True,
                conservative_force_or_open_boundary_or_gameplay_accepted=False)


def source_trace(record, sampler):
    point, normal = (tuple(map(exact, record[k])) for k in ('point', 'normal'))
    depth, slope = exact(record['local_depth']), tuple(map(exact, record['original_gradient']))
    d = exact(record['whole']['volume']['radicand'])
    fan = AffineDryFan(point, normal, depth, tuple(map(exact, record['local_velocity'])),
                      exact(record['original_bed']), slope, d/(depth*sum(n*n for n in normal)))
    sid = record['source_id']
    whole = SourceFragment(sid, tuple(tuple(F(float(v)) for v in p)
                           for p in sampler.xyz[sampler.faces[sid]]), slope)
    coordinate = lambda p: sum(n*(x-o) for n, x, o in zip(normal, p, point))
    fragments = tuple(replace(whole, polygon=_clip(whole.polygon, coordinate, side)) for side in (False, True))
    trace = FrontPrescribedTrace(fan, fragments, exact(record['time_increment']), boundary='prescribed-fan-velocity')
    g = trace.geometry
    if (g.active != (0, 1) or g.volumes != tuple(number(record[k]['volume']) for k in ('wet_side', 'dry_side'))
            or g.volume_rates != tuple(number(record[k]['volume_rate']) for k in ('wet_side_rates', 'dry_side_rates'))):
        raise ValueError('Original source ownership, volumes or rates changed')
    return trace


def check_coverage(source, replay):
    if (source['schema'] != 'raftsim.south_fork.affine_front_predictor.v1'
            or source['local_rate_controls_passed'] is not True
            or replay['schema'] != 'raftsim.south_fork.affine_moving_pressure.v1'
            or replay['affine_original_poles_checks_passed'] is not True
            or len(source['records']) != len(replay['records'])):
        raise ValueError('Complete qualified original source and affine replay required')
    for index, (record, saved) in enumerate(zip(source['records'], replay['records'])):
        expected = record['status'] == 'local-uniform-state-predictor-only'
        if saved['index'] != index or saved['tested'] is not expected:
            raise ValueError('Original coverage/order changed')
        if not expected:
            if saved['original_record'] != record:
                raise ValueError('Unsupported original source changed')
            continue
        s = saved['result']
        if (s['source_id'] != record['source_id']
                or pairs(s['physical_momentum']) != pairs([record[k]['momentum'] for k in ('wet_side', 'dry_side')])
                or pairs(s['physical_momentum_rate']) != pairs([record[k]['momentum_rate'] for k in ('wet_side_rates', 'dry_side_rates')])):
            raise ValueError('Original source identity, momentum or time rate changed')
    if not any(r['tested'] for r in replay['records']):
        raise ValueError('No original supported source cases')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--replay-sha256', required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    if digest(args.replay) != args.replay_sha256:
        raise ValueError('Qualified replay changed')
    replay, source = (json.loads(p.read_text()) for p in (args.replay, args.source))
    protected = {**replay['protected_sha256'], **replay['implementation_sha256'],
                 str(args.replay.resolve()): args.replay_sha256}
    verify_protected(protected, {})
    source_path = str(args.source.resolve())
    if source_path not in protected or digest(args.source) != protected[source_path]:
        raise ValueError('Original predictor must remain hash-bound')
    check_coverage(source, replay)
    scripts = Path(__file__).resolve().parent
    implementation = {str(Path(m.__file__).resolve()): digest(m.__file__) for m in tuple(sys.modules.values())
                      if getattr(m, '__file__', None) and Path(m.__file__).resolve().parent == scripts}
    mesh_path, = [p for p in protected if p.endswith('troublemaker_registered_source.npz')]
    with np.load(mesh_path, allow_pickle=False) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    rows = []
    for record, saved in zip(source['records'], replay['records']):
        if not saved['tested']:
            rows.append(saved)
            continue
        started = time.perf_counter()
        print(json.dumps(dict(index=saved['index'], phase='started')), flush=True)
        trace = source_trace(record, sampler)
        metric = AffineMovingPressureMetric.from_trace(trace)
        result = check_saved(trace, metric, saved['result'])
        rows.append(dict(index=saved['index'], source_id=record['source_id'], tested=True, result=result))
        print(json.dumps(dict(index=saved['index'], phase='passed', seconds=time.perf_counter()-started)), flush=True)
    verify_protected({**protected, **implementation}, {})
    result = dict(schema='raftsim.south_fork.affine_front_variation.v1', protected_sha256=protected,
                  implementation_sha256=implementation, records=rows, exact_source_pullbacks_passed=True,
                  conservative_force_or_open_boundary_or_gameplay_accepted=False, scope=__doc__)
    serialize = lambda v: v.record() if isinstance(v, Radical) else json_default(v)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False, default=serialize)


if __name__ == '__main__':
    main()
