"""Export an evidence-based Hance cook as the L_Hance runtime data set (numpy only).

Inputs: the evidence grid (build_hance_evidence_grid.py), the curvilinear
scenario (build_hance_curvilinear_scenario.py), the raftsim_water_solver run
that cooked it, and its compare_hance_cook.py report.

Outputs (fresh folders under physics/data/real_world/colorado_river_grand_canyon_rowing):
  scenario_hance_evidence_2021/
    scenario/              the solver package that produced the cook
    cooked_flow_fields/    raftsim.cooked_flow_fields.v1, band steady_8000cfs_2021,
                           arrays (ny, nx) = (lateral, station); bed/eta absolute
                           NAD83(2011) ellipsoid heights (source datum 0)
    runtime/moving_water_streaming.json
    evidence/              the evidence, boulder, profile, build and compare reports
  terrain/hance_evidence_2021/
    hance_evidence_heightfield_2017.png   16-bit, north up, the evidence bed/ground
    hance_evidence_drape_4096x2048.png    2021 orthophoto colour over the same extent
    hance_evidence_local_centerline.json  raftsim.local_centerline.v1 (Unreal frame)
    hance_evidence_runtime_coordinate_map.json
    hance_evidence_terrain_manifest.json

Frames. Local metres: east = E - 211300, north = N - 559694 (EPSG:6404). The
Landscape spans the evidence window (2500 x 1212 m), is anchored at world
X = 0 and centred in Y; Unreal +Y is south (the coordinate map declares
world_y_sign -1). Unreal Z cm = (ellipsoid height - vertical datum) * 100.
"""
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from tiff_numpy import read_geotiff  # noqa: E402

DATA = ROOT / 'physics/data/real_world/colorado_river_grand_canyon_rowing'
SRC = DATA / 'hance_sources_2026_09'
X0, Y1, NXE, NYE = 211300.0, 560300.0, 2500, 1212
ORIGIN = (211300.0, 559694.0)
SPAN_X, SPAN_Y = 2500.0, 1212.0
LANDSCAPE = 2017
DATUM = 740.0
FILL_RISE, FILL_RISE_CAP_M = 0.45, 350.0
EDGE_TRIM_M = 10
ALBEDO_MEDIAN, ALBEDO_CAP = 0.11, 0.45
WET_BED_DARKENING = 0.55
BAND = 'steady_8000cfs_2021'
Q = 226.534772736


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()


def png_chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def write_png_u16(path, a):
    h, w = a.shape
    raw = np.zeros((h, 1 + 2 * w), np.uint8)
    raw[:, 1:] = a.astype('>u2').view(np.uint8).reshape(h, 2 * w)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n' + png_chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 16, 0, 0, 0, 0))
                           + png_chunk(b'IDAT', zlib.compress(raw.tobytes(), 6)) + png_chunk(b'IEND', b''))


def write_png_rgb(path, rgb):
    h, w, _ = rgb.shape
    raw = np.zeros((h, 1 + 3 * w), np.uint8); raw[:, 1:] = rgb.reshape(h, 3 * w)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n' + png_chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + png_chunk(b'IDAT', zlib.compress(raw.tobytes(), 6)) + png_chunk(b'IEND', b''))


def fill_nan(a):
    """Pyramid push-pull fill of NaN cells (smooth, from surrounding values)."""
    if np.isfinite(a).all():
        return a.copy()
    levels = [a]
    while min(levels[-1].shape) > 2 and not np.isfinite(levels[-1]).all():
        c = levels[-1]
        H, W = (c.shape[0] + 1) // 2 * 2, (c.shape[1] + 1) // 2 * 2
        p = np.full((H, W), np.nan); p[:c.shape[0], :c.shape[1]] = c
        blk = p.reshape(H // 2, 2, W // 2, 2)
        cnt = np.isfinite(blk).sum((1, 3))
        levels.append(np.where(cnt > 0, np.nansum(blk, (1, 3)) / np.maximum(cnt, 1), np.nan))
    top = levels[-1]
    if not np.isfinite(top).all():
        top = np.where(np.isfinite(top), top, np.nanmean(top))
    for c in reversed(levels[:-1]):
        up = np.repeat(np.repeat(top, 2, 0), 2, 1)[:c.shape[0], :c.shape[1]]
        top = np.where(np.isfinite(c), c, up)
    return top


def smooth_fill(a, valid, block, iters=600):
    """Fill invalid cells smoothly: block means on a coarse grid, push-pull,
    Jacobi relaxation with measured blocks held, bilinear back to full size.
    Also returns the Euclidean distance (full-size cells) to measured data."""
    H, W = a.shape
    Hc, Wc = -(-H // block), -(-W // block)
    pa = np.zeros((Hc * block, Wc * block)); pv = np.zeros_like(pa)
    pa[:H, :W] = np.where(valid, a, 0.0); pv[:H, :W] = valid
    sums = pa.reshape(Hc, block, Wc, block).sum((1, 3)); cnt = pv.reshape(Hc, block, Wc, block).sum((1, 3))
    coarse = np.where(cnt > 0, sums / np.maximum(cnt, 1), np.nan)
    fixed = cnt >= 0.5 * block * block
    c = fill_nan(coarse)
    for _ in range(iters):
        p_ = np.pad(c, 1, mode='edge')
        sm = (p_[:-2, 1:-1] + p_[2:, 1:-1] + p_[1:-1, :-2] + p_[1:-1, 2:] + 4 * c) / 8.0
        c = np.where(fixed, coarse, sm)
    fy = (np.arange(H) + 0.5) / block - 0.5; fx = (np.arange(W) + 0.5) / block - 0.5
    FX, FY = np.meshgrid(fx, fy)
    up = bilinear(c, FX, FY)
    # Euclidean distance on the coarse grid to the nearest measured block
    rr, cc = np.nonzero(cnt > 0)
    edge = np.zeros_like(fixed)
    m = cnt > 0
    edge[rr, cc] = True
    inner = m.copy(); inner[1:-1, 1:-1] = m[1:-1, 1:-1] & m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:]
    er, ec = np.nonzero(edge & ~inner)
    qr, qc = np.nonzero(~m)
    dist_c = np.zeros((Hc, Wc))
    for k in range(0, len(qr), 4096):
        d2 = (qr[k:k + 4096, None] - er[None, :]) ** 2 + (qc[k:k + 4096, None] - ec[None, :]) ** 2
        dist_c[qr[k:k + 4096], qc[k:k + 4096]] = np.sqrt(d2.min(1)) * block
    dist = bilinear(dist_c, FX, FY)
    return np.where(valid, a, up), np.where(valid, 0.0, dist)


def bilinear(a, fx, fy):
    """a sampled at fractional cell-centre coordinates (col, row), clamped."""
    c = np.clip(np.floor(fx).astype(int), 0, a.shape[1] - 2); r = np.clip(np.floor(fy).astype(int), 0, a.shape[0] - 2)
    u = np.clip(fx - c, 0, 1); v = np.clip(fy - r, 0, 1)
    return a[r, c] * (1 - u) * (1 - v) + a[r, c + 1] * u * (1 - v) + a[r + 1, c] * (1 - u) * v + a[r + 1, c + 1] * u * v


def read_frame(path, ny, nx):
    a = np.loadtxt(path, delimiter=',', skiprows=1)
    names = 'row,col,x,y,h,eta,u,v,hu,hv,wet,normal_x,normal_y,normal_z,froude'.split(',')
    return {n: a[:, k].reshape(ny, nx) for k, n in enumerate(names)}


def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('evidence', type=Path)
    ap.add_argument('scenario_root', type=Path)
    ap.add_argument('run', type=Path, help='raftsim_water_solver output folder (holds frames/ and manifest.json)')
    ap.add_argument('compare', type=Path)
    ap.add_argument('--solver-binary', type=Path, default=ROOT / 'tmp/hance-solver-build/raftsim_water_solver.exe')
    ap.add_argument('--steps', type=int, required=True)
    ap.add_argument('--frame-interval', type=int, required=True)
    ap.add_argument('--window-station-extent-m', type=float, default=480.0)
    ap.add_argument('--window-advance-m', type=float, default=80.0)
    args = ap.parse_args()
    scen_out = DATA / 'scenario_hance_evidence_2021'; terr_out = DATA / 'terrain/hance_evidence_2021'
    assert not scen_out.exists() and not terr_out.exists(), 'fresh output folders required'
    ev = args.evidence.resolve(); sr = args.scenario_root.resolve()
    sc = json.loads((sr / 'scenario/scenario.json').read_text())
    ny, nx, d = sc['grid']['ny'], sc['grid']['nx'], sc['grid']['dx']
    frames = sorted((args.run / 'frames').glob('frame_*.csv'))
    f = read_frame(frames[-1], ny, nx); f0 = read_frame(frames[-2], ny, nx)
    bed = np.load(sr / 'scenario/bed.npy')
    assert bed.shape == (ny, nx)
    solved = f['h'] > 0
    assert np.allclose((f['eta'] - f['h'])[solved], bed[solved], atol=1e-6), 'run does not belong to this scenario'
    ref = np.load(sr / 'reference.npz')
    cmap = json.loads((sr / 'coordinate_map.json').read_text())
    assert tuple(cmap['horizontal_origin_epsg6404_m']) == ORIGIN and cmap['vertical_datum_m'] == DATUM
    compare = json.loads((args.compare / 'compare.json').read_text())

    # ---------------- scenario + cooked fields
    (scen_out / 'cooked_flow_fields' / BAND).mkdir(parents=True)
    shutil.copytree(sr / 'scenario', scen_out / 'scenario')
    arrays = {}
    h = np.where(f['h'] > 0, f['h'], 0.0)
    wet = f['wet'] > 0.5
    fields = dict(bed=(bed, 'float32', 'Bed elevation, NAD83(2011) ellipsoid height (m); source datum 0.', 'm'),
                  h=(h, 'float32', 'Water depth above bed.', 'm'),
                  u=(np.where(wet, f['u'], 0.0), 'float32', 'Depth-averaged velocity along +station (downstream).', 'm_per_s'),
                  v=(np.where(wet, f['v'], 0.0), 'float32', 'Depth-averaged velocity along the river-left normal.', 'm_per_s'),
                  wet_mask=(wet, 'uint8', '1 where the solver reports the cell wet.', 'boolean'))
    for name, (a, dt, desc, units) in fields.items():
        path = scen_out / 'cooked_flow_fields' / BAND / f'{name}.npy'
        np.save(path, np.ascontiguousarray(a.astype(dt)))
        arrays[name] = dict(file=f'{BAND}/{name}.npy', sha256=sha(path), shape=[ny, nx], dtype=dt, description=desc, units=units)
    # render-only presentation baseline for curved maps (RSBF v1, read by
    # URaftSimWaterRuntimeAdapter::LoadPresentationBaselineFieldFromFile):
    # rows = stations, columns = lateral; absolute surface, energy, wet.
    speed = np.hypot(fields['u'][0], fields['v'][0])
    froude = np.where(h > 0.05, speed / np.sqrt(9.81 * np.maximum(h, 0.05)), 0.0)
    energy = np.clip(0.6 * np.clip((speed - 0.5) / 2.5, 0, 1) + 0.4 * np.clip((froude - 0.5) / 0.5, 0, 1), 0, 1)
    bwet = wet & (h > 0.05)
    base_path = scen_out / 'cooked_flow_fields' / f'support_band_field_{BAND}.bin'
    with open(base_path, 'wb') as fb:
        fb.write(struct.pack('<IIiiff', 0x52534246, 1, ny, nx, float(sc['grid']['origin_y']), float(d)))
        for arr, fmt in ((np.arange(nx, dtype=np.float32) * np.float32(d), '<f4'),
                         (np.ascontiguousarray(np.where(bwet, f['eta'], bed).T), '<f4'),
                         (np.ascontiguousarray(energy.T), '<f4'), (np.ascontiguousarray(bwet.T), 'u1')):
            flat = arr.astype(fmt).ravel()
            fb.write(struct.pack('<i', flat.size)); fb.write(flat.tobytes())
    q_sec = (h * fields['u'][0]).sum(0) * d
    dh = np.abs(f['h'] - f0['h'])[wet]; du = np.abs(f['u'] - f0['u'])[wet]; dv = np.abs(f['v'] - f0['v'])[wet]
    wet_in = wet[:, 0] & (h[:, 0] > 0.05); wet_out = wet[:, -1] & (h[:, -1] > 0.05)
    runtime_boundaries = [
        dict(edge='west', kind='inflow', stage=float(np.median(f['eta'][wet_in, 0])),
             velocity=[float((h[:, 0] * fields['u'][0][:, 0]).sum() / max(h[wet_in, 0].sum(), 1e-9)), 0.0],
             note='used only when a runtime crop touches the cooked grid inlet; the cook itself used a discharge profile'),
        dict(edge='east', kind='outflow', stage=float(np.median(f['eta'][wet_out, -1]))),
        dict(edge='south', kind='bank'), dict(edge='north', kind='bank')]
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    evm = json.loads((ev / 'manifest.json').read_text())
    manifest = dict(
        schema='raftsim.cooked_flow_fields.v1', generator='physics/scripts/export_hance_evidence_runtime.py',
        generated_on='2026-09-26', river_id='colorado_river_grand_canyon_rowing', rapid_name='Hance',
        section_id='hance_evidence_2021', source_commit=git, source_package=rel(scen_out / 'scenario'),
        source_elevation_datum_m=0.0,
        grid=dict(crs='curvilinear: x station downstream along the smoothed 2021 channel centreline (EPSG:6404), y positive river-left; '
                      'see terrain/hance_evidence_2021/hance_evidence_runtime_coordinate_map.json',
                  downstream_axis='+x', dx_m=d, dy_m=d, nx=nx, ny=ny, origin_x_m=0.0, origin_y_m=sc['grid']['origin_y'],
                  layout='row_major_c_order', index_to_world='station = origin_x_m + col * dx_m; lateral = origin_y_m + row * dy_m (cell-centred)'),
        solver=dict(solver='raftsim_water_cpp_v1', binary_sha256=sha(args.solver_binary), solver_mode='finite_volume', flux_scheme='hll',
                    spatial_order=2, boundary_mode='scenario', cfl=0.2, dry_tolerance=1e-06, fixed_dt_s=sc['fixed_dt'],
                    feature_strength_scale=0.0, roughness_scale=1.0, bed_slope_source_scale=1.0, disable_fixture_calibrations=True,
                    preserve_initial_mass=False, steps=args.steps, frame_interval_steps=args.frame_interval,
                    simulated_seconds=args.steps * sc['fixed_dt']),
        bands=[dict(band_id=BAND, directory=BAND, scenario_id=sc['metadata']['scenario_id'], manning_n=sc['roughness'],
                    effective_manning_n=sc['roughness'], discharge_target_m3s=Q, discharge_target_cfs=8000.0,
                    discharge_steady_m3s=dict(west=float(q_sec[2]), mid=float(np.median(q_sec[10:-10])), east=float(q_sec[-3])),
                    convergence=dict(converged=False, compared_frames=[frames[-2].name, frames[-1].name],
                                     frame_spacing_s=args.frame_interval * sc['fixed_dt'],
                                     max_abs_dh_m=float(dh.max()), p95_abs_dh_m=float(np.percentile(dh, 95)),
                                     max_abs_du_m_per_s=float(du.max()), max_abs_dv_m_per_s=float(dv.max()),
                                     note='rapids keep unsteady eddies and hydraulic jumps; the p95 change is the settling measure'),
                    field_stats=dict(h_max_m=float(h.max()), h_mean_m=float(h[wet].mean()), wet_fraction=float(wet.mean()),
                                     speed_max_m_per_s=float(np.hypot(fields['u'][0], fields['v'][0]).max())),
                    runtime_boundaries=runtime_boundaries, arrays=arrays,
                    presentation_baseline=dict(file=base_path.name, sha256=sha(base_path), format='RSBF v1 rows=station cols=lateral',
                                               energy='0.6*clip((speed-0.5)/2.5) + 0.4*clip((Froude-0.5)/0.5), render only'),
                    scenario_input_sha256={n: sha(sr / 'scenario' / n) for n in ('scenario.json', 'bed.npy', 'initial_state.npz')})],
        provenance=dict(evidence_manifest=evm, measured=['2021 photogrammetric DEM (banks, emergent rocks)', '2014 sonar/total-station bed (pools)',
                                                         '2021 imagery water outline and whitewater'],
                        inferred=['bed inside the rapid (discharge-consistent, calibrated to the textured 2021 surface)',
                                  'submerged boulders located from imagery whitewater, heights from a pour-over assumption',
                                  'roughness', 'velocities (no measured velocity)'],
                        validation=compare),
        notes=['Accepted only as described in docs/reconstruction-review-2026-09-07/colorado-hance-evidence.md; not survey-grade.'])
    (scen_out / 'cooked_flow_fields/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (scen_out / 'evidence').mkdir()
    for srcf, name in ((ev / 'manifest.json', 'evidence_manifest.json'), (ev / 'profile.json', 'evidence_profile.json'),
                       (ev / 'boulders.json', 'inferred_boulders.json'), (ev / 'centreline.json', 'evidence_centreline.json'),
                       (sr / 'build_report.json', 'scenario_build_report.json'), (args.compare / 'compare.json', 'cook_compare.json')):
        shutil.copyfile(srcf, scen_out / 'evidence' / name)
    corr = evm.get('parameters', {}).get('bed_correction')
    if corr:
        # archive the cook calibration that built this evidence bed
        corr_path = Path(corr) if Path(corr).is_absolute() else ROOT / corr
        assert sha(corr_path) == evm['parameters']['bed_correction_sha256']
        shutil.copyfile(corr_path, scen_out / 'evidence' / 'bed_correction.npz')
    for png in ('profile.png', 'whitewater.png', 'wet_agreement.png', 'speed.png', 'surface_error.png'):
        shutil.copyfile(args.compare / png, scen_out / 'evidence' / ('cook_' + png))
    (scen_out / 'runtime').mkdir()
    cm_path = scen_out / 'cooked_flow_fields/manifest.json'
    stream = dict(schema='raftsim.south_fork.moving_water_streaming.v1',
                  purpose='Moving live-solver window for the 2.5 km evidence-based Hance reach: the cooked field is cropped around the raft.',
                  full_reach_transit_seed=dict(cooked_fields_manifest=rel(cm_path), cooked_fields_manifest_sha256=sha(cm_path)),
                  windows=[dict(window_id='hance_evidence_full', cooked_fields_manifest=rel(cm_path), station_range_m=[0.0, (nx - 1) * d],
                                note='single source field; the streamer only re-centres the crop')],
                  moving_window=dict(station_extent_m=args.window_station_extent_m, lateral_extent_m=(ny - 1) * d, advance_m=args.window_advance_m),
                  settled_hydraulics=False, procedural_reference_field=False)
    (scen_out / 'runtime/moving_water_streaming.json').write_text(json.dumps(stream, indent=2) + '\n')

    # ---------------- terrain
    terr_out.mkdir(parents=True)
    g = np.load(ev / 'evidence_grid.npz')
    ebed = g['bed'].astype(np.float64); cls = g['class_code']
    # Photogrammetric DEM edges are unreliable (isolated high cells at the
    # corridor boundary read as spires from the river): drop the outermost
    # EDGE_TRIM_M of measured ground and let the fill take over there.
    core = np.isfinite(ebed)
    for _ in range(EDGE_TRIM_M):
        k_ = core.copy()
        k_[1:] &= core[:-1]; k_[:-1] &= core[1:]; k_[:, 1:] &= core[:, :-1]; k_[:, :-1] &= core[:, 1:]
        core = k_
    ebed = np.where(core | (cls > 0), ebed, np.nan)
    missing = ~np.isfinite(ebed)
    # Outside the 2021 corridor DEM (it reaches ~200-250 m from the channel)
    # the canyon keeps rising; a flat push-pull fill would read as plateaus.
    # Presentation fill: smooth continuation plus a rise of FILL_RISE per metre
    # from the measured edge, capped. Invented, not measured (manifest).
    smooth, dist_out = smooth_fill(ebed, ~missing, 8)
    # Continuity at the measured edge: the coarse fill averages 8 m blocks and
    # can sit tens of metres off a cliff-top edge cell (a one-pixel wall seen
    # as a needle). Relax the fill harmonically within 40 m of the edge.
    filled = smooth + np.where(missing, np.minimum(FILL_RISE * dist_out, FILL_RISE_CAP_M), 0.0)
    band = missing & (dist_out < 40.0)
    for _ in range(600):  # Jacobi: measured cells and the deep fill stay fixed
        p_ = np.pad(filled, 1, mode='edge')
        filled = np.where(band, 0.25 * (p_[:-2, 1:-1] + p_[2:, 1:-1] + p_[1:-1, :-2] + p_[1:-1, 2:]), filled)
    jj = np.arange(LANDSCAPE) * (SPAN_X / (LANDSCAPE - 1)); ii = np.arange(LANDSCAPE) * (SPAN_Y / (LANDSCAPE - 1))
    FX, FY = np.meshgrid(jj - 0.5, ii - 0.5)  # evidence cell centres sit at +0.5 m
    height = bilinear(filled, FX, FY)
    tmin, tmax = float(height.min()), float(height.max())
    relief = tmax - tmin
    hf = np.round((height - tmin) / relief * 65535.0).astype(np.uint16)
    hf_path = terr_out / 'hance_evidence_heightfield_2017.png'
    write_png_u16(hf_path, hf)
    quant = hf.astype(np.float64) / 65535.0 * relief + tmin
    # drape: the 0.5 m 2021 orthophoto over the same window, 4096 x 2048
    img, gi, _ = read_geotiff(SRC / 'imagery_2021/hance_broad_0p5m.tif')
    assert gi['corner_utm_m'] == (X0, Y1) and gi['cell_m'] == (0.5, 0.5)
    rgb = img[..., :3].astype(np.float32)
    valid = img.sum(-1) > 0
    lo = np.percentile(rgb[valid], 0.5, axis=0); hi = np.percentile(rgb[valid], 99.7, axis=0)
    DW, DH = 4096, 2048
    fx = (np.arange(DW) + 0.5) * (img.shape[1] / DW) - 0.5; fy = (np.arange(DH) + 0.5) * (img.shape[0] / DH) - 0.5
    FX2, FY2 = np.meshgrid(fx, fy)
    vmask = bilinear(valid.astype(np.float32), FX2, FY2) > 0.5
    # The orthophoto already contains the capture sunlight; used as albedo it
    # is lit again. Stretch the bands, then scale linear colour so the median
    # ground luminance is ALBEDO_MEDIAN (typical canyon rock/soil albedo),
    # capped at ALBEDO_CAP. One global factor: relative colour is unchanged.
    lin = np.zeros((DH, DW, 3))
    for k in range(3):
        band = bilinear(rgb[..., k], FX2, FY2)
        lin[..., k] = np.clip((band - lo[k]) / (hi[k] - lo[k]), 0, 1) ** 2.2
    lum = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    albedo_scale = ALBEDO_MEDIAN / max(float(np.median(lum[vmask])), 1e-6)
    drape = np.round(np.clip(lin * albedo_scale, 0, ALBEDO_CAP) ** (1 / 2.2) * 255).astype(np.uint8)
    # Under water the photo shows the 2021 water surface (dark water and
    # whitewater), not the bed; seen through the transparent live water it
    # read as a bright bed. Replace imagery water with a smooth continuation
    # of the surrounding dry-bank colours, darkened for wet ground. Outside
    # the imagery footprint, continue the measured colours outward. Both are
    # invented presentation colour, labelled in the manifest.
    g_ev = np.load(ev / 'evidence_grid.npz')
    wr = np.clip(((np.arange(DH) + 0.5) * (NYE / DH)).astype(int), 0, NYE - 1)
    wc = np.clip(((np.arange(DW) + 0.5) * (NXE / DW)).astype(int), 0, NXE - 1)
    water_px = g_ev['river'][wr][:, wc]
    keep = vmask & ~water_px
    for k in range(3):
        drape[..., k] = np.round(np.clip(smooth_fill(drape[..., k].astype(np.float64), keep, 16, iters=400)[0], 0, 255))
    drape[water_px] = np.round(drape[water_px] * WET_BED_DARKENING).astype(np.uint8)
    drape_path = terr_out / 'hance_evidence_drape_4096x2048.png'
    write_png_rgb(drape_path, drape)
    # centreline (Unreal frame) and coordinate map
    ox, oy = ORIGIN
    pts = np.array(cmap['points'])
    E, N = pts[:, 1] + ox, pts[:, 2] + oy
    mid = ny // 2
    surf = np.array([np.median(f['eta'][wet[:, j], j]) if wet[:, j].any() else np.nan for j in range(nx)])
    surf = np.interp(np.arange(nx), np.nonzero(np.isfinite(surf))[0], surf[np.isfinite(surf)])
    bedc = np.array([np.median(bed[wet[:, j], j]) if wet[:, j].any() else bed[mid, j] for j in range(nx)])
    assert len(pts) == nx
    cl = dict(schema='raftsim.local_centerline.v1', river_id='colorado_river', section_id='hance_evidence_2021',
              local_metric_policy='Unreal frame: X = (E - 211300) m * 100, Y = (560300 - N) m * 100 from the Landscape north-west corner; '
                                  'E/N EPSG:6404; heights NAD83(2011) ellipsoid',
              points=[dict(station_m=float(s), unreal_local_cm=[float((e - X0) * 100), float((Y1 - n) * 100)],
                           conditioned_visual_surface_elevation_m=float(zs), conditioned_visual_bed_elevation_m=float(zb),
                           conditioned_visual_surface_normalized=float((zs - tmin) / relief),
                           conditioned_visual_bed_normalized=float((zb - tmin) / relief))
                      for s, e, n, zs, zb in zip(pts[:, 0], E, N, surf, bedc)])
    cl_path = terr_out / 'hance_evidence_local_centerline.json'
    cl_path.write_text(json.dumps(cl, indent=1) + '\n')
    cm_out = terr_out / 'hance_evidence_runtime_coordinate_map.json'
    cm_out.write_text(json.dumps(cmap, indent=1) + '\n')
    # terrain vs solver bed consistency inside the cooked wet area
    wx, wy = ref['world_x'], ref['world_y']
    land_at_cells = bilinear(quant, (wx - X0) / (SPAN_X / (LANDSCAPE - 1)), (Y1 - wy) / (SPAN_Y / (LANDSCAPE - 1)))
    diff = (land_at_cells - bed)[wet]
    tm = dict(schema='raftsim.colorado.hance_evidence_terrain.v1',
              status='evidence_based_reconstruction_measured_ground_and_pools_inferred_rapid_bed',
              river_id='colorado_river', section_id='hance_evidence_2021',
              inputs=dict(evidence_manifest=rel(scen_out / 'evidence/evidence_manifest.json'),
                          evidence_grid_sha256=sha(ev / 'evidence_grid.npz'), sources_manifest=rel(SRC / 'manifest.json'),
                          sources_manifest_sha256=sha(SRC / 'manifest.json')),
              outputs=dict(heightfield=rel(hf_path), heightfield_sha256=sha(hf_path), drape=rel(drape_path), drape_sha256=sha(drape_path),
                           local_centerline=rel(cl_path), local_centerline_sha256=sha(cl_path),
                           runtime_coordinate_map=rel(cm_out), runtime_coordinate_map_sha256=sha(cm_out)),
              landscape=dict(size_px=LANDSCAPE, pixel_format='16_bit_grayscale_png', north_up=True,
                             horizontal_span_x_m=SPAN_X, horizontal_span_y_m=SPAN_Y,
                             sample_spacing_x_m=SPAN_X / (LANDSCAPE - 1), sample_spacing_y_m=SPAN_Y / (LANDSCAPE - 1),
                             terrain_min_m=tmin, terrain_max_m=tmax, target_relief_cm=relief * 100.0,
                             world_vertical_offset_cm=(tmin - DATUM) * 100.0, runtime_vertical_datum_m=DATUM,
                             world_origin_epsg6404_m=dict(west_edge_e=X0, centre_n=ORIGIN[1]), world_min_x_cm=0.0),
              drape=dict(size_px=[DW, DH], source='2021 corridor imagery 0.5 m export, bands R,G,B', stretch_percentiles=[0.5, 99.7],
                         outside_footprint='smooth outward continuation of measured colours (invented)',
                         under_water=f'imagery water replaced by the continuation of dry-bank colours x {WET_BED_DARKENING} (invented bed colour)',
                         footprint_share=float(vmask.mean()),
                         albedo_median=ALBEDO_MEDIAN, albedo_cap=ALBEDO_CAP, albedo_scale=float(albedo_scale), uv='U = world_x / 250000 cm; V = (world_y + 60600) / 121200 cm (north up)',
                         note='orthophoto colour with its capture lighting and shadows; appearance evidence, not albedo'),
              composition=dict(class_share={str(k): float((cls == k).mean()) for k in range(5)}, nan_filled_share=float(missing.mean()),
                               edge_trim_m=EDGE_TRIM_M,
                               nan_fill=f'outside the 2021 corridor DEM: pyramid push-pull from the measured edge plus {FILL_RISE} m rise per metre '
                                        f'from it (cap {FILL_RISE_CAP_M} m); invented presentation terrain, not measured'),
              solver_consistency=dict(terrain_minus_solver_bed_wet_cells_m_p5_p50_p95=np.percentile(diff, [5, 50, 95]).tolist(),
                                      note='Landscape 1.24 x 0.60 m bilinear resample of the 1 m evidence bed; solver bed is a 2 m box filter'))
    (terr_out / 'hance_evidence_terrain_manifest.json').write_text(json.dumps(tm, indent=2) + '\n')
    print(json.dumps(dict(terrain=tm['landscape'], consistency=tm['solver_consistency'], nan_filled=tm['composition']['nan_filled_share'],
                          boundaries=runtime_boundaries[:2]), indent=1))


if __name__ == '__main__':
    main()
