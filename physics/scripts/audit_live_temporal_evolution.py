"""Replay a complete observed live-source interval; not gameplay qualification.

Uses independent CPU double SSP-RK2 and the existing rational pressure solver.
The interior evolves from the first observation: the second interior is neither
a reset nor an expected answer. Only observed exterior/face data are linearly
interpolated. No extrapolation, bed change, positivity repair or gate relaxation.
This double-storage control is not a float-storage GPU parity fixture.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
import total_depth_bank_replay as bank


KW = dict(second_order=True, dispersive=True, pressure_model='rational_sgn',
          pressure_interpolation='depth_weighted', pressure_formulation='kinematic',
          pressure_bed_slope='geometry')


def observations(record):
    if record.get('schema') != 'raftsim.live_temporal_boundary_inputs.v1':
        raise ValueError('Unsupported live source schema')
    endpoints = []
    for raw in (record['first'], record['second']):
        nx, ny = raw['nx'], raw['ny']
        if not isinstance(nx, int) or not isinstance(ny, int) or not (1 <= nx <= 512 and 1 <= ny <= 512):
            raise ValueError('Invalid source grid')
        value = {key: raw[key] for key in ('nx', 'ny', 'cell_meters', 'origin_x', 'origin_y', 'native_seconds', 'revision')}
        for key, shape in (('state', (ny, nx, 4)), ('bed', (ny, nx)),
                           ('exterior_state', (2*(nx+ny), 4)), ('exterior_bed', (2*(nx+ny),)),
                           ('face_normal_velocity', (2*(nx+ny),))):
            value[key] = np.asarray(raw[key], dtype=float).reshape(shape)
            if not np.isfinite(value[key]).all():
                raise ValueError('Nonfinite source '+key)
        for key in ('cell_meters', 'origin_x', 'origin_y', 'native_seconds'):
            if not np.isfinite(value[key]): raise ValueError('Nonfinite '+key)
        if value['cell_meters'] <= 0: raise ValueError('Invalid cell size')
        for key in ('state', 'exterior_state'):
            state = value[key]
            if np.any(state[..., [0, 3]] < 0) or np.any(state[..., 1:3][state[..., 0] == 0] != 0):
                raise ValueError('Invalid conserved source '+key)
            with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
                velocity = np.divide(state[..., 1:3], state[..., 0, None],
                                     out=np.zeros_like(state[..., 1:3]), where=state[..., 0, None] > 0)
            if not np.isfinite(velocity).all(): raise ValueError('Unrepresentable source velocity')
        endpoints.append(value)
    a, b = endpoints
    for key in ('nx', 'ny', 'cell_meters', 'origin_x', 'origin_y'):
        if a[key] != b[key]: raise ValueError('Unregistered source '+key)
    for key in ('bed', 'exterior_bed'):
        if not np.array_equal(a[key], b[key]): raise ValueError('Changed source '+key)
    if b['native_seconds'] <= a['native_seconds'] or b['revision'] <= a['revision']:
        raise ValueError('Source time/revision must increase')
    # bank.advance currently evolves h/hu/hv only. Never silently drop live foam.
    if any(np.any(e[key][..., 3] != 0) for e in endpoints for key in ('state', 'exterior_state')):
        raise ValueError('Double control requires zero observed foam')
    return a, b


def boundary_provider(a, b):
    duration = b['native_seconds']-a['native_seconds']
    acceleration = (b['face_normal_velocity']-a['face_normal_velocity'])/duration

    def sample(elapsed, stage):
        if not np.isfinite(elapsed) or not 0 <= elapsed <= duration:
            raise ValueError('Outside observed temporal bracket')
        alpha = elapsed/duration
        def interpolate(key):
            if elapsed == 0: return a[key].copy()
            if elapsed == duration: return b[key].copy()
            return (1-alpha)*a[key]+alpha*b[key]
        return (interpolate('exterior_state'), a['exterior_bed'].copy(),
                np.stack((interpolate('face_normal_velocity'), acceleration), axis=-1))
    return duration, sample


def replay(record, *, breaking_model='none'):
    if breaking_model not in ('none','hybrid_front'):raise ValueError('Unsupported breaking model')
    a, b = observations(record)
    duration, boundary = boundary_provider(a, b)
    report = dict(requested_seconds=duration, first_native_seconds=a['native_seconds'],
                  second_native_seconds=b['native_seconds'], shape=[a['ny'], a['nx']],
                  cell_meters=a['cell_meters'], maximum_trials=4096, completed=False,
                  integrated=False, scene_accepted=False, storage='CPU double',breaking_model=breaking_model)
    state = a['state'][..., :3].copy()
    try:
        state, stats = bank.advance(state, a['bed'], a['cell_meters'], duration,
                                   max_trials=4096, boundary_at_time=boundary, breaking_model=breaking_model, **KW)
        report.update(completed=True, statistics=stats)
    except (bank.ReplayExhausted, bank.ReplayInvalidRate) as error:
        state = error.state
        report.update(error=str(error), failure=error.diagnostics)
    except (ValueError, FloatingPointError) as error:
        report.update(error=str(error), failure=dict(elapsed_s=0., steps=0))
    report['maximum_state_change'] = float(abs(state-a['state'][..., :3]).max())
    return state, report


def write_fixture(path, record, expected, *, breaking_model='none'):
    if breaking_model not in ('none','hybrid_front'):raise ValueError('Unsupported breaking model')
    a, b = observations(record)
    # The whole-interval double control is deliberately independent of GPU
    # stage storage. Match existing state error gates, not exact step counts.
    expected4 = np.concatenate((expected, np.zeros((*expected.shape[:2], 1))), axis=-1)
    arrays = (a['state'], a['bed'], a['exterior_state'], b['exterior_state'],
              a['exterior_bed'], a['face_normal_velocity'], b['face_normal_velocity'], expected4)
    converted = [np.asarray(value, dtype='<f4') for value in arrays]
    if any(not np.isfinite(value).all() for value in converted):
        raise ValueError('Fixture is not float32 representable')
    with path.open('xb') as stream:
        version=2 if breaking_model=='hybrid_front' else 1
        stream.write(struct.pack('<IIIIfdd', 0x52535445, version, a['nx'], a['ny'],
                                 a['cell_meters'], a['native_seconds'], b['native_seconds']))
        if version==2:stream.write(struct.pack('<I',1)) # explicit same-stage hybrid classifier
        for value in converted: stream.write(value.tobytes(order='C'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, help='Optional complete-interval CPU reference for the GPU test')
    parser.add_argument('--breaking-model',choices=('none','hybrid_front'),default='none')
    args = parser.parse_args()
    output = args.report.with_suffix('.last-state.npy')
    if args.report.exists() or output.exists(): raise FileExistsError(args.report)
    if args.fixture and args.fixture.exists(): raise FileExistsError(args.fixture)
    data = args.inputs.read_bytes()
    state, report = replay(json.loads(data),breaking_model=args.breaking_model)
    report.update(schema='raftsim.live_temporal_evolution.v1', scope=__doc__,
                  source_sha256=hashlib.sha256(data).hexdigest(),
                  implementation_hashes={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                      for name in ('audit_live_temporal_evolution.py', 'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py',
                                   'total_depth_nonlinear_pressure.py','breaking_front_reference.py')})
    with output.open('xb') as stream: np.save(stream, state)
    report.update(last_state=str(output.resolve()), state_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    if args.fixture and report['completed']:
        write_fixture(args.fixture, json.loads(data), state,breaking_model=args.breaking_model)
        report.update(fixture=str(args.fixture.resolve()), fixture_sha256=hashlib.sha256(args.fixture.read_bytes()).hexdigest())
    with args.report.open('x') as stream: json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps(report, indent=2, allow_nan=False), flush=True)


if __name__ == '__main__': main()
