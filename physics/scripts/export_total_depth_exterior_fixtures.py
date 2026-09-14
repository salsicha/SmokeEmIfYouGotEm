"""Explicit exterior FV transport fixtures; not an open-pressure qualification."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
from total_depth_bank_replay import rate
from total_depth_nonlinear_pressure import geometric_bed_slope


def recorded_fixtures(trace, index):
    """Two unmodified actual stage inputs, with independently computed CPU rates."""
    from audit_recorded_stages import read_records
    import audit_live_temporal_evolution as temporal
    metadata = json.loads(trace.read_text())
    if not metadata.get('completed') or not metadata.get('final_state_exact_to_live'):
        raise ValueError('Recorded trace must reproduce the live owner exactly')
    if not isinstance(index, int) or not 0 <= index < len(metadata['trials']):
        raise ValueError('Recorded trial index outside trace')
    binary_path, source_path = Path(metadata['binary']), Path(metadata['source'])
    source = json.loads(source_path.read_text())
    trial, stages, *_ = list(read_records(metadata, binary_path.read_bytes()))[index]
    i = trial['interval']; raw = source['observations']
    a, b = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1', first=raw[i], second=raw[i+1]))
    _, boundary = temporal.boundary_provider(a, b)
    cases = []
    for k, stage in enumerate(stages):
        es, eb, _ = boundary(trial['begin']-a['native_seconds']+(trial['attempted_dt'] if k else 0), None)
        # GPU buffers store these exact represented values, not double ghosts.
        es = es.astype(np.float32).astype(float); eb = eb.astype(np.float32).astype(float)
        state, bed = stage['state'].astype(float), a['bed'].astype(np.float32).astype(float)
        ledger = {}
        expected, cfl = rate(state[..., :3], bed, .5, second_order=True, foam=state[..., 3],
                             exterior=(es, eb), boundary_diagnostics=ledger)
        cases.append(dict(name=f'recorded_interval_{i}_trial_{trial["trial"]}_stage_{k}', state=state, bed=bed,
            exterior=(es, eb), rate=expected, flux=ledger['flux'],
            slope=geometric_bed_slope(bed, .5, False, exterior_bed=eb), dx=.5, second_order=True, cfl=cfl))
    hashes = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in (trace, binary_path, source_path)}
    return cases, dict(index=index, trial=trial, source_hashes=hashes)


def pack_edges(value):
    """Padded grid to ghost centres west/east/south/north, excluding corners."""
    return np.concatenate((value[1:-1, 0], value[1:-1, -1], value[0, 1:-1], value[-1, 1:-1]))


def fixtures():
    cases = []
    specs = [('east', 17, 13), ('west', 17, 13), ('north', 17, 13), ('south', 17, 13),
             ('lake', 17, 13), ('dry', 17, 13), ('thin', 17, 13), ('random', 17, 13),
             ('random', 1, 17), ('random', 19, 1), ('random', 1, 1)]
    for index, (name, nx, ny) in enumerate(specs):
        y, x = np.indices((ny+2, nx+2), dtype=float)
        rng = np.random.default_rng(952+index)
        h = np.ones_like(x); bed = h*0; u = h*0; v = h*0; foam = h*.25
        if name in ('east', 'west'): u[:] = .75 if name == 'east' else -.75
        if name in ('north', 'south'): v[:] = .75 if name == 'north' else -.75
        if name == 'lake':
            bed = .125*((x+2*y) % 13); h = np.maximum(0, 1-bed)
            foam = rng.uniform(0, 2, h.shape)
        if name == 'dry': h[:] = 0; foam[:] = 0
        if name == 'thin':
            h[:] = 1e-30; bed[:] = 500; u[:] = .75
            foam = .2+.1*np.sin(x)**2
        if name == 'random':
            h = np.exp(rng.uniform(-8, 1, h.shape)); h[rng.random(h.shape) < .1] = 0
            bed = rng.uniform(-.2, .2, h.shape)
            u = rng.uniform(-2, 2, h.shape); v = rng.uniform(-2, 2, h.shape)
            foam = rng.uniform(0, 2, h.shape)
        full = np.stack((h, h*u, h*v, foam), axis=-1).astype('float32')
        bed = bed.astype('float32')
        for second in (False, True):
            state = full[1:-1, 1:-1].copy(); b = bed[1:-1, 1:-1].copy()
            exterior = pack_edges(full), pack_edges(bed)
            ledger = {}
            expected, cfl = rate(state[..., :3].astype(float), b.astype(float), .5,
                second_order=second, foam=state[..., 3].astype(float), exterior=exterior,
                boundary_diagnostics=ledger)
            # Physical fixed-bed derivative uses the supplied ghost centres.
            slope = np.stack(((bed[1:-1, 2:].astype(float)-bed[1:-1, :-2]),
                              (bed[2:, 1:-1].astype(float)-bed[:-2, 1:-1])), axis=-1)
            cases.append(dict(name=name+('_mc' if second else '_first'), state=state, bed=b,
                exterior=exterior, rate=expected, flux=ledger['flux'], slope=slope, dx=.5,
                second_order=second, cfl=cfl))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--recorded-trace', type=Path)
    parser.add_argument('--record', type=int, default=0)
    args = parser.parse_args()
    if args.output.exists() or args.output.with_suffix('.json').exists(): raise FileExistsError(args.output)
    cases = fixtures()
    recorded = None
    if args.recorded_trace:
        extra, recorded = recorded_fixtures(args.recorded_trace, args.record)
        cases.extend(extra)
    payload = bytearray(struct.pack('<III', 0x52534558, 1, len(cases)))
    for c in cases:
        ny, nx = c['bed'].shape
        payload += struct.pack('<IIIff', nx, ny, c['second_order'], c['dx'], c['cfl'])
        for a in (c['bed'], c['state'], *c['exterior'], c['rate'], c['flux'], c['slope']):
            payload += np.asarray(a, dtype='<f4').tobytes()
    with args.output.open('xb') as stream: stream.write(payload)
    manifest = dict(path=str(args.output.resolve()), sha256=hashlib.sha256(payload).hexdigest(),
        cases=[c['name'] for c in cases], pressure_qualified=False, recorded=recorded,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('export_total_depth_exterior_fixtures.py', 'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py')})
    with args.output.with_suffix('.json').open('x') as stream: json.dump(manifest, stream, indent=2)
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
