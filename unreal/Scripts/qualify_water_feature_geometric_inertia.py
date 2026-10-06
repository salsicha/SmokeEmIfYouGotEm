"""Independent actual-solid volume and cached-liquid boundary verification.

Imports no volume/centroid/liquid-bound construction helpers. Independent
Gaussian-column union and explicit cached-center interpolation are used.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import time
import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class Reference:
    def __init__(self, meshes):
        self.boxes = []; self.bed = None
        for entry in meshes:
            v = np.load(entry['vertices'], allow_pickle=False); t = np.load(entry['triangles'], allow_pickle=False)
            if hashlib.sha256(v.tobytes()+t.tobytes()).hexdigest() != entry['geometry_sha256']:
                raise ValueError('Actual mesh fingerprint mismatch')
            a, b = v.min(0), v.max(0)
            if entry['name'] != 'Obstacle approach bed':
                if len(v) != 8 or len(t) != 12 or len(np.unique(v, axis=0)) != 8 or not np.all((v == a) | (v == b)):
                    raise ValueError('Actual reference box unsupported')
                self.boxes.append((a, b))
            else:
                xs = np.unique(v[:, 0]); top = np.array([v[v[:, 0] == x, 2].max() for x in xs])
                if len(v) != 4*len(xs) or not np.all((v[:, 1] == a[1]) | (v[:, 1] == b[1])):
                    raise ValueError('Actual reference roof unsupported')
                for x, z in zip(xs, top):
                    expected = set(itertools.product([x], [a[1], b[1]], [a[2], z]))
                    if set(map(tuple, v[v[:, 0] == x])) != expected:
                        raise ValueError('Actual roof extrusion corner mismatch')
                self.bed = xs, top, a, b
        if len(self.boxes) != 7 or self.bed is None:
            raise ValueError('Complete unchanged eight-solid laboratory required')
        self.q, self.w = np.polynomial.legendre.leggauss(2)

    def integrate(self, lower, upper):
        a, b = np.array(lower), np.array(upper); boxes = [x for x in self.boxes if np.all(x[1] > a) and np.all(x[0] < b)]
        xs, top, ba, bb = self.bed; bed = np.all(bb > a) and np.all(ba < b)
        if not boxes and not bed:
            volume = float(np.prod(b-a)); return volume, volume*(a+b)/2
        ex = {a[0], b[0]}; ey = {a[1], b[1]}
        for lo, hi in boxes:
            ex.update(z for z in (lo[0], hi[0]) if a[0] < z < b[0])
            ey.update(z for z in (lo[1], hi[1]) if a[1] < z < b[1])
        if bed:
            ex.update(x for x in xs if a[0] < x < b[0]); ey.update(y for y in (ba[1], bb[1]) if a[1] < y < b[1])
            # Gaussian integration must split every roof/constant-z crossing.
            heights = {a[2], b[2], *[float(z) for box in boxes for z in (box[0][2], box[1][2])]}
            for x0, x1, z0, z1 in zip(xs, xs[1:], top, top[1:]):
                if z1 != z0:
                    for z in heights:
                        u = (z-z0)/(z1-z0)
                        if 0 < u < 1:
                            x = x0+(x1-x0)*u
                            if a[0] < x < b[0]:
                                ex.add(x)
        ex, ey = sorted(ex), sorted(ey); volume = 0.; moment = np.zeros(3)
        for x0, x1 in zip(ex, ex[1:]):
            for y0, y1 in zip(ey, ey[1:]):
                fixed = [(lo[2], hi[2]) for lo, hi in boxes if lo[0] <= x0 and hi[0] >= x1 and lo[1] <= y0 and hi[1] >= y1]
                roof_present = bed and ba[0] <= x0 and bb[0] >= x1 and ba[1] <= y0 and bb[1] >= y1
                for q, w in zip(self.q, self.w):
                    x = x0+(x1-x0)*(q+1)/2; intervals = list(fixed)
                    if roof_present:
                        intervals.append((ba[2], float(np.interp(x, xs, top))))
                    ends = sorted({a[2], b[2], *[max(a[2], min(b[2], z)) for pair in intervals for z in pair]})
                    length = mz = 0.
                    for z0, z1 in zip(ends, ends[1:]):
                        if z1 > z0 and not any(lo <= z0 and hi >= z1 for lo, hi in intervals):
                            length += z1-z0; mz += (z1-z0)*(z1+z0)/2
                    factor = w*(x1-x0)/2*(y1-y0); v = factor*length
                    volume += v; moment += [v*x, v*(y0+y1)/2, factor*mz]
        return float(volume), moment


def field_value(phi, p, origin, h):
    xyz = np.clip((np.asarray(p)-origin)/h-.5, 0., np.array(phi.shape)-1)
    low = np.floor(xyz).astype(int); high = np.minimum(low+1, np.array(phi.shape)-1); d = xyz-low
    result = 0.
    for bits in itertools.product((0, 1), repeat=3):
        bits = np.array(bits); index = np.where(bits, high, low)
        result += float(phi[tuple(index)])*float(np.prod(np.where(bits, d, 1-d)))
    return result


def reference_liquid(ref, phi, origin, h, lo, hi, depth, guard):
    events = []
    for axis in range(3):
        centers = origin[axis]+(np.arange(phi.shape[axis])+.5)*h
        events.append(sorted({lo[axis], hi[axis], *centers[(centers > lo[axis]) & (centers < hi[axis])]}))
    lower = upper = 0.; bits = list(itertools.product((0, 1), repeat=3))
    pending = []
    for ix in itertools.product(*(range(len(e)-1) for e in events)):
        pending.append((np.array([events[a][ix[a]] for a in range(3)]),
                        np.array([events[a][ix[a]+1] for a in range(3)]), 0))
    while pending:
        a, b, n = pending.pop(); vol, _ = ref.integrate(a, b)
        if vol == 0:
            continue
        values = [field_value(phi, np.where(bit, b, a), origin, h) for bit in bits]
        if max(values) < -guard:
            lower += vol; upper += vol
        elif min(values) > guard:
            continue
        elif n == depth:
            upper += vol
        else:
            mid = a+(b-a)/2
            if np.any((mid == a) | (mid == b)):
                upper += vol
            else:
                pending.extend((np.where(bit, mid, a), np.where(bit, b, mid), n+1) for bit in bits)
    return lower, upper


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    audit = json.loads(args.audit.read_text()); inp = json.loads(args.inputs.read_text()); hashes = {}
    for r, path in ((audit, args.audit), (inp, args.inputs)):
        for p, sha in {**r['dependency_sha256'], **r['outputs_sha256']}.items():
            if p in hashes and hashes[p] != sha:
                raise ValueError('Conflicting evidence versions')
            hashes[p] = sha
        hashes[str(path.resolve())] = digest(path)
    hashes[str(Path(__file__).resolve())] = digest(__file__)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned evidence changed')
    ref = Reference(inp['meshes']); shape = tuple(inp['shape']); origin = np.array(inp['origin_m']); h = inp['cell_m']
    volumes = np.load(audit['arrays']['open-cell-volume-m3'], allow_pickle=False)
    moments = np.load(audit['arrays']['open-cell-first-moment-m4'], allow_pickle=False)
    phi = np.load(inp['fields']['phi'], allow_pickle=False); vmax = mmax = 0.; started = time.perf_counter()
    for i in range(shape[0]):
        for j in range(shape[1]):
            for k in range(shape[2]):
                index = (i, j, k); lo = origin+np.array(index)*h; hi = lo+h
                v, m = ref.integrate(lo, hi); vmax = max(vmax, abs(v-volumes[index])); mmax = max(mmax, float(np.max(np.abs(m-moments[index]))))
        if i % 15 == 0:
            print('INDEPENDENT_CELL_VOLUME', i, vmax, mmax, flush=True)
    if vmax > 2e-14 or mmax > 2e-13:
        raise ValueError('Independent Gaussian-column geometry differs beyond fixed allowance')
    cells_seconds = time.perf_counter()-started; verified_bounds = 0; summaries = []
    for row in audit['face_rows']:
        center = np.array(row['face_world_m']); regions = [(center-.5*h, center+.5*h, row['liquid_dual_bounds'])]
        for cell in row['neighbors']:
            lo = origin+np.array(cell['index'])*h; regions.append((lo, lo+h, cell['liquid_bounds']))
            centroid = np.array(cell['open_centroid_m'])
            if abs(field_value(phi, centroid, origin, h)-cell['cached_phi_at_open_centroid']) > 1e-12:
                raise ValueError('Independent open-centroid liquid interpolation mismatch')
        for lo, hi, bounds in regions:
            for b in bounds:
                lower, upper = reference_liquid(ref, phi, origin, h, lo, hi, b['depth'], b['sign_guard'])
                if max(abs(lower-b['lower_m3']), abs(upper-b['upper_m3'])) > 2e-14:
                    raise ValueError('Independent liquid/geometric-volume bound mismatch')
                verified_bounds += 1
        last = row['liquid_dual_bounds'][-1]; volume = row['open_dual_volume_m3']
        summaries.append(dict(index=row['index'], velocity_m_per_second=row['velocity_m_per_second'],
            liquid_dual_fraction_bounds=[last['lower_m3']/volume, last['upper_m3']/volume],
            response_coefficient=row['response_coefficient']))
    minimum = audit['geometric_fluid_cohort']['minimum_positive_index']; lo = origin+np.array(minimum)*h
    minimum_v, _ = ref.integrate(lo, lo+h)
    minimum_liquid = []
    for depth in (1, 2, 3):
        lower, upper = reference_liquid(ref, phi, origin, h, lo, lo+h, depth, 1e-12)
        minimum_liquid.append(dict(depth=depth, lower_m3=lower, upper_m3=upper))
    result = dict(complete=True, accepted=False, originals_unchanged=True, independently_checked_cells=int(volumes.size),
        maximum_volume_error_m3=vmax, maximum_first_moment_error_m4=mmax,
        fixed_volume_allowance_m3=2e-14, fixed_moment_allowance_m4=2e-13,
        independent_cell_seconds=cells_seconds, independently_checked_liquid_bounds=verified_bounds,
        face_summaries=summaries, minimum_open_cell=dict(index=minimum, reference_open_volume_m3=minimum_v,
            liquid_bounds=minimum_liquid), dependency_sha256=hashes,
        scope='Independent actual laboratory open volumes, first moments and cached-liquid bounds. No liquid/contact/pressure update, accepted physical step or animation.')
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Qualification changed preserved evidence')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print('GEOMETRIC_INERTIA_QUALIFIED', int(volumes.size), vmax, mmax, verified_bounds, summaries, flush=True)


if __name__ == '__main__':
    main()
