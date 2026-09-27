"""Compare South Fork snapshots with the captured water surface, not equilibrium.

For each cook (a station section or the whole river) reads the prepared
package directory (manifest + station_map.npz) and one saved frame, keeps
only cells inside the section's own station range (overlaps are discarded),
and reports per 5 m station bin: median cooked surface minus captured
surface, cooked-wet fraction of the captured water mask, speed and Froude
statistics. Writes bias.npz (station, smoothed bias) for the next bed
iteration and report.json. Numpy only. Signed route-aligned transport is a
cell-centred screening proxy, not conservative section flux or settling proof.

Args: output_dir --cook PREP_DIR OUT_DIR STEP [--cook ...]
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

BIN = 5.0
ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/playable_route/coordinate_map.json'


def signed_transport(station, depth, east_velocity, north_velocity, route_points):
    """h * velocity dot local route tangent (m2/s), in native east/north.

    The route stores station/east/north/normal_east/normal_north, matching the
    cook preparation. Endpoint context retains the endpoint tangent. This does
    not approximate numerical face fluxes or account for a station Jacobian.
    """
    points = np.asarray(route_points, dtype=float)
    if (points.ndim != 2 or points.shape[0] < 2 or points.shape[1] != 5
            or not np.isfinite(points).all() or not np.all(np.diff(points[:, 0]) > 0)):
        raise ValueError('Finite ordered route with five columns required')
    if not np.allclose(np.hypot(points[:, 3], points[:, 4]), 1., rtol=0, atol=1e-6):
        raise ValueError('Unit route normals required')
    station, depth, u, v = [np.asarray(a, dtype=float) for a in
                           (station, depth, east_velocity, north_velocity)]
    if (not (station.shape == depth.shape == u.shape == v.shape)
            or not all(np.isfinite(a).all() for a in (station, depth, u, v))
            or np.any(depth < 0)):
        raise ValueError('Matching finite samples and nonnegative depth required')
    tx = np.interp(station, points[:, 0], points[:, 4])
    ty = np.interp(station, points[:, 0], -points[:, 3])
    norm = np.hypot(tx, ty)
    if np.any(norm < 1e-8):
        raise ValueError('Undefined interpolated route tangent')
    return depth * (u * tx + v * ty) / norm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--cook', nargs=3, action='append', required=True, metavar=('PREP', 'OUT', 'STEP'))
    parser.add_argument('--wet-depth-m', type=float, default=0.03)
    parser.add_argument('--discharge', type=float, default=45.3069545472)
    parser.add_argument('--route', type=Path, default=ROUTE)
    parser.add_argument('--transport-screen-only', '--settled-only', dest='transport_screen_only',
                        action='store_true', help='bias only from signed transport proxy bins passing 0.85-1.25 Q; NOT a settling test (--settled-only is a legacy alias)')
    args = parser.parse_args()
    if not np.isfinite(args.discharge) or args.discharge <= 0 or not np.isfinite(args.wet_depth_m) or args.wet_depth_m < 0:
        raise ValueError('Positive finite discharge and nonnegative finite wet threshold required')
    out = args.output
    assert not out.exists()
    route_bytes = args.route.read_bytes()
    route = json.loads(route_bytes)
    if route['horizontal_crs'] != 'EPSG:32610':
        raise ValueError('Native UTM32610 route required')
    rows = []
    balance = []
    for prep, cook, step in args.cook:
        prep, cook, step = Path(prep), Path(cook), int(step)
        manifest = json.loads((prep / 'manifest.json').read_text())
        smap = np.load(prep / 'station_map.npz')
        a, b = manifest['section']['core_range_m']
        frame = cook / ('frame_%06d' % step)
        done = json.loads((frame / 'complete.json').read_text())
        if done['step'] != step or not done['snapshot']:
            raise ValueError('Completed matching snapshot required')
        for name in manifest['packages']:
            grid = json.loads((prep / name / 'scenario.json').read_text())['grid']
            if (grid['nx'], grid['ny'], grid['dx'], grid['dy']) != (80, 80, 1., 1.):
                raise ValueError('This station-bin analysis requires80x80 one-metre native cells')
        h = np.load(frame / 'h.npy').reshape(-1, 80, 80)
        u = np.load(frame / 'u.npy').reshape(-1, 80, 80)
        v = np.load(frame / 'v.npy').reshape(-1, 80, 80)
        bed = np.stack([np.load(prep / name / 'bed.npy') for name in manifest['packages']])
        st, surf, water = smap['station'], smap['surface'], smap['water']
        keep = water & (st >= a) & (st < b)
        eta = bed + h
        wet = keep & (h > args.wet_depth_m)
        speed = np.hypot(u, v)
        fr = np.where(wet, speed / np.sqrt(9.81 * np.maximum(h, 1e-3)), 0.0)
        q = signed_transport(st[keep], h[keep], u[keep], v[keep], route['points'])
        rows.append(dict(station=st[keep], dev=np.where(wet, eta - surf, np.nan)[keep], wet=wet[keep], speed=speed[keep], fr=fr[keep], h=h[keep], q=q, unsigned_q=(h * speed)[keep]))
        fluxes = done['exterior_fluxes']
        inflow = sum(f for f in fluxes if f > 0); outflow = -sum(f for f in fluxes if f < 0)
        balance.append(dict(section=manifest['section']['name'], time_s=done['time_seconds'], inflow_m3s=inflow, outflow_m3s=outflow,
                            volume_m3=done['volume_m3'], max_speed=done['maximum_speed_mps'], max_depth=done['maximum_depth_m']))
    st = np.concatenate([r['station'] for r in rows]); dev = np.concatenate([r['dev'] for r in rows])
    wet = np.concatenate([r['wet'] for r in rows]); speed = np.concatenate([r['speed'] for r in rows])
    fr = np.concatenate([r['fr'] for r in rows]); h = np.concatenate([r['h'] for r in rows]); q = np.concatenate([r['q'] for r in rows])
    unsigned_q = np.concatenate([r['unsigned_q'] for r in rows])
    lo = np.floor(st.min() / BIN) * BIN
    nb = int(np.ceil((st.max() - lo) / BIN)) + 1
    k = ((st - lo) / BIN).astype(int)
    centers = lo + (np.arange(nb) + 0.5) * BIN
    bias = np.full(nb, np.nan); qbin = np.zeros(nb); wetfrac = np.zeros(nb); smed = np.zeros(nb); smax = np.zeros(nb); frac_super = np.zeros(nb); count = np.bincount(k, minlength=nb)
    unsigned_qbin = np.zeros(nb)
    order = np.argsort(k, kind='stable')
    for j, idx in enumerate(np.split(order, np.cumsum(count)[:-1])):
        if len(idx) < 5:
            continue
        w = wet[idx]
        wetfrac[j] = w.mean()
        qbin[j] = q[idx].sum() / BIN  # 1 m cells; signed cell-centred proxy, not face flux
        unsigned_qbin[j] = unsigned_q[idx].sum() / BIN
        if w.sum() >= 5:
            bias[j] = np.nanmedian(dev[idx][w])
            smed[j] = np.median(speed[idx][w]); smax[j] = speed[idx][w].max(); frac_super[j] = (fr[idx][w] > 1).mean()
    screened = (qbin > 0.85 * args.discharge) & (qbin < 1.25 * args.discharge)
    good = np.isfinite(bias) & (wetfrac >= 0.5) & (screened if args.transport_screen_only else True)
    if not good.any():
        raise ValueError('No eligible bias bins; refusing a fabricated zero calibration')
    filled = np.interp(np.arange(nb), np.nonzero(good)[0], bias[good])
    kern = np.exp(-0.5 * (np.arange(-9, 10) / 3.0) ** 2); kern /= kern.sum()
    smooth = np.convolve(np.pad(filled, 9, mode='edge'), kern, mode='valid')
    out.mkdir(parents=True)
    np.savez(out / 'bias.npz', station=centers, bias=smooth, raw_bias=bias, wet_fraction=wetfrac,
             local_discharge=qbin, signed_transport_proxy=qbin, unsigned_transport_proxy=unsigned_qbin,
             used=good, settling_accepted=False, transport_screen_only=args.transport_screen_only)
    valid = np.isfinite(dev) & wet
    summary = dict(cells=int(len(st)), cook_wet_fraction_of_captured_mask=float(wet.mean()),
                   median_surface_error_m=float(np.median(dev[valid])), median_abs_surface_error_m=float(np.median(np.abs(dev[valid]))),
                   p10_p90_surface_error_m=np.percentile(dev[valid], [10, 90]).tolist(),
                   supercritical_wet_fraction=float((fr[wet] > 1).mean()), speed_p50_p95_m_s=np.percentile(speed[wet], [50, 95]).tolist(),
                   bins_with_surface_error_over_0_25_m=int(np.sum(np.abs(bias[np.isfinite(bias)]) > 0.25)), bins=int(np.isfinite(bias).sum()),
                   bins_passing_0_85_to_1_25_q=int(screened.sum()), median_error_in_those_bins_m=float(np.nanmedian(bias[screened])) if screened.any() else None,
                   bins_used_for_bias=int(good.sum()))
    report = dict(schema='raftsim.south_fork.discharge_bed_cook_comparison.v2', cooks=[dict(prep=p, out=o, step=int(s)) for p, o, s in args.cook],
                  settling_accepted=False, normal_map_integrated=False,
                  route=dict(path=str(args.route.resolve()), sha256=hashlib.sha256(route_bytes).hexdigest()),
                  transport_screen_only=args.transport_screen_only,
                  transport_note='local_discharge is a legacy alias for signed route-aligned cell-centred transport / bin length, not numerical section flux or temporal equilibrium. Bias is simulated-minus-captured surface, not measured bathymetry.',
                  mass_balance=balance, summary=summary,
                  bins=dict(station=centers.tolist(), surface_error_m=[None if not np.isfinite(x) else float(x) for x in bias],
                            wet_fraction=wetfrac.tolist(), local_discharge_m3s=qbin.tolist(), signed_transport_proxy_m3s=qbin.tolist(), unsigned_transport_proxy_m3s=unsigned_qbin.tolist(), speed_median=smed.tolist(), speed_max=smax.tolist(), supercritical_fraction=frac_super.tolist()))
    (out / 'report.json').write_text(json.dumps(report) + '\n')
    print(json.dumps(dict(summary=summary, mass_balance=balance), indent=1))
    worst = np.argsort(-np.nan_to_num(np.abs(bias)))[:12]
    print('largest bin errors:', [(round(centers[j]), round(float(bias[j]), 2), round(float(wetfrac[j]), 2)) for j in worst])


if __name__ == '__main__':
    main()
