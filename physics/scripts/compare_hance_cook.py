"""Compare a Hance curvilinear cook with the 2021 measured surface (numpy only).

Inputs: the scenario folder from build_hance_curvilinear_scenario.py and a
raftsim_water_solver run folder (frames/frame_NNNN.csv). Uses the last frame
unless --frame is given.

Reports, over the 2 m station/lateral grid:
- water surface: per-station median of cooked eta over cells that are water
  in the 2021 imagery, against the per-station median of the 2021 DEM over
  the same cells. The DEM metadata states it is less accurate on water: over
  calm clear water the stereo match lands on or near the bed and reads low,
  so this all-water comparison is informative only;
- textured surface (the accepted comparison): DEM over imagery whitewater,
  where the surface itself has stereo texture, against cooked eta at the same
  cells, per 10 m station bin with at least 5 whitewater cells;
- calm-water bounds: the calm per-station DEM median over water is a lower
  bound and the 25th percentile DEM of the dry cells touching the imagery
  water edge (the mask is conservative, so these sit up the bank) an upper
  bound on the true surface;
- wet extent: cooked wet (h > 0.05 m) against the imagery water mask;
- discharge through every station section, Froude and speed distributions;
- convergence: eta change between the last two saved frames.
Writes compare.json and three PNG maps (depth/speed, surface error, wet
agreement) plus a profile chart.
"""
import argparse
import json
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from solver_face_discharge import face_discharge  # noqa: E402

Q = 226.534772736


def write_png(path, rgb):
    h, w, _ = rgb.shape
    raw = np.zeros((h, w * 3 + 1), np.uint8); raw[:, 1:] = rgb.reshape(h, w * 3)

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw.tobytes(), 6)) + chunk(b'IEND', b''))


def colormap(t, stops):
    t = np.clip(t, 0, 1)[..., None]
    xs = np.linspace(0, 1, len(stops)); c = np.array(stops, float)
    out = np.zeros(t.shape[:-1] + (3,))
    for k in range(3):
        out[..., k] = np.interp(t[..., 0], xs, c[:, k])
    return out.astype(np.uint8)


def read_frame(path, ny, nx):
    a = np.loadtxt(path, delimiter=',', skiprows=1)
    assert a.shape[0] == ny * nx
    f = {}
    for k, name in enumerate('row,col,x,y,h,eta,u,v,hu,hv,wet,normal_x,normal_y,normal_z,froude'.split(',')):
        f[name] = a[:, k].reshape(ny, nx)
    return f


def upscale(img, k):
    return np.repeat(np.repeat(img, k, 0), k, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scenario_root', type=Path)
    ap.add_argument('run', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--frame', type=int, default=-1)
    ap.add_argument('--evidence', type=Path, default=Path('tmp/hance-evidence-v0'))
    ap.add_argument('--solver-binary', type=Path, default=ROOT / 'tmp/hance-solver-build/raftsim_water_solver.exe')
    args = ap.parse_args()
    sc = json.loads((args.scenario_root / 'scenario/scenario.json').read_text())
    ny, nx, d = sc['grid']['ny'], sc['grid']['nx'], sc['grid']['dx']
    ref = np.load(args.scenario_root / 'reference.npz')
    bed = np.load(args.scenario_root / 'scenario/bed.npy')
    frames = sorted((args.run / 'frames').glob('frame_*.csv'))
    f = read_frame(frames[args.frame], ny, nx)
    prev = read_frame(frames[args.frame - 1], ny, nx) if len(frames) > 1 else None
    h, eta, u, v, fr = f['h'], f['eta'], f['u'], f['v'], f['froude']
    wet = h > 0.05
    river = ref['river'].astype(bool); dem = ref['dem2021']; cls = ref['class_code']
    station = ref['station']; wsr = ref['ws_reference']
    # per-station surface comparison over imagery water that is cooked wet
    both = river & wet
    cook_med = np.full(nx, np.nan); dem_med = np.full(nx, np.nan)
    for j in range(nx):
        m = both[:, j] & np.isfinite(dem[:, j])
        if m.sum() >= 5:
            cook_med[j] = np.median(eta[m, j]); dem_med[j] = np.median(dem[m, j])
    err = cook_med - dem_med
    ok = np.isfinite(err)
    # 25 m running median of the per-station error (photogrammetric noise)
    k = 12
    err_s = np.array([np.nanmedian(err[max(0, j - k):j + k + 1]) if ok[max(0, j - k):j + k + 1].any() else np.nan for j in range(nx)])
    cell_err = np.where(both, eta - dem, np.nan)
    # Section discharge: the solver's exact face mass flux. The cell-centre
    # h*u sum overstates transport on steep, shallow wet/dry reaches.
    q_sec = face_discharge(args.solver_binary, args.scenario_root / 'scenario', f)
    q_centre = (h * u).sum(0) * d
    iou = (river & wet).sum() / max((river | wet).sum(), 1)
    false_wet = wet & ~river & (cls != 3)
    missed = river & ~wet
    rapid = (station >= 700) & (station <= 1600)
    # waterline upper bound: dry cells touching imagery water, projected on the centreline
    evg0 = np.load(args.evidence / 'evidence_grid.npz')
    ev_river, ev_channel, ev_dem = evg0['river'], evg0['channel'], evg0['dem2021'].astype(float)
    adj = np.zeros_like(ev_river)
    adj[1:] |= ev_river[:-1]; adj[:-1] |= ev_river[1:]; adj[:, 1:] |= ev_river[:, :-1]; adj[:, :-1] |= ev_river[:, 1:]
    er, ec = np.nonzero(~ev_channel & adj & np.isfinite(ev_dem))
    ex, ey = 211300.0 + ec + 0.5, 560300.0 - er - 0.5
    mid = ny // 2
    cx, cy = ref['world_x'][mid], ref['world_y'][mid]
    best = np.full(len(er), np.inf); bi = np.zeros(len(er), int)
    for j0 in range(0, nx, 64):
        d2 = (ex[:, None] - cx[None, j0:j0 + 64]) ** 2 + (ey[:, None] - cy[None, j0:j0 + 64]) ** 2
        jj = d2.argmin(1); dd = d2[np.arange(len(er)), jj]; u_ = dd < best; best[u_] = dd[u_]; bi[u_] = j0 + jj[u_]
    upper = np.full(nx, np.nan)
    for j in range(0, nx, 5):
        m = (bi >= j) & (bi < j + 5) & (best < 120 ** 2)
        if m.sum() >= 6:
            upper[j:j + 5] = np.percentile(ev_dem[er[m], ec[m]], 25)
    # imagery whitewater (evidence foam mask, nearest 1 m cell) against cooked
    # near-critical flow; foam is a surface texture cue, Froude a flow state
    evg = np.load(args.evidence / 'evidence_grid.npz')
    wx, wy = ref['world_x'], ref['world_y']
    cc = np.clip(np.floor(wx - 211300.0).astype(int), 0, evg['foam'].shape[1] - 1)
    rr = np.clip(np.floor(560300.0 - wy).astype(int), 0, evg['foam'].shape[0] - 1)
    foam = evg['foam'][rr, cc] & river
    fast = wet & (fr > 0.8)
    foam_share = foam.sum(0) / np.maximum(river.sum(0), 1)
    fast_share = fast.sum(0) / np.maximum(wet.sum(0), 1)
    kern = np.ones(13) / 13
    fs_s = np.convolve(foam_share, kern, mode='same'); ks_s = np.convolve(fast_share, kern, mode='same')
    tex_err, tex_st = [], []
    for j in range(0, nx, 5):
        m = foam[:, j:j + 5] & wet[:, j:j + 5] & np.isfinite(dem[:, j:j + 5])
        if m.sum() >= 5:
            tex_err.append(float(np.median(eta[:, j:j + 5][m] - dem[:, j:j + 5][m]))); tex_st.append(float(station[j]))
    tex_err = np.array(tex_err)
    textured = dict(bins=len(tex_err), median=float(np.median(tex_err)) if len(tex_err) else None,
                    median_abs=float(np.median(np.abs(tex_err))) if len(tex_err) else None,
                    p10_p90=np.percentile(tex_err, [10, 90]).tolist() if len(tex_err) else None,
                    by_bin=[[s_, round(e_, 3)] for s_, e_ in zip(tex_st, tex_err)])
    calm = (foam_share < 0.02) & np.isfinite(cook_med) & np.isfinite(dem_med) & np.isfinite(upper)
    lo_ok = cook_med[calm] >= dem_med[calm] - 0.15
    hi_ok = cook_med[calm] <= upper[calm] + 0.15
    bounds = dict(calm_stations=int(calm.sum()), within_both=float(np.mean(lo_ok & hi_ok)), below_lower=float(np.mean(~lo_ok)),
                  above_upper=float(np.mean(~hi_ok)), tolerance_m=0.15)
    whitewater = dict(foam_cells=int(foam.sum()), cooked_fr_gt_0p8_cells=int(fast.sum()),
                      overlap_cells=int((foam & fast).sum()),
                      station_profile_correlation=float(np.corrcoef(fs_s, ks_s)[0, 1]),
                      foam_share_by_250m=[float(foam[:, j:j + 125].sum() / max(river[:, j:j + 125].sum(), 1)) for j in range(0, nx, 125)],
                      fr_gt_0p8_share_by_250m=[float(fast[:, j:j + 125].sum() / max(wet[:, j:j + 125].sum(), 1)) for j in range(0, nx, 125)])
    out = args.output; out.mkdir(parents=True, exist_ok=True)
    res = dict(
        frame=frames[args.frame].name, frames=len(frames),
        surface_error_m=dict(station_median_abs=float(np.nanmedian(np.abs(err))), station_p10_p90=np.nanpercentile(err, [10, 90]).tolist(),
                             smoothed_25m_abs_max=float(np.nanmax(np.abs(err_s))),
                             rapid_700_1600_median_abs=float(np.nanmedian(np.abs(err[rapid]))),
                             cell_p10_p50_p90=np.nanpercentile(cell_err, [10, 50, 90]).tolist(),
                             stations_over_0p5m=int(np.sum(np.abs(err_s) > 0.5))),
        wet_extent=dict(iou=float(iou), cooked_wet_cells=int(wet.sum()), imagery_water_cells=int(river.sum()),
                        false_wet_cells=int(false_wet.sum()), missed_water_cells=int(missed.sum())),
        discharge_m3s=dict(target=Q, section_p5_p50_p95=np.percentile(q_sec[10:-10], [5, 50, 95]).tolist(),
                           inlet=float(q_sec[1]), outlet=float(q_sec[-2]),
                           method='exact numerical face mass flux of the frame (solver --inspect-face-fluxes)'),
        discharge_cell_centre_hu_sum_m3s=dict(section_p5_p50_p95=np.percentile(q_centre[10:-10], [5, 50, 95]).tolist(),
                                              note='diagnostic only: overstates transport on steep, shallow wet/dry reaches'),
        hydraulics=dict(froude_gt1_share_of_wet=float((fr[wet] > 1).mean()), speed_p50_p95_max=np.percentile(np.hypot(u, v)[wet], [50, 95, 100]).tolist(),
                        rapid_speed_p50_p95=np.percentile(np.hypot(u, v)[wet & rapid[None, :]], [50, 95]).tolist()),
        textured_surface_error_m=textured,
        calm_water_bounds=bounds,
        whitewater=whitewater,
        convergence=dict(eta_change_last_frames_p95_m=float(np.percentile(np.abs(eta - prev['eta'])[wet & (prev['h'] > 0.05)], 95)) if prev else None),
        stage_at_stations={str(int(s)): [float(cook_med[int(s / d)]), float(dem_med[int(s / d)])] for s in range(0, int(station[-1]), 250)})
    (out / 'compare.json').write_text(json.dumps(res, indent=2) + '\n')
    np.savez_compressed(out / 'profiles.npz', waterline_upper=upper, station=station, cook_median=cook_med, dem_median=dem_med, ws_reference=wsr, error=err, error_25m=err_s, q_section=q_sec)
    # --- maps (rows flipped so river-left is at the top; station runs left to right)
    sp = np.hypot(u, v)
    img = colormap(sp / 5.0, [(20, 30, 60), (40, 110, 200), (120, 220, 230), (255, 255, 255)])
    img[~wet] = colormap(np.clip((bed[~wet] - 745) / 40, 0, 1), [(90, 70, 50), (200, 180, 150)])
    write_png(out / 'speed.png', upscale(img[::-1], 2))
    e = np.nan_to_num(np.clip(cell_err / 1.5, -1, 1))
    img = colormap((e + 1) / 2, [(40, 80, 220), (245, 245, 245), (220, 50, 40)])
    img[~both] = (60, 60, 60)
    write_png(out / 'surface_error.png', upscale(img[::-1], 2))
    img = np.full((ny, nx, 3), 60, np.uint8)
    img[river & wet] = (60, 140, 230); img[wet & ~river] = (230, 60, 50); img[river & ~wet] = (250, 210, 40)
    img[cls == 3] = (150, 150, 150)
    write_png(out / 'wet_agreement.png', upscale(img[::-1], 2))
    img = np.full((ny, nx, 3), 60, np.uint8)
    img[wet] = (40, 70, 110); img[foam] = (250, 250, 250); img[fast] = (230, 90, 40); img[foam & fast] = (250, 200, 60)
    write_png(out / 'whitewater.png', upscale(img[::-1], 2))
    # --- profile chart: cooked median (blue), DEM median (grey), reference WS (black), bed min (brown)
    W, H = 1400, 500
    canvas = np.full((H, W, 3), 255, np.uint8)
    zmin, zmax = np.nanmin(np.where(river, bed, np.nan)) - 1, np.nanmax(wsr) + 1
    def px(s, z):
        return (s / station[-1] * (W - 40) + 20), (H - 20 - (z - zmin) / (zmax - zmin) * (H - 40))
    def line(z, color, width=1):
        s = station; good = np.isfinite(z)
        ss = np.linspace(0, station[-1], 8000); zz = np.interp(ss, s[good], z[good])
        keep = np.interp(ss, s, good.astype(float)) > 0.5
        x, y = px(ss[keep], zz[keep])
        for dx_ in range(-width + 1, width):
            for dy_ in range(-width + 1, width):
                xi = np.clip((x + dx_).astype(int), 0, W - 1); yi = np.clip((y + dy_).astype(int), 0, H - 1)
                canvas[yi, xi] = color
    for s in range(0, int(station[-1]), 100):
        canvas[:, int(px(s, 0)[0])] = (235, 235, 235)
    for z in range(int(zmin), int(zmax) + 1):
        canvas[int(px(0, z)[1]), :] = (235, 235, 235) if z % 5 else (200, 200, 200)
    bed_min = np.array([np.nanmin(np.where(river[:, j], bed[:, j], np.nan)) if river[:, j].any() else np.nan for j in range(nx)])
    line(bed_min, (140, 100, 60))
    line(dem_med, (150, 150, 150), 2)
    line(upper, (120, 200, 120), 1)
    line(wsr, (0, 0, 0))
    line(cook_med, (30, 90, 220), 2)
    write_png(out / 'profile.png', canvas)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
