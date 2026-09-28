"""Replay the physical transport pullback on original source; not full PDE acceptance."""
import argparse
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import sys

import numpy as np

from audit_south_fork_front_auxiliary_transport import digest, exact, number
from audit_south_fork_affine_front_metric import verify_protected
from exact_rational_json import json_default
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_affine_dry_fan import AffineDryFan, Radical, _clip
from subcell_exact_geometry import SourceFragment
from subcell_prescribed_physical_transport import PrescribedPhysicalTransport
from subcell_affine_moving_pressure import AffineMovingPressureMetric


def check_case(record, previous, sampler):
    point, normal = (tuple(map(exact, record[k])) for k in ('point', 'normal'))
    depth, slope = exact(record['local_depth']), tuple(map(exact, record['original_gradient']))
    d, time = exact(record['whole']['volume']['radicand']), exact(record['time_increment'])
    fan = AffineDryFan(point, normal, depth, tuple(map(exact, record['local_velocity'])),
                      exact(record['original_bed']), slope, d/(depth*sum(n*n for n in normal)))
    sid = record['source_id']
    whole = SourceFragment(sid, tuple(tuple(F(float(v)) for v in p)
                           for p in sampler.xyz[sampler.faces[sid]]), slope)
    coordinate = lambda p: sum(n*(x-o) for n,x,o in zip(normal,p,point))
    fragments = tuple(replace(whole,polygon=_clip(whole.polygon,coordinate,side)) for side in (False,True))
    op = PrescribedPhysicalTransport(fan,fragments,time,boundary='prescribed-fan-velocity')
    trace, g, metric = op.connections.trace, op.connections.geometry, op.metric
    if g.active != (0,1) or g.volumes != tuple(number(record[k]['volume']) for k in ('wet_side','dry_side')):
        raise ValueError('Original active ownership or volume changed')
    if g.volume_rates != tuple(number(record[k]['volume_rate']) for k in ('wet_side_rates','dry_side_rates')):
        raise ValueError('Original source volume rate changed')
    for attribute in ('linear','linear_rate'):
        if getattr(trace,attribute) != tuple(map(number,previous[attribute])):
            raise ValueError('Qualified boundary coefficients changed')
    for attribute in ('constant','constant_rate'):
        if getattr(trace,attribute) != number(previous[attribute]):
            raise ValueError('Qualified boundary constant changed')
    p = tuple(tuple(map(number,record[k]['momentum'])) for k in ('wet_side','dry_side'))
    pt = tuple(tuple(map(number,record[k]['momentum_rate'])) for k in ('wet_side_rates','dry_side_rates'))
    original = metric.evaluate(p,pt)
    # The recorded physical momentum is the probe. Do not silently use its
    # layer velocity as the pressure model's distinct canonical velocity.
    canonical = original['canonical_velocity']
    result = op.prescribed_kinetic_ledger(canonical)
    if result['physical_momentum'] != p:
        raise ValueError('Original physical momentum failed exact roundtrip')
    if result['transport']['kinetic_energy'] != original['kinetic_energy']:
        raise ValueError('Original two-pole physical kinetic energy changed')
    return dict(source_id=sid,original_volume_momentum_and_rate_retained=True,
                original_physical_momentum=p,original_nondispersive_rate_probe=pt,
                canonical_velocity_probe=canonical,result=result,
                scope='Frozen-fan transport contribution; original nondispersive rate is NOT the coupled dispersive momentum law.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace-report', type=Path, required=True)
    parser.add_argument('--trace-sha256', required=True)
    parser.add_argument('--source-report', type=Path, required=True)
    parser.add_argument('--historical-tool', action='append', default=[], metavar='PATH=COMMIT')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    if digest(args.trace_report) != args.trace_sha256:
        raise ValueError('Qualified prescribed trace report changed')
    trace = json.loads(args.trace_report.read_text())
    if trace['schema'] != 'raftsim.south_fork.front_prescribed_trace.v1' or trace['prescribed_trace_checks_passed'] is not True:
        raise ValueError('Qualified prescribed trace required')
    protected = {**trace['current_source_sha256'], **trace['implementation_sha256'],
                 str(args.trace_report.resolve()): args.trace_sha256}
    historical = dict(item.rsplit('=',1) for item in args.historical_tool)
    if len(historical) != len(args.historical_tool):
        raise ValueError('Duplicate historical tool')
    # The shared verifier forbids exceptions for captured inputs or any code
    # imported into this computation. Original hashes remain unchanged.
    current, old_tools = verify_protected(protected, historical)
    source_path = str(args.source_report.resolve())
    if source_path not in protected or digest(source_path) != protected[source_path]:
        raise ValueError('Original predictor must remain hash-bound')
    source = json.loads(args.source_report.read_text())
    if source['schema'] != 'raftsim.south_fork.affine_front_predictor.v1' or source['local_rate_controls_passed'] is not True:
        raise ValueError('Qualified original predictor required')
    if len(source['records']) != len(trace['records']):
        raise ValueError('Original predictor coverage changed')
    scripts = Path(__file__).resolve().parent
    implementation = {str(Path(m.__file__).resolve()): digest(m.__file__) for m in tuple(sys.modules.values())
                      if getattr(m, '__file__', None) and Path(m.__file__).resolve().parent == scripts}
    mesh_path, = [p for p in protected if p.endswith('troublemaker_registered_source.npz')]
    with np.load(mesh_path, allow_pickle=False) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    rows = []
    for index, (record, prior) in enumerate(zip(source['records'], trace['records'])):
        if prior['index'] != index:
            raise ValueError('Prior source order changed')
        if record['status'] != 'local-uniform-state-predictor-only':
            if prior['tested'] or prior['original_record'] != record:
                raise ValueError('Unsupported original source changed')
            rows.append(dict(index=index, original_record=record, tested=False))
            continue
        if prior['tested'] is not True:
            raise ValueError('Missing qualified prescribed trace')
        print(json.dumps(dict(index=index, status='started')), flush=True)
        rows.append(dict(index=index, result=check_case(record, prior['result'], sampler), tested=True))
        print(json.dumps(dict(index=index, physical_transport_pullback_checked=True)), flush=True)
    if not any(r['tested'] for r in rows):
        raise ValueError('No original source cases tested')
    for path, expected in {**current, **implementation}.items():
        if digest(path) != expected:
            raise ValueError('Protected source or loaded implementation changed during audit: '+path)
    result = dict(schema='raftsim.south_fork.prescribed_physical_transport.v1', protected_sha256=protected,
                  current_source_sha256=current, unused_historical_tools=old_tools,
                  implementation_sha256=implementation, records=rows, physical_transport_pullback_checks_passed=True,
                  nonlinear_force_or_natural_open_boundary_or_gameplay_accepted=False, scope=__doc__)
    serialize = lambda v: v.record() if isinstance(v, Radical) else json_default(v)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False, default=serialize)


if __name__ == '__main__':
    main()
