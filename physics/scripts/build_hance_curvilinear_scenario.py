"""Hance Rapid solver scenario on a curvilinear station/lateral grid (numpy only).

Input: the evidence grid from build_hance_evidence_grid.py (EPSG:6404 metres,
NAD83(2011) ellipsoid heights). Output: a raftsim.scenario2_5d.v0 package on a
2 m station (x, downstream) by lateral (y, river-left) grid, plus the matching
raftsim.curved_river_coordinate_map.v1 and a reference file for comparing a
cook with the 2021 surface.

Centreline: the evidence centreline (column means of the channel) is too noisy
for a curvilinear grid (radii down to 31 m), so it is Gaussian-smoothed until
its tightest radius is at least --min-radius-m and re-parametrised by arc
length at exactly 2 m. Station 0 is the upstream (east) end of the grid.

World/local frame: local = EPSG:6404 minus --origin (metres east, north).
The coordinate map declares world_y_sign -1 (ENU: north is camera-left for a
+X camera in Unreal). Heights stay NAD83(2011) ellipsoid heights; the map's
vertical_datum_m is subtracted at the Unreal boundary only.

Bed per 2 m cell: mean of four bilinear samples of the evidence bed at
+-0.5 m in the station/lateral frame. Its class (measured / inferred /
emergent rock / dry DEM) is the nearest evidence cell's.

Initial water: the 2021 reference surface WS(s) in channel cells, conveyance
velocity along the station axis. Upstream boundary: discharge_profile with
Q = 226.534772736 m3/s (8,000 cfs, the 2021 flight flow) distributed by
h^(5/3); downstream: outflow at the reference stage; sides: bank.

The solver has no metric terms: the grid is treated as Cartesian, so cells at
lateral n are (1 - kappa n) too long or short on bends. The script reports the
worst ratio over wet cells.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / 'physics/data/real_world/colorado_river_grand_canyon_rowing/scenario_hance/low_release_planning/scenario.json'
X0, Y1, NX, NY = 211300.0, 560300.0, 2500, 1212
Q = 226.534772736
DS = 2.0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gauss_smooth(v, sigma):
    """Gaussian smoothing with linear-trend padding (no end shrinkage)."""
    r = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    head = v[0] + (v[0] - v[min(r, len(v) - 1)]) * np.arange(r, 0, -1) / r
    tail = v[-1] + (v[-1] - v[max(-r - 1, -len(v))]) * np.arange(1, r + 1) / r
    return np.convolve(np.concatenate([head, v, tail]), k, mode='valid')


def arc_resample(x, y, step):
    s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
    n = int(np.floor(s[-1] / step)) + 1
    t = np.arange(n) * step
    return np.interp(t, s, x), np.interp(t, s, y), t


def curvature(x, y):
    dx, dy = np.gradient(x), np.gradient(y)
    ddx, ddy = np.gradient(dx), np.gradient(dy)
    return (dx * ddy - dy * ddx) / np.maximum((dx * dx + dy * dy) ** 1.5, 1e-12)


def bilinear(a, ex, ny_):
    """Sample a 1 m evidence array at EPSG:6404 points (cell centres at +0.5)."""
    cf = ex - X0 - 0.5; rf = Y1 - ny_ - 0.5
    c = np.clip(np.floor(cf).astype(int), 0, NX - 2); r = np.clip(np.floor(rf).astype(int), 0, NY - 2)
    u = np.clip(cf - c, 0, 1); v = np.clip(rf - r, 0, 1)
    return (a[r, c] * (1 - u) * (1 - v) + a[r, c + 1] * u * (1 - v) + a[r + 1, c] * (1 - u) * v + a[r + 1, c + 1] * u * v)


def nearest(a, ex, ny_):
    c = np.clip(np.floor(ex - X0).astype(int), 0, NX - 1); r = np.clip(np.floor(Y1 - ny_).astype(int), 0, NY - 1)
    return a[r, c]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('evidence', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--min-radius-m', type=float, default=250.0)
    ap.add_argument('--half-width-m', type=float, default=0.0, help='0: channel extent + margin')
    ap.add_argument('--bank-margin-m', type=float, default=12.0)
    ap.add_argument('--roughness', type=float, default=0.058)
    ap.add_argument('--origin', type=float, nargs=2, default=(211300.0, 559694.0),
                    help='local frame origin: west edge and north-south centre of the evidence window (Landscape frame)')
    ap.add_argument('--vertical-datum-m', type=float, default=740.0)
    ap.add_argument('--outflow-stage', choices=('ws_reference', 'dem_water_median'), default='ws_reference',
                    help='the DEM over calm clear water reads low (metadata: less accurate on water)')
    ap.add_argument('--trim-m', type=float, default=30.0, help='keep the grid this far inside the evidence window')
    args = ap.parse_args()
    out = args.output.resolve()
    assert not out.exists(), 'fresh output required'
    ev = args.evidence.resolve()
    g = np.load(ev / 'evidence_grid.npz')
    bed1, dem1, cls1 = g['bed'].astype(np.float64), g['dem2021'].astype(np.float64), g['class_code']
    river1, channel1 = g['river'], g['channel']
    prof = json.loads((ev / 'profile.json').read_text())
    cl = np.array(json.loads((ev / 'centreline.json').read_text())['points_xy_station'])
    cl = cl[np.argsort(cl[:, 2])]  # upstream (east) first
    old_x, old_y, old_s = cl[:, 0], cl[:, 1], cl[:, 2]

    # --- smooth centreline until the tightest radius is acceptable
    x, y, _ = arc_resample(old_x, old_y, DS)
    sigma = 5.0
    while True:
        xs, ys = gauss_smooth(x, sigma), gauss_smooth(y, sigma)
        xs, ys, st = arc_resample(xs, ys, DS)
        k = curvature(xs, ys) / DS
        if 1 / np.max(np.abs(k[5:-5])) >= args.min_radius_m or sigma > 400:
            break
        sigma *= 1.25
    # --- trim to the evidence window
    tx, ty = np.gradient(xs), np.gradient(ys)
    tn = np.hypot(tx, ty); tx, ty = tx / tn, ty / tn
    lx, ly = -ty, tx  # river-left
    # channel extent per station (project channel cells on the smoothed line)
    rr, cc = np.nonzero(channel1)
    ex, ey = X0 + cc + 0.5, Y1 - rr - 0.5
    best = np.full(len(rr), np.inf); bi = np.zeros(len(rr), int)
    for j0 in range(0, len(xs), 64):
        j1 = min(len(xs), j0 + 64)
        d2 = (ex[:, None] - xs[None, j0:j1]) ** 2 + (ey[:, None] - ys[None, j0:j1]) ** 2
        jj = np.argmin(d2, 1); dd = d2[np.arange(len(rr)), jj]
        u = dd < best; best[u] = dd[u]; bi[u] = j0 + jj[u]
    lat = (ex - xs[bi]) * lx[bi] + (ey - ys[bi]) * ly[bi]
    need = float(np.max(np.abs(lat))) + args.bank_margin_m
    half = args.half_width_m or float(np.ceil(need / DS) * DS)
    ncell = int(round(half / DS))
    lats = np.arange(-ncell, ncell + 1) * DS
    px = xs[:, None] + lats[None, :] * lx[:, None]
    py = ys[:, None] + lats[None, :] * ly[:, None]
    m = args.trim_m
    inside = np.all((px > X0 + m) & (px < X0 + NX - m) & (py > Y1 - NY + m) & (py < Y1 - m), axis=1)
    idx = np.nonzero(inside)[0]
    a, b = idx[0], idx[-1]
    assert np.all(inside[a:b + 1]), 'window exits and re-enters'
    sel = slice(a, b + 1)
    xs, ys, lx, ly, tx, ty, px, py = xs[sel], ys[sel], lx[sel], ly[sel], tx[sel], ty[sel], px[sel], py[sel]
    k = curvature(xs, ys) / DS
    nst = len(xs)
    station = np.arange(nst) * DS
    # map each new station to the evidence station (nearest old centreline point)
    j = np.array([np.argmin((old_x - X) ** 2 + (old_y - Y) ** 2) for X, Y in zip(xs, ys)])
    ev_station = old_s[j]
    ws_ref = np.interp(ev_station, prof['station_center_m'], prof['ws_reference_m'])
    # --- sample fields at 2 m cells (box of four bilinear samples)
    bed = np.zeros((nst, len(lats))); dem = np.zeros_like(bed)
    for o_s in (-0.5, 0.5):
        for o_n in (-0.5, 0.5):
            qx = px + o_s * tx[:, None] + o_n * lx[:, None]
            qy = py + o_s * ty[:, None] + o_n * ly[:, None]
            bed += 0.25 * bilinear(bed1, qx, qy)
            dem += 0.25 * bilinear(dem1, qx, qy)
    cls = nearest(cls1, px, py); river = nearest(river1, px, py); channel = nearest(channel1, px, py)
    nan_bed = ~np.isfinite(bed)
    if nan_bed.any():
        # outside DEM coverage: nearest finite value along the same station row, raised 5 m
        for r_ in np.nonzero(nan_bed.any(1))[0]:
            f = np.isfinite(bed[r_])
            bed[r_, ~f] = np.interp(np.nonzero(~f)[0], np.nonzero(f)[0], bed[r_, f]) + 5.0
    # --- metric distortion over the wet channel
    ratio = 1 - k[:, None] * lats[None, :]
    wetc = channel & (ws_ref[:, None] > bed)
    # --- initial state (solver arrays are [lateral row, station col])
    B = np.ascontiguousarray(bed.T)  # solver .npy reader requires C order
    WS = np.broadcast_to(ws_ref[None, :], B.shape)
    wet0 = (channel.T & (WS - B > 0.02))
    h = np.where(wet0, WS - B, 0.0)
    conv = np.where(h > 0, h ** (5 / 3), 0.0).sum(0) * DS
    u = np.where(h > 0, Q * h ** (2 / 3) / np.maximum(conv[None, :], 1e-9), 0.0)
    v = np.zeros_like(u)
    q_col = (h * u).sum(0) * DS
    assert np.allclose(q_col[conv > 0], Q)
    # --- package
    out.mkdir(parents=True)
    pkg = out / 'scenario'; pkg.mkdir()
    np.save(pkg / 'bed.npy', B)
    C = np.ascontiguousarray
    np.savez_compressed(pkg / 'initial_state.npz', depth=C(h), eta=C(B + h), u=C(u), v=C(v), hu=C(h * u), hv=C(h * v), wet=C(h > 1e-6))
    (pkg / 'features.json').write_text('{"features":[]}\n')
    (pkg / 'probes.json').write_text('{"probes":[]}\n')
    sc = copy.deepcopy(json.loads(TEMPLATE.read_text()))
    # inlet: rows shallower than 0.15 m carry no flux (thin shoreline rows make
    # the characteristic inlet solve degenerate); Q goes to the deeper rows
    h_in = h[:, 0]; act = h_in >= 0.15
    u_in = np.where(act, Q * h_in ** (2 / 3) / (np.where(act, h_in, 0) ** (5 / 3)).sum() / DS, 0.0)
    assert abs((h_in * u_in).sum() * DS - Q) < 1e-9
    prof_w = np.column_stack((B[:, 0], h_in, u_in, np.zeros_like(u_in)))
    if args.outflow_stage == 'ws_reference':
        stage_out, stage_src = float(ws_ref[-1]), 'evidence ws_reference at the last station (' + prof.get('ws_reference_method', 'water_median') + ')'
    else:
        stage_out = float(np.median(dem[-3:][river[-3:]])) if river[-3:].any() else float(ws_ref[-1])
        stage_src = '2021 DEM median over imagery water, last 3 stations'
    sc['boundaries'] = [
        dict(edge='west', kind='discharge_profile', ghost_cells=np.tile(prof_w, (2, 1)).tolist(),
             metadata=dict(target_discharge_m3s=Q, distribution='h^(5/3) conveyance, along station axis')),
        dict(edge='east', kind='outflow', stage=stage_out, metadata=dict(source=stage_src)),
        dict(edge='south', kind='bank'), dict(edge='north', kind='bank')]
    sc['grid'] = dict(nx=nst, ny=len(lats), dx=DS, dy=DS, origin_x=0.0, origin_y=float(lats[0]))
    sc.update(fixed_dt=0.05, duration=1200.0, roughness=args.roughness, feature_count=0, probe_count=0)
    sc['metadata'] = dict(
        scenario_id='colorado_hance_evidence_8000cfs_2021', scenario_type='real_world', fixture_kind=None,
        river_id='colorado_river_grand_canyon_rowing', flow_band='steady_8000cfs_2021',
        generator='build_hance_curvilinear_scenario.py', generator_version='20260926-v1', seed=1,
        description='Hance Rapid from measured sources: 2021 photogrammetric DEM banks and surface, 2014 sonar pools, '
                    'discharge-consistent inferred bed inside the rapid (no sonar there). Not accepted.',
        confidence_score=0.5, coordinate_reference_system='curvilinear: x station downstream along a smoothed EPSG:6404 centreline, y river-left; heights NAD83(2011) ellipsoid',
        provenance=dict(evidence_manifest_sha256=sha(ev / 'manifest.json'), evidence_grid_sha256=sha(ev / 'evidence_grid.npz'),
                        submerged_bed_inside_rapid_is_inference=True, initial_velocity_is_inferred=True,
                        target_discharge_m3s=Q, flow_source='2021-05/06 steady ~8,000 cfs Glen Canyon Dam release during the DEM/imagery flights',
                        measured_velocity=False))
    (pkg / 'scenario.json').write_text(json.dumps(sc, indent=2) + '\n')
    ox, oy = args.origin
    cmap = dict(schema='raftsim.curved_river_coordinate_map.v1', river_id='colorado_river',
                section_id='hance_evidence_2021', world_y_sign=-1, vertical_datum_m=args.vertical_datum_m,
                horizontal_origin_epsg6404_m=[ox, oy], vertical_reference='NAD83(2011) ellipsoid heights',
                mapping_policy='curved station/lateral map on a Gaussian-smoothed centreline of the 2021 imagery channel; local = EPSG:6404 minus origin (east, north); world Y reflected (ENU)',
                points=[[float(s_), float(X - ox), float(Y - oy), float(a_), float(b_)] for s_, X, Y, a_, b_ in zip(station, xs, ys, lx, ly)])
    (out / 'coordinate_map.json').write_text(json.dumps(cmap) + '\n')
    np.savez_compressed(out / 'reference.npz', station=station, lateral=lats, evidence_station=ev_station, ws_reference=ws_ref,
                        dem2021=dem.T, river=river.T, channel=channel.T, class_code=cls.T, curvature=k,
                        world_x=px.T, world_y=py.T)
    wet_ratio = ratio[wetc]
    stats = dict(stations=nst, lateral_cells=len(lats), half_width_m=half, smoothing_sigma_samples=sigma,
                 min_radius_m=float(1 / np.max(np.abs(k[3:-3]))), evidence_station_range=[float(ev_station[0]), float(ev_station[-1])],
                 metric_ratio_wet_min_max=[float(wet_ratio.min()), float(wet_ratio.max())],
                 wet_cells=int(wet0.sum()), measured_wet_cells=int((wet0 & (cls.T == 1)).sum()), inferred_wet_cells=int((wet0 & (cls.T == 2)).sum()),
                 stage_in=float(ws_ref[0]), stage_out=stage_out, filled_nan_bed_cells=int(nan_bed.sum()))
    (out / 'build_report.json').write_text(json.dumps(stats, indent=2) + '\n')
    print(json.dumps(stats, indent=1))


if __name__ == '__main__':
    main()
