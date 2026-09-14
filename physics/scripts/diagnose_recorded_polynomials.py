"""Compare shoreline decisions with exact rational arithmetic on recorded inputs.

Fractions are a local diagnostic, not a production solver or altered reference.
All arithmetic starts from the represented GPU state/bed, not decimal literals.
"""
import argparse
import json
from fractions import Fraction
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
import audit_live_temporal_evolution as temporal
from audit_recorded_stages import read_records


def exact_slopes(h, bed, y, x, axis):
    ny, nx = h.shape; n = ny if axis == 0 else nx; c = y if axis == 0 else x
    if c == 0 or c == n-1: return Fraction(0), Fraction(0)
    p = (y-1, x) if axis == 0 else (y, x-1)
    q = (y+1, x) if axis == 0 else (y, x+1)
    a, b, c = (Fraction(float(h[t])) for t in (p, (y, x), q))
    if min(a, b, c) <= 0: return Fraction(0), Fraction(0)
    za, zb, zc = (Fraction(float(bed[t])) for t in (p, (y, x), q))
    def mc(back, front):
        if back*front <= 0: return Fraction(0)
        return (1 if back > 0 else -1)*min(abs((back+front)/2), 2*abs(back), 2*abs(front))
    return mc(b-a, c-b), mc((b-a)+(zb-za), (c-b)+(zc-zb))


def exact_face(h, bed, y, x, axis, direction, *, final=False):
    p = (y, x); q = (y+direction, x) if axis == 0 else (y, x+direction)
    if not 0 <= q[0] < h.shape[0] or not 0 <= q[1] < h.shape[1]: q = p
    dh, de = exact_slopes(h, bed, *p, axis); rh, re = exact_slopes(h, bed, *q, axis)
    if final:
        def partial(point):
            return h[point]>0 and (exact_face(h,bed,*point,axis,1)==0 or exact_face(h,bed,*point,axis,-1)==0)
        if partial(p):dh=de=Fraction(0)
        if partial(q):rh=re=Fraction(0)
    d = Fraction(direction, 2); rd = d if q == p else -d
    depth = Fraction(float(h[p]))+d*dh
    jump = Fraction(float(bed[q]))-Fraction(float(bed[p]))+rd*(re-rh)-d*(de-dh)
    return max(Fraction(0), depth-max(Fraction(0), jump))


def diagnose(meta, binary, source, index, stage):
    trial, stages, *_ = list(read_records(meta, binary))[index]
    gpu = stages[stage]; i = trial['interval']
    a, b = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1', first=source['observations'][i], second=source['observations'][i+1]))
    _, boundary = temporal.boundary_provider(a, b)
    es, eb, _ = boundary(trial['begin']-a['native_seconds']+(trial['attempted_dt'] if stage else 0), None)
    state = gpu['state'][..., :3].astype(float); bed = a['bed']; h = state[..., 0]
    hydro, _ = bank.rate(state, bed, .5, second_order=True, exterior=(es, eb))
    error = abs(hydro-gpu['rate'][..., :3]); worst = np.unravel_index(error.argmax(), error.shape)
    y0, x0 = map(int, worst[:2]); decisions = []; gpu_polynomials = []
    for axis, label in ((0, 'y'), (1, 'x')):
        if 'raw_'+label not in gpu: continue
        raw, final = gpu['raw_'+label], gpu['slope_'+label]
        for y in range(max(0, y0-2), min(h.shape[0], y0+3)):
            for x in range(max(0, x0-2), min(h.shape[1], x0+3)):
                ep, en = exact_face(h, bed, y, x, axis, 1), exact_face(h, bed, y, x, axis, -1)
                dh, de = exact_slopes(h, bed, y, x, axis)
                flattened = np.any(raw[y, x] != 0) and np.all(final[y, x] == 0)
                gpu_polynomials.append(dict(axis=axis, y=y, x=x, h=float(h[y, x]), bed=float(bed[y, x]),
                    raw=raw[y, x].tolist(), final=final[y, x].tolist(), exact_dh=float(dh), exact_deta=float(de),
                    exact_positive=float(ep), exact_negative=float(en), flattened=bool(flattened),
                    exact_flatten=bool(h[y, x]>0 and (ep==0 or en==0))))
    for dtype in (np.float32, np.float64):
        hh, zz = h.astype(dtype), bed.astype(dtype)
        for axis in (0, 1):
            dh = bank.mc(hh, axis, False); de = bank.mc(hh, axis, False, other=zz)
            wet = (hh>0)&(np.roll(hh, 1, axis)>0)&(np.roll(hh, -1, axis)>0)
            dh *= wet; de *= wet
            *_, left, right = bank.hydrostatic_faces(hh, zz, dh, de, axis, False, (es.astype(dtype), eb.astype(dtype)))
            pos = np.take(left, range(1, left.shape[axis]), axis=axis)
            neg = np.take(right, range(right.shape[axis]-1), axis=axis)
            for y in range(max(0, y0-2), min(h.shape[0], y0+3)):
                for x in range(max(0, x0-2), min(h.shape[1], x0+3)):
                    ep, en = exact_face(h, bed, y, x, axis, 1), exact_face(h, bed, y, x, axis, -1)
                    flatten = h[y, x]>0 and (pos[y, x]==0 or neg[y, x]==0)
                    exact_flatten = h[y, x]>0 and (ep==0 or en==0)
                    if flatten != exact_flatten:
                        decisions.append(dict(dtype=np.dtype(dtype).name, axis=axis, y=y, x=x, h=float(h[y, x]),
                            dh=float(dh[y, x]), deta=float(de[y, x]), positive=float(pos[y, x]), negative=float(neg[y, x]),
                            exact_positive=float(ep), exact_negative=float(en), flatten=bool(flatten), exact_flatten=bool(exact_flatten)))
    return dict(scope=__doc__, index=index, stage=stage, trial=trial, worst_yxc=list(map(int, worst)),
                maximum_hydro_error=float(error.max()), gpu_rate=float(gpu['rate'][worst]), cpu_rate=float(hydro[worst]),
                decisions=decisions, gpu_polynomials=gpu_polynomials)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path); parser.add_argument('--record', type=int, required=True)
    parser.add_argument('--stage', type=int, choices=(0, 1), required=True); parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    meta = json.loads(args.trace.read_text())
    report = diagnose(meta, Path(meta['binary']).read_bytes(), json.loads(Path(meta['source']).read_text()), args.record, args.stage)
    serialized = json.dumps(report, indent=2, allow_nan=False)
    with args.report.open('x') as stream: stream.write(serialized)
    print(serialized)


if __name__ == '__main__': main()
