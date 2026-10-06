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

- ledge_hole: concentrates `drop_m` of the reach's fall into a step across
  [lateral - width/2, lateral + width/2] (optionally angled): the bed is raised
  by drop/2 upstream and lowered by drop/2 downstream, tapering to nothing over
  `span_m` (30 m) each side, with a `face_length_m` face and a plunge pool under
  it. The surface away from the step keeps its level; the flow goes critical on
  the lip and the jump at the toe is the hole. A crest is never raised above
  1.1 critical depths under the surface.
- drop: the same concentration spread over a chute of `length_m` (a tongue).
- sill: the rock bar at the head of a deep-pool rapid. Across the footprint the
  bed rises to `crest_critical_depths` (1.3) critical depths under the local
  surface over `thickness_m` (6 m) and falls back to the existing bed over
  `face_length_m` (4 m) downstream. The flow goes critical on the bar and runs
  as a jet into the pool below, where it breaks; the pools either side keep
  their bed.
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
                 'constriction', 'drop', 'whitewater_boulders', 'sill')


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

    def __init__(self, bed, cls, ws, st, lat, discharge_m3s, channel_classes=(2, 4), foam=None, wet_extent=None,
                 edit_wet_extent=False):
        self.bed, self.cls, self.ws, self.st, self.lat = bed, cls, ws, st, lat
        self.foam = foam
        self.q_total = float(discharge_m3s)
        self.channel = np.isin(cls, channel_classes) & np.isfinite(ws) & np.isfinite(st) & np.isfinite(lat)
        if edit_wet_extent and wet_extent is not None:
            # water the cook carries over an inferred bank zone is part of the
            # flow a full-width feature must span, or it simply goes round
            self.channel |= wet_extent & np.isfinite(ws) & np.isfinite(st) & np.isfinite(lat)
        # Width and depth statistics use the water the flow actually occupies:
        # a cook can spread two or three times wider than the imaged channel
        # (Pacuare's lower rapids), and a crest sized for the narrow channel's
        # unit discharge sits far too deep to control the flow.
        stat = self.channel if wet_extent is None else (wet_extent & np.isfinite(ws) & np.isfinite(st))
        s = st[stat]
        self.s0 = float(np.floor(s.min())); n = int(np.ceil(s.max()) - self.s0) + 2
        b = np.clip((s - self.s0).astype(int), 0, n - 1)
        # wetted width per metre of station (1 m cells), lightly smoothed
        width = np.bincount(b, minlength=n).astype(float)
        k = np.ones(9) / 9.0
        self.width = np.maximum(np.convolve(width, k, mode='same'), 1.0)
        wsum = np.bincount(b, weights=ws[stat], minlength=n)
        dsum = np.bincount(b, weights=(ws - bed)[stat], minlength=n)
        cnt = np.bincount(b, minlength=n)
        # station metres without a cell (gaps in a builder's station field, the
        # two ends) are interpolated and the ends edge-padded: averaging in
        # zeros there pulled the smoothed surface hundreds of metres down
        have = cnt > 0; idx = np.arange(n)

        def smooth(total):
            mean = np.interp(idx, idx[have], total[have] / cnt[have])
            return np.convolve(np.pad(mean, 4, mode='edge'), k, mode='valid')
        self.ws_s = smooth(wsum)
        self.depth_s = np.maximum(smooth(dsum), 0.2)

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
        if t in ('ledge_hole', 'drop'):
            # Concentrate `drop_m` of the reach's fall into a step (ledge) or a
            # chute of `length_m` (drop): the bed is raised by D/2 upstream and
            # lowered by D/2 downstream, tapering to nothing over `span_m` each
            # side, so the surface away from the feature (and the measured
            # anchors) keeps its level while the feature carries the fall.
            # A ledge also gets a plunge pool under its face.
            drop = float(f['drop_m'])
            face = float(f.get('face_length_m', max(2.0, 1.5 * drop)) if t == 'ledge_hole' else f.get('length_m', 20.0))
            span = float(f.get('span_m', 30.0))
            m = frame.channel & across & (u >= -span) & (u <= face + span)
            ramp_up = _smooth01((u + span) / span)                 # 0 at -span .. 1 at the crest
            ramp_dn = _smooth01((face + span - u) / span)          # 1 at the toe .. 0 at +span
            shift = np.where(u <= 0.0, 0.5 * drop * ramp_up,
                             np.where(u <= face, 0.5 * drop - drop * (u / face), -0.5 * drop * ramp_dn))
            if t == 'ledge_hole':
                pool_len = float(f.get('pool_length_m', max(6.0, 4.0 * drop)))
                pool = float(f.get('pool_depth_m', max(0.5, 0.5 * drop)))
                shift = shift - np.where((u > face) & (u <= face + pool_len),
                                         pool * np.sin(np.pi * np.clip((u - face) / pool_len, 0, 1)), 0.0)
            new = np.where(m, bed + shift * edge, bed)
            # never lift a crest above critical control of the surface over it
            new = np.where(m & (shift > 0), np.minimum(new, frame.ws - 1.1 * hc), new)
            new = np.where(m, np.where(shift > 0, np.maximum(new, bed), np.minimum(new, bed + shift * edge)), bed)
            changed = m & (np.abs(new - bed) > 0.02)
            cls[changed] = CLASS_OBSERVED; bed = new
            rec.update(drop_m=drop, span_m=span, face_length_m=face, cells=int(changed.sum()))
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
        elif t == 'sill':
            thick = float(f.get('thickness_m', 6.0)); face = float(f.get('face_length_m', 4.0))
            crest = _surface_at(frame, s - 3.0, f['lateral_m'], radius=0.5 * max(half, 3.0)) - \
                float(f.get('crest_critical_depths', 1.3)) * hc
            m = frame.channel & across & (u >= -2.0) & (u <= thick + face)
            prof = np.where(u <= thick, _smooth01((u + 2.0) / 2.0), 1.0 - _smooth01((u - thick) / face))
            bed, n = _raise(bed, cls, m, crest, edge * prof)
            rec.update(crest_m=round(crest, 3), cells=n)
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
        report.append(rec)
    return bed, cls, report
