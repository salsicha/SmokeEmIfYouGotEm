"""Rapid features reconstructed from observations, imprinted on an evidence grid (numpy only).

None of the evidence reaches has bathymetry inside its rapids, and a smooth
discharge-consistent bed cannot place their holes, waves and diagonals. Each
reach therefore carries a catalogue of the whitewater that is observed there
(Sentinel-2 or orthophoto whitewater, outfitter and guidebook descriptions,
video): <reach>_observed_rapid_features.json. This module turns every catalogued
feature into a bed shape so that the shallow-water solver forms the feature
itself, and the raft meets it, instead of a painted-on foam patch.

Frame: the evidence grid's own station/lateral fields (station downstream along
its midline, lateral positive to river left). A feature is placed by station and
lateral offset and is sized from the reference water surface and the local unit
discharge, so it survives changes to the inferred bed around it:

- ledge_hole: a sill across [lateral - width/2, lateral + width/2] (optionally
  angled) whose crest sits `crest_depth_m` under the upstream reference surface
  (default 1.2 critical depths, so the flow goes critical on the crest), a steep
  face and a plunge pool `drop_m` + `pool_depth_m` below the crest. The
  hydraulic jump at the toe is the hole.
- pour_over / boulder: a mound (cos^2 plan shape, elongated downstream) with its
  crest `crest_below_ws_m` under the surface (negative = emergent rock).
- rock_garden: `count` deterministic boulders inside the footprint.
- wave_train: `waves` bed ridges at `wavelength_m` (default the standing-wave
  length 2 pi U^2 / g for near-critical flow, U^2 ~ g hc, at least 6 m) and
  amplitude `amplitude_m` across the footprint.
- lateral / diagonal: an oblique rib from `side` at `angle_deg` to the flow,
  crest `crest_below_ws_m` under the surface: an oblique jump in fast water.
- constriction: raises the bed of the outer parts of the channel to the surface
  so the flowing width narrows to `open_width_m` over the footprint.
- drop: steepens the bed so the surface falls `drop_m` over `length_m` (a tongue).
- whitewater_boulders: a boulder garden placed by the imagery itself. Inside
  the footprint (`length_m` x `width_m`) every photographed whitewater patch
  (the evidence grid's foam mask) of at least `min_patch_m2` gets a pour-over
  on its upstream edge, radius clip(patch width / 2, `radius_m`), crest
  `crest_below_ws_m` under the surface. Whitewater forms just downstream of
  an obstacle, so the photograph locates the rocks.

Crest heights are set against the frame's water surface. By default that is
the evidence reference surface; pass the previous cook's surface
(imprint_observed_rapids.py --surface-from) so crests are placed against the
water the solver actually carries: the reference can sit 0.5-0.9 m under the
cooked surface in a rapid (Pacuare), which drowns every feature.

Every changed cell gets class 5 ("bed shape reconstructed from observations,
inferred"). The catalogue records, per feature, its observation sources; the
imprint report records what was applied. Shapes, heights and positions are
approximations of what is observed, not measurements.
"""
import json
from pathlib import Path

import numpy as np

G = 9.81
CLASS_OBSERVED = 5
FEATURE_TYPES = ('ledge_hole', 'pour_over', 'boulder', 'rock_garden', 'wave_train', 'lateral', 'diagonal',
                 'constriction', 'drop', 'whitewater_boulders')


def load_catalogue(path):
    cat = json.loads(Path(path).read_text())
    assert cat.get('schema') == 'raftsim.observed_rapid_features.v1', 'unexpected catalogue schema'
    for f in cat['features']:
        assert f['type'] in FEATURE_TYPES, f['type']
        assert f.get('sources'), 'every feature needs its observation sources: ' + f['id']
    return cat


def _smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


class Frame:
    """Station/lateral helpers over one evidence grid (1 m cells)."""

    def __init__(self, bed, cls, ws, st, lat, discharge_m3s, channel_classes=(2, 4), foam=None):
        self.bed, self.cls, self.ws, self.st, self.lat = bed, cls, ws, st, lat
        self.foam = foam
        self.q_total = float(discharge_m3s)
        self.channel = np.isin(cls, channel_classes) & np.isfinite(ws) & np.isfinite(st) & np.isfinite(lat)
        s = st[self.channel]
        self.s0 = float(np.floor(s.min())); n = int(np.ceil(s.max()) - self.s0) + 2
        b = np.clip((s - self.s0).astype(int), 0, n - 1)
        # wetted width per metre of station (1 m cells), lightly smoothed
        width = np.bincount(b, minlength=n).astype(float)
        k = np.ones(9) / 9.0
        self.width = np.maximum(np.convolve(width, k, mode='same'), 1.0)
        wsum = np.bincount(b, weights=ws[self.channel], minlength=n)
        dsum = np.bincount(b, weights=(ws - bed)[self.channel], minlength=n)
        cnt = np.maximum(np.bincount(b, minlength=n), 1)
        self.ws_s = np.convolve(wsum / cnt, k, mode='same')
        self.depth_s = np.maximum(np.convolve(dsum / cnt, k, mode='same'), 0.2)

    def at(self, arr, s):
        i = np.clip((np.asarray(s, float) - self.s0).astype(int), 0, len(arr) - 1)
        return arr[i]

    def unit_q(self, s):
        return self.q_total / self.at(self.width, s)

    def critical_depth(self, s):
        return (self.unit_q(s) ** 2 / G) ** (1.0 / 3.0)

    def velocity(self, s):
        return self.unit_q(s) / self.at(self.depth_s, s)

    def ws_ref(self, s):
        return self.at(self.ws_s, s)


def _local(frame, f):
    """Along-feature (u, downstream from the crest line) and across (v, from its centre) coordinates."""
    st, lat = frame.st, frame.lat
    ang = np.radians(f.get('angle_deg', 0.0))
    v = lat - f['lateral_m']
    u = st - (f['station_m'] + v * np.tan(ang))
    return u, v


def _raise(bed, cls, mask, target, weight):
    new = np.where(mask, np.maximum(bed, bed + (target - bed) * weight), bed)
    changed = mask & (new > bed + 0.02)
    cls[changed] = CLASS_OBSERVED
    return new, int(changed.sum())


def _lower(bed, cls, mask, target, weight):
    new = np.where(mask, np.minimum(bed, bed + (target - bed) * weight), bed)
    changed = mask & (new < bed - 0.02)
    cls[changed] = CLASS_OBSERVED
    return new, int(changed.sum())


def _surface_at(frame, s, l, radius=3.0):
    """Median frame surface within `radius` of (station, lateral); the station mean where none."""
    m = frame.channel & (np.abs(frame.st - s) <= radius) & (np.abs(frame.lat - l) <= radius)
    return float(np.median(frame.ws[m])) if m.any() else float(frame.ws_ref(s))


def _components(mask):
    from collections import deque
    H, W = mask.shape
    lab = -np.ones((H, W), int); comps = []
    for r0, c0 in zip(*np.nonzero(mask)):
        if lab[r0, c0] >= 0:
            continue
        q = deque([(r0, c0)]); lab[r0, c0] = len(comps); pix = []
        while q:
            r, c = q.popleft(); pix.append((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    r2, c2 = r + dr, c + dc
                    if 0 <= r2 < H and 0 <= c2 < W and mask[r2, c2] and lab[r2, c2] < 0:
                        lab[r2, c2] = len(comps); q.append((r2, c2))
        comps.append(np.array(pix))
    return comps


def _mound(frame, bed, cls, cx_s, cx_l, radius_across, radius_along, crest):
    st, lat = frame.st, frame.lat
    d = np.sqrt(((st - cx_s) / radius_along) ** 2 + ((lat - cx_l) / radius_across) ** 2)
    w = np.where(d < 1.0, np.cos(0.5 * np.pi * d) ** 2, 0.0)
    m = frame.channel & (w > 0)
    return _raise(bed, cls, m, crest, w)


def imprint(frame, features, seed=20260929):
    """Apply every catalogued feature in order; returns (bed, cls, report)."""
    bed = frame.bed.copy(); cls = frame.cls.copy()
    rng = np.random.default_rng(seed)
    report = []
    for f in features:
        t = f['type']; s = f['station_m']; half = 0.5 * f.get('width_m', 10.0)
        hc = float(frame.critical_depth(s)); ws_up = float(frame.ws_ref(s - 2.0))
        rec = dict(id=f['id'], type=t, station_m=s, lateral_m=f['lateral_m'], critical_depth_m=round(hc, 3),
                   unit_discharge_m2s=round(float(frame.unit_q(s)), 3), reference_surface_m=round(ws_up, 3))
        u, v = _local(frame, f)
        across = np.abs(v) <= half
        edge = _smooth01((half - np.abs(v)) / max(min(2.0, half), 0.5))
        if t == 'ledge_hole':
            drop = float(f['drop_m'])
            crest = ws_up - float(f.get('crest_depth_m', 1.2 * hc))
            face = float(f.get('face_length_m', max(2.0, 1.5 * drop)))
            approach = float(f.get('approach_length_m', 8.0))
            pool_len = float(f.get('pool_length_m', max(8.0, 6.0 * drop)))
            toe = crest - drop - float(f.get('pool_depth_m', max(1.0, 0.8 * drop)))
            up = frame.channel & across & (u >= -approach) & (u <= 0.0)
            bed, n1 = _raise(bed, cls, up, crest, edge * _smooth01((u + approach) / approach))
            fc = frame.channel & across & (u > 0.0) & (u <= face)
            bed, n2 = _raise(bed, cls, fc, crest - drop * (u / face), edge)
            bed, n2b = _lower(bed, cls, fc, crest - drop * (u / face), edge)
            pl = frame.channel & across & (u > face) & (u <= face + pool_len)
            bed, n3 = _lower(bed, cls, pl, toe, edge * _smooth01((face + pool_len - u) / (0.5 * pool_len)))
            rec.update(crest_m=round(crest, 3), drop_m=drop, toe_m=round(toe, 3), cells=n1 + n2 + n2b + n3)
        elif t in ('pour_over', 'boulder'):
            crest = _surface_at(frame, s, f['lateral_m']) - float(f.get('crest_below_ws_m', 0.3 if t == 'pour_over' else -0.5))
            bed, n = _mound(frame, bed, cls, s, f['lateral_m'], half, float(f.get('length_m', 2.0 * half)) / 2.0, crest)
            rec.update(crest_m=round(crest, 3), cells=n)
        elif t == 'rock_garden':
            count = int(f.get('count', 8)); length = float(f.get('length_m', 30.0))
            rmin, rmax = f.get('boulder_radius_m', [1.0, 2.5])
            below = f.get('crest_below_ws_m', [-0.3, 0.6])
            n = 0; placed = []
            for _ in range(count * 20):
                if len(placed) >= count:
                    break
                ps = s + rng.uniform(0.0, length); pl = f['lateral_m'] + rng.uniform(-half, half)
                r = rng.uniform(rmin, rmax)
                if any((ps - a) ** 2 + (pl - b) ** 2 < (r + c + 1.0) ** 2 for a, b, c in placed):
                    continue
                crest = _surface_at(frame, ps, pl) - rng.uniform(*below)
                bed, k = _mound(frame, bed, cls, ps, pl, r, 1.3 * r, crest)
                if k:
                    placed.append((ps, pl, r)); n += k
            rec.update(boulders=len(placed), cells=n)
        elif t == 'wave_train':
            # Standing waves in a rapid ride near-critical flow (U^2 ~ g hc), so
            # the default length is 2 pi hc unless the reach-mean velocity is
            # faster; never under three 2 m solver cells per half wave.
            U = float(frame.velocity(s))
            lam = float(f.get('wavelength_m', max(2.0 * np.pi * U * U / G, 2.0 * np.pi * hc, 6.0)))
            waves = int(f.get('waves', 4)); amp = float(f.get('amplitude_m', 0.5))
            length = waves * lam
            m = frame.channel & across & (u >= 0.0) & (u <= length)
            taper = _smooth01(u / lam) * _smooth01((length - u) / lam) * edge
            ridge = amp * np.maximum(np.sin(2.0 * np.pi * u / lam), 0.0) * taper
            # ridges only: raise the bed under each crest, capped under the surface
            cap = frame.ws - 0.6 * hc
            bed, n = _raise(bed, cls, m & (ridge > 0.02), np.minimum(bed + ridge, cap), 1.0)
            rec.update(wavelength_m=round(lam, 2), waves=waves, amplitude_m=amp, velocity_mps=round(U, 2), cells=n)
        elif t in ('lateral', 'diagonal'):
            # oblique rib: angle_deg is the rib's angle to the cross-section
            crest = ws_up - float(f.get('crest_below_ws_m', 0.4))
            thick = float(f.get('thickness_m', 3.0))
            rib = frame.channel & across & (np.abs(u) <= 0.5 * thick)
            bed, n = _raise(bed, cls, rib, crest, edge * _smooth01((0.5 * thick - np.abs(u)) / (0.25 * thick)))
            rec.update(crest_m=round(crest, 3), cells=n)
        elif t == 'constriction':
            length = float(f.get('length_m', 30.0)); open_half = 0.5 * float(f['open_width_m'])
            crest = ws_up + float(f.get('crest_above_ws_m', 0.3))
            m = frame.channel & (u >= 0.0) & (u <= length) & (np.abs(v) > open_half)
            ramp = _smooth01((np.abs(v) - open_half) / 3.0) * _smooth01(u / 5.0) * _smooth01((length - u) / 5.0)
            bed, n = _raise(bed, cls, m, crest, ramp)
            rec.update(open_width_m=2 * open_half, cells=n)
        elif t == 'whitewater_boulders':
            assert frame.foam is not None, 'whitewater_boulders needs the evidence foam mask'
            length = float(f.get('length_m', 50.0))
            rmin, rmax = f.get('radius_m', [2.5, 4.0])
            below = float(f.get('crest_below_ws_m', 0.15))
            min_patch = int(f.get('min_patch_m2', 6))
            box = frame.channel & (u >= 0.0) & (u <= length) & across
            n = 0; placed = []
            for pix in sorted((p for p in _components(frame.foam & box) if len(p) >= min_patch), key=len, reverse=True):
                ps_all = frame.st[pix[:, 0], pix[:, 1]]; pl_all = frame.lat[pix[:, 0], pix[:, 1]]
                width = float(pl_all.max() - pl_all.min() + 1.0)
                r = float(np.clip(0.5 * width, rmin, rmax))
                # the rock sits just upstream of the patch's upstream edge
                ps = float(ps_all.min()) - 0.5 * r
                pl = float(np.median(pl_all[ps_all <= ps_all.min() + 2.0]))
                if any((ps - a) ** 2 + (pl - b) ** 2 < (r + c) ** 2 for a, b, c in placed):
                    continue
                crest = _surface_at(frame, ps, pl) - below
                bed, k = _mound(frame, bed, cls, ps, pl, r, 1.3 * r, crest)
                if k:
                    placed.append((ps, pl, r)); n += k
            rec.update(boulders=len(placed), cells=n, placed=[dict(station_m=round(a, 1), lateral_m=round(b, 1), radius_m=round(c, 2))
                                                             for a, b, c in placed])
        elif t == 'drop':
            length = float(f.get('length_m', 20.0)); drop = float(f['drop_m'])
            m = frame.channel & across & (u >= 0.0) & (u <= length)
            depth = float(frame.at(frame.depth_s, s))
            target = ws_up - depth - drop * (u / length)
            bed, n1 = _raise(bed, cls, m, target, edge)
            rec.update(drop_m=drop, cells=n1)
        report.append(rec)
    return bed, cls, report
