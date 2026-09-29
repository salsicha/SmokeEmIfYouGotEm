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
                                          (3DEP 10 m outside the 2021 corridor DEM)
    hance_evidence_drape_4096x2048.png    2021 orthophoto colour over the same extent
    hance_evidence_backdrop_3dep_10m.npz  always-loaded 3DEP backdrop mesh, 6.5 km window
    hance_evidence_backdrop_drape_2048.png  its colour (terrain-conditioned palette)
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
from solver_face_discharge import face_discharge  # noqa: E402

DATA = ROOT / 'physics/data/real_world/colorado_river_grand_canyon_rowing'
SRC = DATA / 'hance_sources_2026_09'
X0, Y1, NXE, NYE = 211300.0, 560300.0, 2500, 1212
ORIGIN = (211300.0, 559694.0)
SPAN_X, SPAN_Y = 2500.0, 1212.0
LANDSCAPE = 2017
DATUM = 740.0
EDGE_TRIM_M = 10
# USGS 3DEP 10 m (NAVD88) over a 6.5 km window: measured terrain outside the
# 2021 corridor DEM and the always-loaded backdrop beyond the Landscape.
DEP = SRC / 'backdrop_3dep/hance_3dep_10m_6404.tif'
DEP_X0, DEP_Y1, DEP_CELL = 209300.0, 563100.0, 10.0
EDGE_BLEND_M = 150.0      # corridor-edge residual fades to pure 3DEP over this distance
BACKDROP_MARGIN_M = 3.0   # backdrop well under the Landscape stays this far below it
BACKDROP_RING_M, BACKDROP_RING_DROP_M = 20.0, 0.5   # under the Landscape edge ring
BACKDROP_DRAPE = 2048
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


def bicubic(a, fx, fy):
    """Catmull-Rom sample of a at fractional cell-centre coordinates (col, row), clamped; row-chunked.
    Upsampling 10 m 3DEP with bilinear leaves grid-aligned slope creases that lighting shows."""
    out = np.empty(fx.shape)
    H, W = a.shape

    def weights(t):
        t2, t3 = t * t, t * t * t
        return (-0.5 * t3 + t2 - 0.5 * t, 1.5 * t3 - 2.5 * t2 + 1.0, -1.5 * t3 + 2.0 * t2 + 0.5 * t, 0.5 * t3 - 0.5 * t2)
    for r in range(0, fx.shape[0], 128):
        x = fx[r:r + 128]; y = fy[r:r + 128]
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
        wx = weights(x - x0); wy = weights(y - y0)
        acc = np.zeros(x.shape)
        for j in range(4):
            rows = np.clip(y0 - 1 + j, 0, H - 1)
            line = np.zeros(x.shape)
            for i in range(4):
                line += wx[i] * a[rows, np.clip(x0 - 1 + i, 0, W - 1)]
            acc += wy[j] * line
        out[r:r + 128] = acc
    return out


def bilinear_rgb(t, fa, fb):
    """t[a, b, 3] sampled at fractional indices (fa along a, fb along b), clamped; row-chunked."""
    out = np.empty(fa.shape + (3,))
    fa2 = fa.reshape(fa.shape[0], -1) if fa.ndim > 1 else fa[None]
    fb2 = fb.reshape(fb.shape[0], -1) if fb.ndim > 1 else fb[None]
    o2 = out.reshape(fa2.shape + (3,))
    for r in range(0, fa2.shape[0], 128):
        a = fa2[r:r + 128]; b = fb2[r:r + 128]
        a0 = np.clip(np.floor(a).astype(int), 0, t.shape[0] - 2); b0 = np.clip(np.floor(b).astype(int), 0, t.shape[1] - 2)
        u = np.clip(a - a0, 0, 1)[..., None]; v = np.clip(b - b0, 0, 1)[..., None]
        o2[r:r + 128] = (t[a0, b0] * (1 - u) * (1 - v) + t[a0 + 1, b0] * u * (1 - v)
                         + t[a0, b0 + 1] * (1 - u) * v + t[a0 + 1, b0 + 1] * u * v)
    return out


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
    ap.add_argument('--terrain-only', action='store_true',
                    help='rewrite only terrain/hance_evidence_2021 (fresh); the cooked export must already exist and is not touched')
    args = ap.parse_args()
    scen_out = DATA / 'scenario_hance_evidence_2021'; terr_out = DATA / 'terrain/hance_evidence_2021'
    if args.terrain_only:
        assert scen_out.exists() and not terr_out.exists(), 'terrain-only: existing cooked export and a fresh terrain folder required'
    else:
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

    wet = f['wet'] > 0.5
    runtime_boundaries = None
    if not args.terrain_only:
        # ---------------- scenario + cooked fields
        (scen_out / 'cooked_flow_fields' / BAND).mkdir(parents=True)
        shutil.copytree(sr / 'scenario', scen_out / 'scenario')
        arrays = {}
        h = np.where(f['h'] > 0, f['h'], 0.0)
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
        # Section discharge: the solver's exact face mass flux. The cell-centre
        # h*u sum overstated it here by 1-2 % (the first export reported it).
        q_sec = face_discharge(args.solver_binary, sr / 'scenario', f)
        q_centre = (h * fields['u'][0]).sum(0) * d
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
                        discharge_steady_m3s=dict(west=float(q_sec[2]), mid=float(np.median(q_sec[10:-10])), east=float(q_sec[-3]),
                                                  method='exact numerical face mass flux of the last frame (solver --inspect-face-fluxes)'),
                        discharge_cell_centre_hu_sum_m3s=dict(
                            west=float(q_centre[2]), mid=float(np.median(q_centre[10:-10])), east=float(q_centre[-3]),
                            note='diagnostic only: the cell-centre momentum sum overstates the transported discharge on steep, shallow wet/dry reaches'),
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
    # Outside the 2021 corridor DEM (it reaches ~200-250 m from the channel):
    # USGS 3DEP 10 m (NAVD88). Its offset to the corridor's NAD83(2011)
    # ellipsoid heights (the geoid separation, about -23 m here) is measured
    # over dry measured ground. The remaining corridor-edge residual (1 m
    # photogrammetry against 10 m 3DEP) is extended harmonically from the
    # edge and faded out over EDGE_BLEND_M, so the outside is pure 3DEP.
    dep, dgeo, _ = read_geotiff(DEP)
    assert dgeo['corner_utm_m'] == (DEP_X0, DEP_Y1) and dgeo['cell_m'] == (DEP_CELL, DEP_CELL)
    dep = dep.astype(np.float64)
    CE, CN = np.meshgrid(X0 + np.arange(NXE) + 0.5, Y1 - np.arange(NYE) - 0.5)  # evidence cell centres
    dep_at = bicubic(dep, (CE - DEP_X0) / DEP_CELL - 0.5, (DEP_Y1 - CN) / DEP_CELL - 0.5)
    dry_measured = core & (cls == 0) & ~missing
    off = (ebed - dep_at)[dry_measured]
    dep_offset = float(np.median(off))
    depz = dep_at + dep_offset
    ext, dist_out = smooth_fill(np.where(dry_measured, ebed - depz, 0.0), dry_measured, 8)
    fade = np.clip(1.0 - dist_out / EDGE_BLEND_M, 0.0, 1.0) ** 2
    filled = np.where(missing, depz + ext * fade, ebed)
    # Continuity at the measured edge: relax harmonically within 40 m of it.
    band = missing & (dist_out < 40.0)
    for _ in range(600):  # Jacobi: measured cells and the outer 3DEP stay fixed
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

    # River level for colour: 3DEP is hydro-flattened, so the river is its
    # flat low cells; each point takes the level of the nearest river cell.
    dgy, dgx = np.gradient(dep, DEP_CELL)
    dep_slope = np.hypot(dgx, dgy)
    river3 = (dep_slope < 0.02) & (dep < np.percentile(dep, 2) + 40.0)
    rr3, rc3 = np.nonzero(river3)
    lvl_step = 2  # 20 m lattice
    lr, lc = np.mgrid[0:dep.shape[0]:lvl_step, 0:dep.shape[1]:lvl_step]
    level = np.empty(lr.shape)
    flat_r, flat_c = lr.ravel(), lc.ravel(); out_l = level.ravel()
    for k in range(0, len(flat_r), 2048):
        d2 = (flat_r[k:k + 2048, None] - rr3[None]) ** 2 + (flat_c[k:k + 2048, None] - rc3[None]) ** 2
        out_l[k:k + 2048] = dep[rr3, rc3][d2.argmin(1)]
    level = out_l.reshape(lr.shape) + dep_offset

    def river_level(e, n):
        return bilinear(level, (e - DEP_X0) / (DEP_CELL * lvl_step) - 0.5 / lvl_step, (DEP_Y1 - n) / (DEP_CELL * lvl_step) - 0.5 / lvl_step)

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
        band_k = bilinear(rgb[..., k], FX2, FY2)
        lin[..., k] = np.clip((band_k - lo[k]) / (hi[k] - lo[k]), 0, 1) ** 2.2
    lum = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    albedo_scale = ALBEDO_MEDIAN / max(float(np.median(lum[vmask])), 1e-6)
    alb = np.clip(lin * albedo_scale, 0, ALBEDO_CAP)
    g_ev = np.load(ev / 'evidence_grid.npz')
    wr = np.clip(((np.arange(DH) + 0.5) * (NYE / DH)).astype(int), 0, NYE - 1)
    wc = np.clip(((np.arange(DW) + 0.5) * (NXE / DW)).astype(int), 0, NXE - 1)
    water_px = g_ev['river'][wr][:, wc]
    keep = vmask & ~water_px
    # Outside the imagery footprint the colour is invented, but conditioned on
    # the measured terrain: the photo's median albedo per (slope, height above
    # the river) bin, interpolated between bin centres, applied to the 3DEP
    # slopes and heights. Slopes use a 10 m smoothing everywhere so the photo
    # statistics and the 3DEP terrain share one scale.
    blk = 10
    Hc, Wc = NYE // blk, NXE // blk
    coarse_z = filled[:Hc * blk, :Wc * blk].reshape(Hc, blk, Wc, blk).mean((1, 3))
    cgy, cgx = np.gradient(coarse_z, float(blk))
    coarse_slope = np.degrees(np.arctan(np.hypot(cgx, cgy)))
    px_e = X0 + (np.arange(DW) + 0.5) * (SPAN_X / DW); px_n = Y1 - (np.arange(DH) + 0.5) * (SPAN_Y / DH)
    PE, PN = np.meshgrid(px_e, px_n)
    slope_px = bilinear(coarse_slope, (PE - X0) / blk - 0.5, (Y1 - PN) / blk - 0.5)
    z_px = bilinear(filled, PE - X0 - 0.5, Y1 - PN - 0.5)
    hrel_px = z_px - river_level(PE, PN)
    S_EDGES = np.array([0, 8, 16, 24, 32, 40, 50, 90.0]); H_EDGES = np.array([-10, 3, 10, 25, 50, 100, 200, 2000.0])
    s_idx = np.clip(np.searchsorted(S_EDGES, slope_px[keep]) - 1, 0, len(S_EDGES) - 2)
    h_idx = np.clip(np.searchsorted(H_EDGES, hrel_px[keep]) - 1, 0, len(H_EDGES) - 2)
    table = np.full((len(S_EDGES) - 1, len(H_EDGES) - 1, 3), np.nan); counts = np.zeros(table.shape[:2], int)
    kc = alb[keep]
    for a_ in range(table.shape[0]):
        for b_ in range(table.shape[1]):
            sel = (s_idx == a_) & (h_idx == b_)
            counts[a_, b_] = int(sel.sum())
            if counts[a_, b_] >= 400:
                table[a_, b_] = np.median(kc[sel], axis=0)
    # empty bins: nearest filled bin along height, then along slope
    for a_ in range(table.shape[0]):
        ok = np.nonzero(np.isfinite(table[a_, :, 0]))[0]
        if len(ok):
            for b_ in range(table.shape[1]):
                if not np.isfinite(table[a_, b_, 0]):
                    table[a_, b_] = table[a_, ok[np.abs(ok - b_).argmin()]]
    for b_ in range(table.shape[1]):
        ok = np.nonzero(np.isfinite(table[:, b_, 0]))[0]
        for a_ in range(table.shape[0]):
            if not np.isfinite(table[a_, b_, 0]):
                table[a_, b_] = table[ok[np.abs(ok - a_).argmin()], b_] if len(ok) else np.median(kc, axis=0)
    s_ctr = 0.5 * (S_EDGES[:-1] + S_EDGES[1:]); h_ctr = 0.5 * (H_EDGES[:-1] + H_EDGES[1:]); h_ctr[-1] = 300.0

    def palette(slope_deg, hrel):
        fs = np.interp(slope_deg, s_ctr, np.arange(len(s_ctr))); fh = np.interp(hrel, h_ctr, np.arange(len(h_ctr)))
        return bilinear_rgb(table, fs, fh)

    pal = palette(slope_px, hrel_px)
    # Under water the photo shows the 2021 water surface (dark water and
    # whitewater), not the bed; seen through the transparent live water it
    # read as a bright bed. Replace imagery water with a smooth continuation
    # of the surrounding dry-bank colours, darkened for wet ground.
    cont = np.zeros_like(alb); dist_fp = None
    for k in range(3):
        cont[..., k], dist_fp = smooth_fill(alb[..., k], keep, 16, iters=400)
    px_m = SPAN_X / DW
    w_pal = np.clip(dist_fp * px_m / 60.0, 0.0, 1.0)[..., None]
    outside = ~vmask & ~water_px
    alb_out = np.where(keep[..., None], alb, cont)
    alb_out = np.where(outside[..., None], (1 - w_pal) * cont + w_pal * pal, alb_out)
    alb_out = np.where(water_px[..., None], cont * WET_BED_DARKENING ** 2.2, alb_out)
    drape = np.round(np.clip(alb_out, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)
    drape_path = terr_out / 'hance_evidence_drape_4096x2048.png'
    write_png_rgb(drape_path, drape)

    # ---------------- always-loaded backdrop beyond the Landscape (3DEP, 10 m)
    # Vertices at the 3DEP cell centres of the whole 6.5 km window; outside
    # the Landscape they keep the measured 3DEP heights (lowering them there
    # left a shadowed trench along the Landscape edge). Under the Landscape,
    # within BACKDROP_RING_M of its edge, a vertex sits BACKDROP_RING_DROP_M
    # below the Landscape at that point: the Landscape there is the same 3DEP
    # surface (Catmull-Rom passes through these samples), so the seam stays
    # closed. Deeper inside, vertices sit BACKDROP_MARGIN_M below the lowest
    # Landscape height within 25 m and quads fully inside are dropped, so the
    # Landscape always wins. No collision (installer).
    rows3, cols3 = dep.shape
    e3 = DEP_X0 + (np.arange(cols3) + 0.5) * DEP_CELL; n3 = DEP_Y1 - (np.arange(rows3) + 0.5) * DEP_CELL
    E3, N3 = np.meshgrid(e3, n3)
    z3 = dep + dep_offset
    under = (E3 > X0) & (E3 < X0 + SPAN_X) & (N3 > Y1 - SPAN_Y) & (N3 < Y1)
    inside = ((E3 > X0 + BACKDROP_RING_M) & (E3 < X0 + SPAN_X - BACKDROP_RING_M)
              & (N3 > Y1 - SPAN_Y + BACKDROP_RING_M) & (N3 < Y1 - BACKDROP_RING_M))
    land_here = bilinear(filled, E3 - X0 - 0.5, Y1 - N3 - 0.5)
    land_lo = np.full(z3.shape, np.inf)
    for i_, j_ in zip(*np.nonzero(inside)):
        c0_ = int(max(E3[i_, j_] - X0 - 25, 0)); c1_ = int(min(E3[i_, j_] - X0 + 25, NXE))
        r0_ = int(max(Y1 - N3[i_, j_] - 25, 0)); r1_ = int(min(Y1 - N3[i_, j_] + 25, NYE))
        land_lo[i_, j_] = filled[r0_:r1_, c0_:c1_].min()
    z3 = np.where(under & ~inside, np.minimum(z3, land_here) - BACKDROP_RING_DROP_M, z3)
    z3 = np.where(inside, np.minimum(z3, land_lo) - BACKDROP_MARGIN_M, z3)
    idx = np.arange(rows3 * cols3).reshape(rows3, cols3)
    a_, b_, c_, d_ = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]
    quad = ~(inside[:-1, :-1] & inside[:-1, 1:] & inside[1:, :-1] & inside[1:, 1:])
    tri = np.concatenate([np.stack([a_[quad], b_[quad], c_[quad]], 1), np.stack([b_[quad], d_[quad], c_[quad]], 1)])
    xyz_all = np.stack([(E3 - e3[0]).ravel(), (N3 - n3[0]).ravel(), (z3 - DATUM).ravel()], 1)
    used = np.zeros(len(xyz_all), bool); used[tri.ravel()] = True
    remap = -np.ones(len(xyz_all), np.int64); remap[used] = np.arange(int(used.sum()))
    xyz_b = xyz_all[used]; tri_b = remap[tri]
    backdrop_path = terr_out / 'hance_evidence_backdrop_3dep_10m.npz'
    np.savez_compressed(backdrop_path, xyz_local_m=xyz_b, triangles=tri_b)
    # Backdrop colour (2048^2 over the window, north up): the same palette on
    # 3DEP slope and height above the river; the river itself takes the
    # photo's median open-water colour (whitewater excluded).
    BD = BACKDROP_DRAPE
    span3 = cols3 * DEP_CELL
    be = DEP_X0 + (np.arange(BD) + 0.5) * (span3 / BD); bn = DEP_Y1 - (np.arange(BD) + 0.5) * (span3 / BD)
    BE, BN = np.meshgrid(be, bn)
    sl3 = np.degrees(np.arctan(dep_slope))
    bslope = bilinear(sl3, (BE - DEP_X0) / DEP_CELL - 0.5, (DEP_Y1 - BN) / DEP_CELL - 0.5)
    bz = bilinear(dep, (BE - DEP_X0) / DEP_CELL - 0.5, (DEP_Y1 - BN) / DEP_CELL - 0.5) + dep_offset
    bcol = palette(bslope, bz - river_level(BE, BN))
    water_lum = 0.2126 * alb[..., 0] + 0.7152 * alb[..., 1] + 0.0722 * alb[..., 2]
    open_water = water_px & vmask & (water_lum < 2.0 * np.median(water_lum[water_px & vmask]))
    water_colour = np.median(alb[open_water], axis=0)
    briver = bilinear(river3.astype(np.float64), (BE - DEP_X0) / DEP_CELL - 0.5, (DEP_Y1 - BN) / DEP_CELL - 0.5)
    bcol = np.where((briver > 0.5)[..., None], water_colour, bcol)
    bdrape = np.round(np.clip(bcol, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)
    bdrape_path = terr_out / f'hance_evidence_backdrop_drape_{BD}.png'
    write_png_rgb(bdrape_path, bdrape)
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
                           runtime_coordinate_map=rel(cm_out), runtime_coordinate_map_sha256=sha(cm_out),
                           backdrop_mesh=rel(backdrop_path), backdrop_mesh_sha256=sha(backdrop_path),
                           backdrop_drape=rel(bdrape_path), backdrop_drape_sha256=sha(bdrape_path)),
              landscape=dict(size_px=LANDSCAPE, pixel_format='16_bit_grayscale_png', north_up=True,
                             horizontal_span_x_m=SPAN_X, horizontal_span_y_m=SPAN_Y,
                             sample_spacing_x_m=SPAN_X / (LANDSCAPE - 1), sample_spacing_y_m=SPAN_Y / (LANDSCAPE - 1),
                             terrain_min_m=tmin, terrain_max_m=tmax, target_relief_cm=relief * 100.0,
                             world_vertical_offset_cm=(tmin - DATUM) * 100.0, runtime_vertical_datum_m=DATUM,
                             world_origin_epsg6404_m=dict(west_edge_e=X0, centre_n=ORIGIN[1]), world_min_x_cm=0.0),
              drape=dict(size_px=[DW, DH], source='2021 corridor imagery 0.5 m export, bands R,G,B', stretch_percentiles=[0.5, 99.7],
                         outside_footprint='invented colour conditioned on measured terrain: the photo median albedo per (10 m slope, height above '
                                           'the 3DEP river level) bin, interpolated, on the 3DEP terrain; blended over 60 m from the footprint '
                                           'edge with the smooth continuation of measured colours',
                         palette=dict(slope_edges_deg=S_EDGES.tolist(), height_above_river_edges_m=H_EDGES.tolist(),
                                      samples_per_bin=counts.tolist(), min_samples=400),
                         under_water=f'imagery water replaced by the continuation of dry-bank colours x {WET_BED_DARKENING} (sRGB) (invented bed colour)',
                         footprint_share=float(vmask.mean()),
                         albedo_median=ALBEDO_MEDIAN, albedo_cap=ALBEDO_CAP, albedo_scale=float(albedo_scale), uv='U = world_x / 250000 cm; V = (world_y + 60600) / 121200 cm (north up)',
                         note='orthophoto colour with its capture lighting and shadows; appearance evidence, not albedo'),
              composition=dict(class_share={str(k): float((cls == k).mean()) for k in range(5)}, nan_filled_share=float(missing.mean()),
                               edge_trim_m=EDGE_TRIM_M,
                               nan_fill=f'outside the 2021 corridor DEM: USGS 3DEP 10 m (NAVD88, Catmull-Rom upsampled) + {dep_offset:.3f} m (median corridor DEM minus 3DEP '
                                        f'over dry measured ground), plus the corridor-edge residual extended harmonically and faded out over '
                                        f'{EDGE_BLEND_M:.0f} m, relaxed within 40 m of the edge; measured terrain at 10 m'),
              dep_3dep=dict(source=rel(DEP), sha256=sha(DEP), offset_to_ellipsoid_m=dep_offset,
                            corridor_minus_3dep_dry_m_p10_p50_p90=np.percentile(off, [10, 50, 90]).tolist(), dry_samples=int(off.size),
                            river_cells_10m=int(river3.sum()), river_rule='3DEP slope < 0.02 and below the 2nd percentile + 40 m (hydro-flattened)'),
              backdrop=dict(mesh=rel(backdrop_path), vertices=int(len(xyz_b)), triangles=int(len(tri_b)), spacing_m=DEP_CELL,
                            origin_epsg6404_m=[float(e3[0]), float(n3[0])], xyz='local metres east, north, height - datum from origin',
                            actor_translation_cm=[(float(e3[0]) - ORIGIN[0]) * 100.0, -(float(n3[0]) - ORIGIN[1]) * 100.0, 0.0],
                            actor_scale=[1.0, -1.0, 1.0],
                            expected_mesh_bounds_cm=[(xyz_b.min(0) * 100).tolist(), (xyz_b.max(0) * 100).tolist()],
                            mesh_frame='imported static mesh: X east, Y north (cm) from the origin; the actor scale (1, -1, 1) '
                                       'maps it to Unreal +Y south',
                            under_landscape=f'outside the Landscape: 3DEP heights unchanged; under it within {BACKDROP_RING_M:.0f} m of the '
                                            f'edge: {BACKDROP_RING_DROP_M} m below the Landscape at the vertex; deeper: {BACKDROP_MARGIN_M} m '
                                            f'below the lowest Landscape height within 25 m, quads fully inside dropped',
                            drape=dict(file=rel(bdrape_path), size_px=[BACKDROP_DRAPE, BACKDROP_DRAPE], north_up=True,
                                       uv=f'U = (world_x + {(ORIGIN[0] - DEP_X0) * 100:.0f}) / {cols3 * DEP_CELL * 100:.0f} cm; '
                                          f'V = (world_y + {(DEP_Y1 - ORIGIN[1]) * 100:.0f}) / {rows3 * DEP_CELL * 100:.0f} cm',
                                       colour='palette above on 3DEP slope/height (invented, terrain-conditioned); 3DEP river cells take the '
                                              'photo median open-water colour', water_colour_linear=water_colour.tolist()),
                            collision=False, note='measured 3DEP shape; colour invented'),
              solver_consistency=dict(terrain_minus_solver_bed_wet_cells_m_p5_p50_p95=np.percentile(diff, [5, 50, 95]).tolist(),
                                      note='Landscape 1.24 x 0.60 m bilinear resample of the 1 m evidence bed; solver bed is a 2 m box filter'))
    (terr_out / 'hance_evidence_terrain_manifest.json').write_text(json.dumps(tm, indent=2) + '\n')
    print(json.dumps(dict(terrain=tm['landscape'], consistency=tm['solver_consistency'], nan_filled=tm['composition']['nan_filled_share'],
                          dep=tm['dep_3dep'], backdrop={k: tm['backdrop'][k] for k in ('vertices', 'triangles', 'actor_translation_cm')},
                          boundaries=runtime_boundaries[:2] if runtime_boundaries else None), indent=1))


if __name__ == '__main__':
    main()
