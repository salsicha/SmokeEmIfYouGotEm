"""Source-locked prescribed exterior kinetic trace, not coupled PDE acceptance."""
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
from subcell_front_prescribed_trace import FrontPrescribedTrace


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
    op = FrontPrescribedTrace(fan, fragments, time, boundary='prescribed-fan-velocity')
    g = op.geometry
    if g.active != (0, 1):
        raise ValueError('Original active ownership changed')
    velocities = []
    for i, side in enumerate(('wet_side', 'dry_side')):
        if g.volumes[i] != number(record[side]['volume']):
            raise ValueError('Original source volume changed')
        velocities.append(tuple(number(p)/g.volumes[i] for p in record[side]['momentum']))
    if sum(g.volume_rates, op.zero) != -sum(op.outward_mass_flux, op.zero):
        raise ValueError('Prescribed exterior flux does not match original fan mass budget')
    return dict(source_id=sid, original_volumes_and_total_mass_rate_exact=True,
                boundary_faces=op.boundary_faces, divergence_lift=op.lift,
                divergence_lift_rate=op.lift_rate, linear=op.linear, linear_rate=op.linear_rate,
                constant=op.constant, constant_rate=op.constant_rate,
                physical_owner_velocity_probe=tuple(velocities), result=op.evaluate(velocities),
                note='Actual owner mean is an evaluation probe, not a replacement for the varying exterior trace.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile-report', type=Path, required=True)
    parser.add_argument('--profile-sha256', required=True)
    parser.add_argument('--source-report', type=Path, required=True)
    parser.add_argument('--historical-tool', action='append', default=[], metavar='PATH=COMMIT')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    if digest(args.profile_report) != args.profile_sha256:
        raise ValueError('Qualified profile report changed')
    profile = json.loads(args.profile_report.read_text())
    if profile['schema'] != 'raftsim.south_fork.front_profile_transport.v1' or profile['original_receipts_checks_passed'] is not True:
        raise ValueError('Qualified original profile report required')
    protected = {**profile['current_source_sha256'], **profile['implementation_sha256'],
                 str(args.profile_report.resolve()): args.profile_sha256}
    historical = dict(item.rsplit('=', 1) for item in args.historical_tool)
    if len(historical) != len(args.historical_tool):
        raise ValueError('Duplicate historical tool')
    current, old_tools = verify_protected(protected, historical)
    source_path = str(args.source_report.resolve())
    if source_path not in profile['source_sha256'] or digest(source_path) != profile['source_sha256'][source_path]:
        raise ValueError('Original predictor must be hash-bound by the qualified profile report')
    source = json.loads(args.source_report.read_text())
    if source.get('schema') != 'raftsim.south_fork.affine_front_predictor.v1' or source.get('local_rate_controls_passed') is not True:
        raise ValueError('Qualified original predictor required')
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
        rows.append(dict(index=index, result=check_case(record, sampler), tested=True))
        print(json.dumps(dict(index=index, prescribed_trace_checked=True)), flush=True)
    if not any(row['tested'] for row in rows):
        raise ValueError('No original cases tested')
    for path, expected in {**current, **implementation}.items():
        if digest(path) != expected:
            raise ValueError('Protected source or loaded implementation changed during audit: '+path)
    result = dict(schema='raftsim.south_fork.front_prescribed_trace.v1', protected_sha256=protected,
                  current_source_sha256=current, unused_historical_tools=old_tools,
                  implementation_sha256=implementation, records=rows, prescribed_trace_checks_passed=True,
                  natural_open_pressure_or_coupled_force_or_gameplay_accepted=False, scope=__doc__)
    serialize = lambda v: v.record() if isinstance(v, Radical) else json_default(v)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False, default=serialize)


if __name__ == '__main__':
    main()
