"""Original South Fork moment transport and gravitational exchange receipts.

Reuse the completed hash-bound total-energy evidence. No pressure solve, new
source geometry, conservative dispersive closure or playable update is supplied.
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
from subcell_front_moment_transport import FrontMomentTransport


def check_coverage(source, total):
    if (source['schema'] != 'raftsim.south_fork.affine_front_predictor.v1'
            or source['local_rate_controls_passed'] is not True
            or total['schema'] != 'raftsim.south_fork.affine_total_energy.v1'
            or total['exact_source_total_energy_checks_passed'] is not True
            or len(source['records']) != len(total['records'])):
        raise ValueError('Complete qualified original source and total-energy evidence required')
    for index, (record, row) in enumerate(zip(source['records'], total['records'])):
        expected = record['status'] == 'local-uniform-state-predictor-only'
        if row['index'] != index or row['tested'] is not expected:
            raise ValueError('Original coverage or ordering changed')
        if expected:
            if row['source_id'] != record['source_id']:
                raise ValueError('Original source identity changed')
        elif row['original_record'] != record:
            raise ValueError('Unsupported original record changed')
    if not any(row['tested'] for row in total['records']):
        raise ValueError('No supported original source cases')


def check_source(record, sampler, saved):
    point, normal = (tuple(map(exact, record[k])) for k in ('point', 'normal'))
    depth, slope = exact(record['local_depth']), tuple(map(exact, record['original_gradient']))
    fan = AffineDryFan(point, normal, depth, tuple(map(exact, record['local_velocity'])),
                      exact(record['original_bed']), slope,
                      exact(record['whole']['volume']['radicand'])/(depth*sum(n*n for n in normal)))
    sid, t = record['source_id'], exact(record['time_increment'])
    whole = SourceFragment(sid, tuple(tuple(F(float(v)) for v in p) for p in sampler.xyz[sampler.faces[sid]]), slope)
    coordinate = lambda p: sum(n*(x-o) for n, x, o in zip(normal, p, point))
    fragments = tuple(replace(whole, polygon=_clip(whole.polygon, coordinate, side)) for side in (False, True))
    op = FrontMomentTransport(fan, fragments, t)
    g = op.geometry
    if (g.active != (0, 1) or g.volumes != tuple(number(record[k]['volume']) for k in ('wet_side', 'dry_side'))
            or g.volume_rates != tuple(number(record[k]['volume_rate']) for k in ('wet_side_rates', 'dry_side_rates'))):
        raise ValueError('Original source volumes or rates changed')
    rates = op.rates()
    potential = op.potential_balance(number(saved['energy_datum']))
    for coordinate in ('physical', 'canonical'):
        if sum(potential['potential_rate'], op.zero) != number(saved[coordinate+'_time_work']['potential_energy_direction']):
            raise ValueError('Gravitational transport differs from certified original total-energy work')
    return dict(moment_transport=rates, potential_balance=potential,
                exact_original_moment_transport_and_gravity_work=True,
                pressure_solve_performed=False, dispersive_force_or_interacting_fronts_or_gameplay_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'total', 'report'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--total-sha256', required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    if digest(args.total) != args.total_sha256:
        raise ValueError('Qualified total-energy report changed')
    total, source = (json.loads(p.read_text()) for p in (args.total, args.source))
    protected = dict(total['protected_sha256'])
    for path, sha in total['implementation_sha256'].items():
        if path in protected and protected[path] != sha:
            raise ValueError('Conflicting protected hashes')
        protected[path] = sha
    protected[str(args.total.resolve())] = args.total_sha256
    if str(args.source.resolve()) not in protected or digest(args.source) != protected[str(args.source.resolve())]:
        raise ValueError('Original predictor must remain hash-bound')
    verify_protected(protected, {})
    check_coverage(source, total)
    scripts = Path(__file__).resolve().parent
    implementation = {str(Path(m.__file__).resolve()): digest(m.__file__) for m in tuple(sys.modules.values())
                      if getattr(m, '__file__', None) and Path(m.__file__).resolve().parent == scripts}
    mesh_path, = [p for p in protected if p.endswith('troublemaker_registered_source.npz')]
    with np.load(mesh_path, allow_pickle=False) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    rows = []
    for record, old in zip(source['records'], total['records']):
        if not old['tested']:
            rows.append(old)
            continue
        started = time.perf_counter()
        print(json.dumps(dict(index=old['index'], phase='started')), flush=True)
        result = check_source(record, sampler, old['result'])
        rows.append(dict(index=old['index'], source_id=record['source_id'], tested=True, result=result))
        print(json.dumps(dict(index=old['index'], phase='passed', seconds=time.perf_counter()-started)), flush=True)
    verify_protected({**protected, **implementation}, {})
    result = dict(schema='raftsim.south_fork.front_moment_transport.v1', protected_sha256=protected,
                  implementation_sha256=implementation, records=rows, exact_source_moment_transport_passed=True,
                  dispersive_force_or_interacting_fronts_or_gameplay_accepted=False, scope=__doc__)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False,
                  default=lambda v: v.record() if isinstance(v, Radical) else json_default(v))


if __name__ == '__main__':
    main()
