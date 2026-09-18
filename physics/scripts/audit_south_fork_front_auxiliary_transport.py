"""Original South Fork front transport, NOT a nonlinear river qualification.

Retain every original local predictor and unsupported branch. Audit the actual
owner-averaged velocities; the rotated velocity is an adjoint probe, not a
replacement physical state. No original rate, geometry or acceptance is edited.
"""
import argparse
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import sys

import numpy as np

from audit_south_fork_affine_front_predictor import digest, exact
from audit_south_fork_affine_front_metric import verify_protected
from exact_rational_json import json_default
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_affine_dry_fan import AffineDryFan, Radical, _clip, _integrate
from subcell_exact_geometry import SourceFragment
from subcell_front_auxiliary_transport import FrontAuxiliaryTransport


def number(value):
    if isinstance(value, dict) and 'radicand' in value:
        return Radical(exact(value['radicand']), exact(value['rational']), exact(value['radical_coefficient']))
    return exact(value)


def check_case(record, sampler):
    point, normal = (tuple(map(exact, record[key])) for key in ('point', 'normal'))
    depth, slope = exact(record['local_depth']), tuple(map(exact, record['original_gradient']))
    d = exact(record['whole']['volume']['radicand'])
    time = exact(record['time_increment'])
    fan = AffineDryFan(point, normal, depth, tuple(map(exact, record['local_velocity'])),
                      exact(record['original_bed']), slope, d/(depth*sum(n*n for n in normal)))
    sid = record['source_id']
    fragment = SourceFragment(sid, tuple(tuple(F(float(v)) for v in p)
        for p in sampler.xyz[sampler.faces[sid]]), slope)
    coordinate = lambda p: sum(n*(x-o) for n, x, o in zip(normal, p, point))
    fragments = tuple(replace(fragment, polygon=_clip(fragment.polygon, coordinate, side)) for side in (False, True))
    parts = [record['wet_side'], record['dry_side']]
    volume = tuple(number(p['volume']) for p in parts)
    velocity = tuple(tuple(number(x)/v for x in p['momentum']) for p, v in zip(parts, volume))
    operator = FrontAuxiliaryTransport(fan, fragments, time, velocity, outer_boundary='reflecting')
    if operator.geometry.active != (0, 1) or operator.geometry.volumes != volume:
        raise ValueError('Original positive wet/dry-side receipts changed')
    if operator.geometry.volume_rates != tuple(number(record[k]['volume_rate']) for k in ('wet_side_rates', 'dry_side_rates')):
        raise ValueError('Original analytic volume rates changed')
    # Independent VOLUME polynomial integral, not a second boundary contraction.
    head, front, linear, _, _ = fan._profile(time)
    coefficient = F(1, 9)/(fan.gravity*fan.norm2)
    for i, fragment in enumerate(fragments):
        varying = _clip(_clip(fragment.polygon, lambda p: fan._coordinate(p)-head, True),
                        lambda p: fan._coordinate(p)-front, False)
        cubic = sum((_integrate((varying[0], varying[j], varying[j+1]), [linear]*3, fan.zero)
                     for j in range(1, len(varying)-1)), fan.zero)
        expected = tuple(-2*coefficient*coefficient*n*cubic/time for n in normal)
        if expected != operator.depth_gradient_moments[i]:
            raise ValueError('Original volume gradient and shared boundary moments disagree')
    probe = tuple((-row[1], row[0]) for row in velocity)
    u, v = operator.vector(velocity), operator.vector(probe)
    checks = {}
    for name in ('volume_factor_force', 'factor_force', 'difference_force', 'time_commutator'):
        action = getattr(operator, name)
        au, av = operator.vector(action(velocity)), operator.vector(action(probe))
        own_work = sum((a*b for a, b in zip(u, au)), fan.zero)
        paired = sum((a*b+c*d for a, b, c, d in zip(v, au, u, av)), fan.zero)
        if own_work != 0 or paired != 0:
            raise ValueError('Original front transport skew identity failed: '+name)
        checks[name] = dict(force=operator.pairs(au), original_velocity_work=own_work, adjoint_probe_work=paired)
        if name in ('factor_force', 'time_commutator'):
            ledger = getattr(operator, name+'_ledger')(velocity)
            if ledger.action() != operator.pairs(au):
                raise ValueError('Direct source force ledger differs from operator: '+name)
            for axis in range(2):
                if sum((row[axis] for row in ledger.action()), fan.zero) != sum(
                        (bed[axis]+wall[axis] for bed, wall in zip(ledger.bed, ledger.wall)), fan.zero):
                    raise ValueError('Shared source momentum does not cancel: '+name)
            checks[name]['direct_ledger'] = dict(shared_faces=ledger.faces, bed=ledger.bed, wall=ledger.wall)
    return dict(source_id=sid, original_owner_velocity=velocity,
                original_volumes_and_rates_exact=True, depth_gradient_volume_boundary_identity_exact=True,
                depth_gradient_moments=operator.depth_gradient_moments, connection=operator.connection,
                shared_faces=operator.faces, operators=checks, **operator.scope())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--historical-tool', action='append', default=[], metavar='PATH=COMMIT')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    if digest(args.source_report) != args.source_sha256:
        raise ValueError('Original predictor report hash changed')
    source = json.loads(args.source_report.read_text())
    if source['schema'] != 'raftsim.south_fork.affine_front_predictor.v1' or source['local_rate_controls_passed'] is not True:
        raise ValueError('Qualified original local predictor required')
    protected = {**source['source_sha256'], **source['predictor_sha256'],
                 str(args.source_report.resolve()): args.source_sha256}
    historical = dict(item.rsplit('=', 1) for item in args.historical_tool)
    if len(historical) != len(args.historical_tool):
        raise ValueError('Duplicate historical tool')
    current, old_tools = verify_protected(protected, historical)
    scripts = Path(__file__).resolve().parent
    implementation = {str(Path(m.__file__).resolve()): digest(m.__file__) for m in tuple(sys.modules.values())
                      if getattr(m, '__file__', None) and Path(m.__file__).resolve().parent == scripts}
    mesh_path, = [p for p in protected if p.endswith('troublemaker_registered_source.npz')]
    with np.load(mesh_path, allow_pickle=False) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    rows = []
    for index, record in enumerate(source['records']):
        if record['status'] != 'local-uniform-state-predictor-only':
            rows.append(dict(index=index, original_record=record, tested=False))
            continue
        result = check_case(record, sampler)
        rows.append(dict(index=index, result=result, tested=True))
        print(json.dumps(dict(index=index, source_id=record['source_id'], exact_front_transport_checks=True)), flush=True)
    for path, value in {**current, **implementation}.items():
        if digest(path) != value:
            raise ValueError('Source or loaded implementation changed during audit: '+path)
    if not rows or not any(row['tested'] for row in rows):
        raise ValueError('No original cases tested')
    result = dict(schema='raftsim.south_fork.front_auxiliary_transport.v1', source_sha256=protected,
                  current_source_sha256=current, implementation_sha256=implementation,
                  unused_historical_tools=old_tools, records=rows, local_transport_checks_passed=True,
                  full_mass_force_wetting_native_or_gameplay_accepted=False, scope=__doc__)
    serialize = lambda value: value.record() if isinstance(value, Radical) else json_default(value)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False, default=serialize)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
