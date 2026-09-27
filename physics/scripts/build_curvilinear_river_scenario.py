"""River solver scenario on a curvilinear station/lateral grid from an evidence grid (numpy only).

Generalises build_hance_curvilinear_scenario.py (which stays as Hance's
reproducible record): the evidence window, reach station range and discharge
come from the evidence manifest instead of constants.

Input: an evidence folder with evidence_grid.npz (bed, dem2021 = surface over
water / ground elsewhere, class_code, river, channel), centreline.json
(points_xy_station, upstream first), profile.json (station_center_m,
ws_reference_m) and manifest.json (grid x0/y_top/nx/ny at 1 m; statistics
reach_station_m; parameters discharge_m3s).

Output: a raftsim.scenario2_5d.v0 package on a DS m station (x, downstream) by
lateral (y, river-left) grid, the raftsim.curved_river_coordinate_map.v1
(world_y_sign -1: ENU, north is camera-left for a +X camera in Unreal) and a
reference file for comparing a cook with the evidence surface.

Bed per cell: mean of four bilinear samples of the evidence bed at +-DS/4 in
the station/lateral frame; class/river/channel: nearest evidence cell.
Initial water: the reference surface in channel cells, conveyance velocity.
Upstream: discharge_profile (h^(5/3) conveyance; rows < 0.15 m carry none);
downstream: outflow at the reference stage; sides: bank. The solver has no
metric terms; the worst on-bend cell-length ratio is reported.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / 'physics/data/real_world/colorado_river_grand_canyon_rowing/scenario_hance/low_release_planning/scenario.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gauss_smooth(v, sigma):
    r = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    head = v[0] + (v[0] - v[min(r, len(v) - 1)]) * np.arange(r, 0, -1) / r
    tail = v[-1] + (v[-1] - v[max(-r - 1, -len(v))]) * np.arange(1, r + 1) / r
    return np.convolve(np.concatenate([head, v, tail]), k, mode='valid')


def arc_resample(x, y, step):
    s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
    t = np.arange(int(np.floor(s[-1] / step)) + 1) * step
    return np.interp(t, s, x), np.interp(t, s, y), t


def curvature(x, y):
    dx, dy = np.gradient(x), np.gradient(y)
    ddx, ddy = np.gradient(dx), np.gradient(dy)
    return (dx * ddy - dy * ddx) / np.maximum((dx * dx + dy * dy) ** 1.5, 1e-12)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--river-id', required=True)
    ap.add_argument('--section-id', required=True)
    ap.add_argument('--scenario-id', required=True)
    ap.add_argument('--flow-band', required=True)
    ap.add_argument('--crs-label', required=True, help='e.g. "EPSG:5367 CR05 / CRTM05"')
    ap.add_argument('--vertical-reference', required=True)
    ap.add_argument('--vertical-datum-m', type=float, required=True)
    ap.add_argument('--origin', type=float, nargs=2, help='local frame origin (default: west edge, north-south centre of the window)')
    ap.add_argument('--discharge-m3s', type=float, help='default: evidence manifest parameters.discharge_m3s')
    ap.add_argument('--flow-source', required=True)
    ap.add_argument('--description', required=True)
    ap.add_argument('--roughness', type=float, default=0.045)
    ap.add_argument('--ds-m', type=float, default=2.0)
    ap.add_argument('--min-radius-m', type=float, default=120.0)
    ap.add_argument('--half-width-m', type=float, default=0.0, help='0: channel extent + margin')
    ap.add_argument('--bank-margin-m', type=float, default=10.0)
    ap.add_argument('--trim-m', type=float, default=20.0)
    ap.add_argument('--inlet-flux-scale', type=float, default=1.0,
                    help='scale the inlet ghost velocities (the discharge-profile inlet can over-deliver on steep reaches; '
                         'set target / conveyed from a previous cook)')
    args = ap.parse_args()
    out = args.output.resolve(); assert not out.exists(), 'fresh output required'
    ev = args.evidence.resolve()
    man = json.loads((ev / 'manifest.json').read_text())
    X0, Y1, NX, NY = man['grid']['x0'], man['grid']['y_top'], man['grid']['nx'], man['grid']['ny']
    Q = args.discharge_m3s or man['parameters']['discharge_m3s']
    DS = args.ds_m
    reach = man['statistics'].get('reach_station_m')
    g = np.load(ev / 'evidence_grid.npz')
    bed1, dem1, cls1 = g['bed'].astype(np.float64), g['dem2021'].astype(np.float64), g['class_code']
    river1, channel1 = g['river'], g['channel']
    prof = json.loads((ev / 'profile.json').read_text())
    cl = np.array(json.loads((ev / 'centreline.json').read_text())['points_xy_station'])
    cl = cl[np.argsort(cl[:, 2])]
    old_x, old_y, old_s = cl[:, 0], cl[:, 1], cl[:, 2]

    def bilinear(a, ex, ny_):
        cf = ex - X0 - 0.5; rf = Y1 - ny_ - 0.5
        c = np.clip(np.floor(cf).astype(int), 0, NX - 2); r = np.clip(np.floor(rf).astype(int), 0, NY - 2)
        u = np.clip(cf - c, 0, 1); v = np.clip(rf - r, 0, 1)
        return a[r, c] * (1 - u) * (1 - v) + a[r, c + 1] * u * (1 - v) + a[r + 1, c] * (1 - u) * v + a[r + 1, c + 1] * u * v

    def nearest(a, ex, ny_):
        c = np.clip(np.floor(ex - X0).astype(int), 0, NX - 1); r = np.clip(np.floor(Y1 - ny_).astype(int), 0, NY - 1)
        return a[r, c]

    # smooth the centreline until its tightest radius is acceptable
    x, y, _ = arc_resample(old_x, old_y, DS)
    sigma = 2.0
    while True:
        xs, ys = gauss_smooth(x, sigma), gauss_smooth(y, sigma)
        xs, ys, _ = arc_resample(xs, ys, DS)
        k = curvature(xs, ys) / DS
        if 1 / np.max(np.abs(k[5:-5])) >= args.min_radius_m or sigma > 400:
            break
        sigma *= 1.25
    tx, ty = np.gradient(xs), np.gradient(ys); tn = np.hypot(tx, ty); tx, ty = tx / tn, ty / tn
    lx, ly = -ty, tx
    j_old = np.array([np.argmin((old_x - X) ** 2 + (old_y - Y) ** 2) for X, Y in zip(xs, ys)])
    ev_st = old_s[j_old]
    rr, cc = np.nonzero(channel1)
    ex, ey = X0 + cc + 0.5, Y1 - rr - 0.5
    best = np.full(len(rr), np.inf); bi = np.zeros(len(rr), int)
    for j0 in range(0, len(xs), 64):
        j1 = min(len(xs), j0 + 64)
        d2 = (ex[:, None] - xs[None, j0:j1]) ** 2 + (ey[:, None] - ys[None, j0:j1]) ** 2
        jj = np.argmin(d2, 1); dd = d2[np.arange(len(rr)), jj]
        u = dd < best; best[u] = dd[u]; bi[u] = j0 + jj[u]
    lat = (ex - xs[bi]) * lx[bi] + (ey - ys[bi]) * ly[bi]
    in_reach = np.ones(len(rr), bool) if reach is None else (ev_st[bi] >= reach[0]) & (ev_st[bi] <= reach[1])
    need = float(np.percentile(np.abs(lat[in_reach & (best < 150 ** 2)]), 99.5)) + args.bank_margin_m
    half = args.half_width_m or float(np.ceil(need / DS) * DS)
    ncell = int(round(half / DS))
    lats = np.arange(-ncell, ncell + 1) * DS
    px = xs[:, None] + lats[None, :] * lx[:, None]; py = ys[:, None] + lats[None, :] * ly[:, None]
    m = args.trim_m
    inside = np.all((px > X0 + m) & (px < X0 + NX - m) & (py > Y1 - NY + m) & (py < Y1 - m), axis=1)
    if reach is not None:
        inside &= (ev_st >= reach[0]) & (ev_st <= reach[1])
    idx = np.nonzero(inside)[0]
    a, b = idx[0], idx[-1]
    assert np.all(inside[a:b + 1]), 'grid exits and re-enters the window'
    sel = slice(a, b + 1)
    xs, ys, lx, ly, tx, ty, px, py, ev_st = xs[sel], ys[sel], lx[sel], ly[sel], tx[sel], ty[sel], px[sel], py[sel], ev_st[sel]
    k = curvature(xs, ys) / DS
    nst = len(xs); station = np.arange(nst) * DS
    ws_ref = np.interp(ev_st, prof['station_center_m'], prof['ws_reference_m'])
    bed = np.zeros((nst, len(lats))); dem = np.zeros_like(bed)
    q = DS / 4
    for o_s in (-q, q):
        for o_n in (-q, q):
            qx = px + o_s * tx[:, None] + o_n * lx[:, None]; qy = py + o_s * ty[:, None] + o_n * ly[:, None]
            bed += 0.25 * bilinear(bed1, qx, qy); dem += 0.25 * bilinear(dem1, qx, qy)
    cls = nearest(cls1, px, py); river = nearest(river1, px, py); channel = nearest(channel1, px, py)
    assert np.isfinite(bed).all(), 'bed has gaps inside the grid'
    ratio = 1 - k[:, None] * lats[None, :]
    B = np.ascontiguousarray(bed.T)
    WS = np.broadcast_to(ws_ref[None, :], B.shape)
    wet0 = channel.T & (WS - B > 0.02)
    h = np.where(wet0, WS - B, 0.0)
    conv = np.where(h > 0, h ** (5 / 3), 0.0).sum(0) * DS
    u = np.where(h > 0, Q * h ** (2 / 3) / np.maximum(conv[None, :], 1e-9), 0.0)
    v = np.zeros_like(u)
    out.mkdir(parents=True); pkg = out / 'scenario'; pkg.mkdir()
    np.save(pkg / 'bed.npy', B)
    C = np.ascontiguousarray
    np.savez_compressed(pkg / 'initial_state.npz', depth=C(h), eta=C(B + h), u=C(u), v=C(v), hu=C(h * u), hv=C(h * v), wet=C(h > 1e-6))
    (pkg / 'features.json').write_text('{"features":[]}\n'); (pkg / 'probes.json').write_text('{"probes":[]}\n')
    sc = copy.deepcopy(json.loads(TEMPLATE.read_text()))
    h_in = h[:, 0]; act = h_in >= 0.15
    u_in = np.where(act, Q * h_in ** (2 / 3) / (np.where(act, h_in, 0) ** (5 / 3)).sum() / DS, 0.0)
    assert abs((h_in * u_in).sum() * DS - Q) < 1e-9
    u_in = u_in * args.inlet_flux_scale
    prof_w = np.column_stack((B[:, 0], h_in, u_in, np.zeros_like(u_in)))
    stage_out = float(ws_ref[-1])
    sc['boundaries'] = [
        dict(edge='west', kind='discharge_profile', ghost_cells=np.tile(prof_w, (2, 1)).tolist(),
             metadata=dict(target_discharge_m3s=Q, distribution='h^(5/3) conveyance, along station axis',
                          inlet_flux_scale=args.inlet_flux_scale)),
        dict(edge='east', kind='outflow', stage=stage_out, metadata=dict(source='evidence ws_reference at the last station (' + prof.get('ws_reference_method', '') + ')')),
        dict(edge='south', kind='bank'), dict(edge='north', kind='bank')]
    sc['grid'] = dict(nx=nst, ny=len(lats), dx=DS, dy=DS, origin_x=0.0, origin_y=float(lats[0]))
    sc.update(fixed_dt=0.05, duration=1200.0, roughness=args.roughness, feature_count=0, probe_count=0)
    sc['metadata'] = dict(
        scenario_id=args.scenario_id, scenario_type='real_world', fixture_kind=None, river_id=args.river_id, flow_band=args.flow_band,
        generator='build_curvilinear_river_scenario.py', generator_version='20260927-v1', seed=1, description=args.description,
        confidence_score=0.4, coordinate_reference_system=f'curvilinear: x station downstream along a smoothed {args.crs_label} centreline, y river-left; heights {args.vertical_reference}',
        provenance=dict(evidence_manifest_sha256=sha(ev / 'manifest.json'), evidence_grid_sha256=sha(ev / 'evidence_grid.npz'),
                        submerged_bed_is_inference=True, initial_velocity_is_inferred=True, target_discharge_m3s=Q,
                        flow_source=args.flow_source, measured_velocity=False))
    (pkg / 'scenario.json').write_text(json.dumps(sc, indent=2) + '\n')
    ox, oy = args.origin if args.origin else (X0, Y1 - NY / 2.0)
    cmap = dict(schema='raftsim.curved_river_coordinate_map.v1', river_id=args.river_id, section_id=args.section_id,
                world_y_sign=-1, vertical_datum_m=args.vertical_datum_m, horizontal_origin_m=[ox, oy], horizontal_crs=args.crs_label,
                vertical_reference=args.vertical_reference,
                mapping_policy=f'curved station/lateral map on a Gaussian-smoothed evidence centreline; local = {args.crs_label} minus origin (east, north); world Y reflected (ENU)',
                points=[[float(s_), float(X - ox), float(Y - oy), float(a_), float(b_)] for s_, X, Y, a_, b_ in zip(station, xs, ys, lx, ly)])
    (out / 'coordinate_map.json').write_text(json.dumps(cmap) + '\n')
    np.savez_compressed(out / 'reference.npz', station=station, lateral=lats, evidence_station=ev_st, ws_reference=ws_ref,
                        dem2021=dem.T, river=river.T, channel=channel.T, class_code=cls.T, curvature=k, world_x=px.T, world_y=py.T)
    wetc = channel & (ws_ref[:, None] > bed)
    stats = dict(stations=nst, lateral_cells=len(lats), half_width_m=half, smoothing_sigma_samples=sigma,
                 min_radius_m=float(1 / np.max(np.abs(k[3:-3]))), evidence_station_range=[float(ev_st[0]), float(ev_st[-1])],
                 metric_ratio_wet_min_max=[float(ratio[wetc].min()), float(ratio[wetc].max())], wet_cells=int(wet0.sum()),
                 inferred_wet_cells=int((wet0 & (cls.T == 2)).sum()), stage_in=float(ws_ref[0]), stage_out=stage_out, discharge_m3s=Q,
                 origin=[ox, oy])
    (out / 'build_report.json').write_text(json.dumps(stats, indent=2) + '\n')
    print(json.dumps(stats, indent=1))


if __name__ == '__main__':
    main()
