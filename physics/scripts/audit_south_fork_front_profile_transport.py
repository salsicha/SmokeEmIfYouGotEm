"""Replay original South Fork fan receipts with velocity-resolved transport.

Preserves every original source/state and unsupported record. Passing these
single-fan checks does not qualify interacting fans, dispersive/open-boundary
coupling, finite-step evolution, native integration or playable water.
"""
import argparse
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import sys

import numpy as np

from audit_south_fork_affine_front_metric import verify_protected
from audit_south_fork_front_auxiliary_transport import digest, exact, number
from exact_rational_json import json_default
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_affine_dry_fan import AffineDryFan, Radical, _clip
from subcell_exact_geometry import SourceFragment
from subcell_front_profile_transport import FrontProfileTransport


def check_case(record, sampler):
    point, normal = (tuple(map(exact, record[k])) for k in ('point', 'normal'))
    depth, slope = exact(record['local_depth']), tuple(map(exact, record['original_gradient']))
    d, time = exact(record['whole']['volume']['radicand']), exact(record['time_increment'])
    fan = AffineDryFan(point, normal, depth, tuple(map(exact, record['local_velocity'])),
                      exact(record['original_bed']), slope, d/(depth*sum(n*n for n in normal)))
    sid = record['source_id']
    whole = SourceFragment(sid, tuple(tuple(F(float(v)) for v in p)
                           for p in sampler.xyz[sampler.faces[sid]]), slope)
    coordinate = lambda p: sum(n*(x-o) for n, x, o in zip(normal, p, point))
    fragments = tuple(replace(whole, polygon=_clip(whole.polygon, coordinate, side)) for side in (False, True))
    op = FrontProfileTransport(fan, fragments, time, outer_boundary='reflecting', energy_datum=fan.bed)
    rates = op.shallow_water_rates()
    if op.geometry.active != (0, 1):
        raise ValueError('Original positive wet/dry owners changed')
    for i, side in enumerate(('wet_side', 'dry_side')):
        if op.geometry.volumes[i] != number(record[side]['volume']):
            raise ValueError('Original owner volume changed')
        old = record[side+'_rates']
        for key in ('volume_rate', 'momentum_rate', 'energy_rate_per_density'):
            expected = tuple(map(number, old[key])) if key == 'momentum_rate' else number(old[key])
            if rates[key][i] != expected:
                raise ValueError('Original conservative receipt changed: '+side+' '+key)
    velocity = op.owner_mean_velocity
    probe = tuple((-v, u) for u, v in velocity)
    u, v = op.vector(velocity), op.vector(probe)
    checks = {}
    for name in ('volume_factor_force', 'factor_force', 'difference_force', 'time_commutator'):
        action = getattr(op, name)
        au, av = op.vector(action(velocity)), op.vector(action(probe))
        own = sum((a*b for a, b in zip(u, au)), op.zero)
        paired = sum((a*b+c*d for a, b, c, d in zip(v, au, u, av)), op.zero)
        if own != 0 or paired != 0:
            raise ValueError('Profile factor work identity failed: '+name)
        checks[name] = dict(force=op.pairs(au), own_work=own, paired_work=paired)
        if name in ('factor_force', 'time_commutator'):
            ledger = getattr(op, name+'_ledger')(velocity)
            if ledger.action() != op.pairs(au):
                raise ValueError('Direct force ledger disagrees: '+name)
            checks[name]['ledger'] = dict(faces=ledger.faces, bed=ledger.bed, wall=ledger.wall)
    return dict(source_id=sid, conservative_receipts_match_original_exactly=True,
                rates=rates, shared_faces=op.faces, connection=op.connection,
                depth_advection=op.profile_depth_advection, operators=checks, **op.scope())


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
        raise ValueError('Original source report changed')
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
        print(json.dumps(dict(index=index, source_id=record['source_id'], exact_profile_receipts=True)), flush=True)
    for path, value in {**current, **implementation}.items():
        if digest(path) != value:
            raise ValueError('Protected input or loaded implementation changed: '+path)
    if not rows or not any(row['tested'] for row in rows):
        raise ValueError('No original cases tested')
    result = dict(schema='raftsim.south_fork.front_profile_transport.v1', source_sha256=protected,
                  current_source_sha256=current, implementation_sha256=implementation,
                  unused_historical_tools=old_tools, records=rows, original_receipts_checks_passed=True,
                  full_mass_force_wetting_native_or_gameplay_accepted=False, scope=__doc__)
    serialize = lambda value: value.record() if isinstance(value, Radical) else json_default(value)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False, default=serialize)


if __name__ == '__main__':
    main()
