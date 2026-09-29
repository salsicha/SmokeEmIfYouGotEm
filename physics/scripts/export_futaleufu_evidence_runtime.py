"""Export the evidence-based Futaleufu Terminator cook as runtime data (numpy only).

Inputs: the evidence folder (build_futaleufu_evidence_grid.py), the scenario
root (build_curvilinear_river_scenario.py), the raftsim_water_solver run and
its compare_river_cook.py report, and a Sentinel-2 window for colour.

Outputs under physics/data/real_world/futaleufu_river_chile:
  scenario_terminator_evidence_2026/
    scenario/, cooked_flow_fields/ (raftsim.cooked_flow_fields.v1, band
    high_runnable_400cms, render-only baseline and observed-whitewater RSBF
    fields), runtime/moving_water_streaming.json, evidence/
  terrain/terminator_evidence_2026/
    heightfield 2017^2 over the evidence window, 2048^2 drape, backdrop mesh
    and drape, local centreline, runtime coordinate map, terrain manifest.

Frames: UTM 18S (EPSG:32718) metres; local = E - x0, N - y_centre; the
coordinate map declares world_y_sign -1; Unreal Z cm = (EGM2008 height -
datum) * 100. Colour: Sentinel-2 L2A true colour at 10 m (no finer open
imagery exists here), albedo-scaled like the Pacuare drape. Terrain beyond
the window: Copernicus GLO-30 (a surface model; forest canopy included).
"""
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from export_hance_evidence_runtime import (bilinear, read_frame, smooth_fill,  # noqa: E402
                                           write_png_rgb, write_png_u16)
from build_futaleufu_evidence_grid import UTM18S, catmull_rom, load_glo30  # noqa: E402
from geo_frames import tm_inverse  # noqa: E402
from solver_face_discharge import face_discharge  # noqa: E402

DATA = ROOT / 'physics/data/real_world/futaleufu_river_chile'
SRC = DATA / 'futaleufu_sources_2026_09'
BAND = 'high_runnable_400cms'
LANDSCAPE = 2017
DRAPE = 2048
BACKDROP_DRAPE = 2048
BACKDROP_CELL = 20.0
BACKDROP_EXTENT_M = 3000.0
BACKDROP_MARGIN_M = 3.0
BACKDROP_RING_M, BACKDROP_RING_DROP_M = 20.0, 0.5
ALBEDO_MEDIAN, ALBEDO_CAP = 0.07, 0.45
WET_BED_DARKENING = 0.55


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()


def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()


def write_rsbf(path, ny, nx, origin_y, d, surface, energy, wet):
    with open(path, 'wb') as fb:
        fb.write(struct.pack('<IIiiff', 0x52534246, 1, ny, nx, float(origin_y), float(d)))
        for arr, fmt in ((np.arange(nx, dtype=np.float32) * np.float32(d), '<f4'), (np.ascontiguousarray(surface.T), '<f4'),
                         (np.ascontiguousarray(energy.T), '<f4'), (np.ascontiguousarray(wet.T), 'u1')):
            flat = arr.astype(fmt).ravel()
            fb.write(struct.pack('<i', flat.size)); fb.write(flat.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path)
    ap.add_argument('scenario_root', type=Path)
    ap.add_argument('run', type=Path)
    ap.add_argument('compare', type=Path)
    ap.add_argument('--sentinel2', type=Path, required=True, help='fetch_sentinel2_window.py .npz (blue, green, red)')
    ap.add_argument('--sentinel2-manifest', type=Path, required=True)
    ap.add_argument('--solver-binary', type=Path, default=ROOT / 'tmp/hance-solver-build/raftsim_water_solver.exe')
    ap.add_argument('--steps', type=int, required=True)
    ap.add_argument('--frame-interval', type=int, required=True)
    ap.add_argument('--window-station-extent-m', type=float, default=480.0)
    ap.add_argument('--window-advance-m', type=float, default=80.0)
    ap.add_argument('--bed-correction-file', type=Path, default=None,
                    help='where the bed correction named by the evidence manifest now lives (checked by its sha256)')
    args = ap.parse_args()
    scen_out = DATA / 'scenario_terminator_evidence_2026'; terr_out = DATA / 'terrain/terminator_evidence_2026'
    assert not scen_out.exists() and not terr_out.exists(), 'fresh output folders required'
    ev = args.evidence.resolve(); sr = args.scenario_root.resolve()
    evm = json.loads((ev / 'manifest.json').read_text())
    X0, Y1, NX, NY = evm['grid']['x0'], evm['grid']['y_top'], evm['grid']['nx'], evm['grid']['ny']
    sc = json.loads((sr / 'scenario/scenario.json').read_text())
    ny, nx, d = sc['grid']['ny'], sc['grid']['nx'], sc['grid']['dx']
    Q = sc['metadata']['provenance']['target_discharge_m3s']
    cmap = json.loads((sr / 'coordinate_map.json').read_text())
    ORIGIN = tuple(cmap['horizontal_origin_m']); DATUM = cmap['vertical_datum_m']
    frames = sorted((args.run / 'frames').glob('frame_*.csv'))
    f = read_frame(frames[-1], ny, nx); f0 = read_frame(frames[-2], ny, nx)
    bed = np.load(sr / 'scenario/bed.npy')
    solved = f['h'] > 0
    assert np.allclose((f['eta'] - f['h'])[solved], bed[solved], atol=1e-6), 'run does not belong to this scenario'
    ref = np.load(sr / 'reference.npz')
    compare = json.loads((args.compare / 'compare.json').read_text())

    # ---------------- cooked fields
    (scen_out / 'cooked_flow_fields' / BAND).mkdir(parents=True)
    shutil.copytree(sr / 'scenario', scen_out / 'scenario')
    h = np.where(f['h'] > 0, f['h'], 0.0)
    wet = f['wet'] > 0.5
    fields = dict(bed=(bed, 'float32', 'Bed elevation, EGM2008 orthometric height (m); source datum 0.', 'm'),
                  h=(h, 'float32', 'Water depth above bed.', 'm'),
                  u=(np.where(wet, f['u'], 0.0), 'float32', 'Depth-averaged velocity along +station (downstream).', 'm_per_s'),
                  v=(np.where(wet, f['v'], 0.0), 'float32', 'Depth-averaged velocity along the river-left normal.', 'm_per_s'),
                  wet_mask=(wet, 'uint8', '1 where the solver reports the cell wet.', 'boolean'))
    arrays = {}
    for name, (a, dt, desc, units) in fields.items():
        path = scen_out / 'cooked_flow_fields' / BAND / f'{name}.npy'
        np.save(path, np.ascontiguousarray(a.astype(dt)))
        arrays[name] = dict(file=f'{BAND}/{name}.npy', sha256=sha(path), shape=[ny, nx], dtype=dt, description=desc, units=units)
    speed = np.hypot(fields['u'][0], fields['v'][0])
    froude = np.where(h > 0.05, speed / np.sqrt(9.81 * np.maximum(h, 0.05)), 0.0)
    energy = np.clip(0.6 * np.clip((speed - 0.5) / 2.5, 0, 1) + 0.4 * np.clip((froude - 0.5) / 0.5, 0, 1), 0, 1)
    bwet = wet & (h > 0.05)
    base_path = scen_out / 'cooked_flow_fields' / f'support_band_field_{BAND}.bin'
    write_rsbf(base_path, ny, nx, sc['grid']['origin_y'], d, np.where(bwet, f['eta'], bed), energy, bwet)
    # observed whitewater (Sentinel-2 whitewater mask, appearance evidence) on the cooked grid
    evg = np.load(ev / 'evidence_grid.npz')
    wx, wy = ref['world_x'], ref['world_y']
    dxc, dyc = np.gradient(wx, axis=1), np.gradient(wy, axis=1); dxr, dyr = np.gradient(wx, axis=0), np.gradient(wy, axis=0)
    frac = np.zeros((ny, nx))
    for a_ in (np.arange(4) + 0.5) / 4 - 0.5:
        for b_ in (np.arange(4) + 0.5) / 4 - 0.5:
            px = wx + a_ * dxc + b_ * dxr; py = wy + a_ * dyc + b_ * dyr
            cc = np.floor(px - X0).astype(int); rr = np.floor(Y1 - py).astype(int)
            ok = (cc >= 0) & (cc < NX) & (rr >= 0) & (rr < NY)
            hit = np.zeros((ny, nx), bool); hit[ok] = evg['foam'][rr[ok], cc[ok]]
            frac += hit
    frac /= 16.0
    p_ = np.pad(frac, 1, mode='edge'); frac = 0.25 * p_[:-2, 1:-1] + 0.5 * p_[1:-1, 1:-1] + 0.25 * p_[2:, 1:-1]
    p_ = np.pad(frac, ((0, 0), (1, 1)), mode='edge'); frac = 0.25 * p_[:, :-2] + 0.5 * p_[:, 1:-1] + 0.25 * p_[:, 2:]
    obs_path = scen_out / 'cooked_flow_fields' / f'observed_whitewater_{BAND}.bin'
    write_rsbf(obs_path, ny, nx, sc['grid']['origin_y'], d, np.where(wet, f['eta'], bed), frac, np.ones((ny, nx), np.uint8))
    # Section discharge: the solver's exact face mass flux (the cell-centre
    # h*u sum overstates transport on steep wet/dry reaches).
    q_sec = face_discharge(args.solver_binary, sr / 'scenario', f)
    q_centre = (h * fields['u'][0]).sum(0) * d
    dh = np.abs(f['h'] - f0['h'])[wet]
    wet_in = wet[:, 0] & (h[:, 0] > 0.05); wet_out = wet[:, -1] & (h[:, -1] > 0.05)
    runtime_boundaries = [
        dict(edge='west', kind='inflow', stage=float(np.median(f['eta'][wet_in, 0])),
             velocity=[float((h[:, 0] * fields['u'][0][:, 0]).sum() / max(h[wet_in, 0].sum(), 1e-9)), 0.0],
             note='used only when a runtime crop touches the cooked grid inlet; the cook itself used a discharge profile'),
        dict(edge='east', kind='outflow', stage=float(np.median(f['eta'][wet_out, -1]))),
        dict(edge='south', kind='bank'), dict(edge='north', kind='bank')]
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    manifest = dict(
        schema='raftsim.cooked_flow_fields.v1', generator='physics/scripts/export_futaleufu_evidence_runtime.py',
        generated_on='2026-09-27', river_id='futaleufu', rapid_name='Terminator',
        section_id='terminator_evidence_2026', source_commit=git, source_package=rel(scen_out / 'scenario'), source_elevation_datum_m=0.0,
        grid=dict(crs='curvilinear: x station downstream along the smoothed Sentinel-2 wetted-extent midline (EPSG:32718), y positive '
                      'river-left; see terrain/terminator_evidence_2026/terminator_evidence_runtime_coordinate_map.json',
                  downstream_axis='+x', dx_m=d, dy_m=d, nx=nx, ny=ny, origin_x_m=0.0, origin_y_m=sc['grid']['origin_y'],
                  layout='row_major_c_order', index_to_world='station = origin_x_m + col * dx_m; lateral = origin_y_m + row * dy_m (cell-centred)'),
        solver=dict(solver='raftsim_water_cpp_v1', binary_sha256=sha(args.solver_binary), solver_mode='finite_volume', flux_scheme='hll',
                    spatial_order=2, boundary_mode='scenario', cfl=0.2, dry_tolerance=1e-06, fixed_dt_s=sc['fixed_dt'],
                    feature_strength_scale=0.0, roughness_scale=1.0, bed_slope_source_scale=1.0, disable_fixture_calibrations=True,
                    steps=args.steps, frame_interval_steps=args.frame_interval, simulated_seconds=args.steps * sc['fixed_dt']),
        bands=[dict(band_id=BAND, directory=BAND, scenario_id=sc['metadata']['scenario_id'], manning_n=sc['roughness'],
                    effective_manning_n=sc['roughness'], discharge_target_m3s=Q,
                    discharge_steady_m3s=dict(west=float(q_sec[2]), mid=float(np.median(q_sec[10:-10])), east=float(q_sec[-3]),
                                              method='exact numerical face mass flux of the last frame (solver --inspect-face-fluxes)'),
                    discharge_cell_centre_hu_sum_m3s=dict(
                        west=float(q_centre[2]), mid=float(np.median(q_centre[10:-10])), east=float(q_centre[-3]),
                        note='diagnostic only: the cell-centre momentum sum overstates the transported discharge on steep, shallow wet/dry reaches'),
                    convergence=dict(converged=False, compared_frames=[frames[-2].name, frames[-1].name],
                                     frame_spacing_s=args.frame_interval * sc['fixed_dt'], max_abs_dh_m=float(dh.max()),
                                     p95_abs_dh_m=float(np.percentile(dh, 95)),
                                     note='rapids keep unsteady eddies and hydraulic jumps; the p95 change is the settling measure'),
                    field_stats=dict(h_max_m=float(h.max()), h_mean_m=float(h[wet].mean()), wet_fraction=float(wet.mean()),
                                     speed_max_m_per_s=float(speed.max())),
                    runtime_boundaries=runtime_boundaries, arrays=arrays,
                    presentation_baseline=dict(file=base_path.name, sha256=sha(base_path), format='RSBF v1 rows=station cols=lateral',
                                               energy='0.6*clip((speed-0.5)/2.5) + 0.4*clip((Froude-0.5)/0.5), render only'),
                    observed_whitewater=dict(file=obs_path.name, sha256=sha(obs_path),
                                             format='RSBF v1 rows=station cols=lateral; energy channel = whitewater fraction 0-1',
                                             source='Sentinel-2 whitewater (mean of 2020-02-20, 2024-02-19, 2026-01-04; 10 m); '
                                                    'flows on the image dates unknown',
                                             sampling='4 x 4 sub-points per cell, one 1-2-1 pass per axis',
                                             provenance='measured appearance (photographed whitewater extent); not predicted by the solver',
                                             use='render-only floor on the displayed live foam and the far-field cue; never gameplay'),
                    scenario_input_sha256={n: sha(sr / 'scenario' / n) for n in ('scenario.json', 'bed.npy', 'initial_state.npz')})],
        provenance=dict(evidence_manifest=evm,
                        measured=['Copernicus GLO-30 terrain (surface model, canopy included) beyond the bank zone',
                                  'water-surface anchors from the GLO-30 edited water surface (TanDEM-X 2011-2015, flow unknown, about +-2 m)',
                                  'Sentinel-2 10 m wetted extent and whitewater (three dates)'],
                        inferred=['surface between anchors (drops placed by whitewater)', 'bed (discharge-consistent for 400 m3/s, no bathymetry)',
                                  'bank zone shape', 'submerged boulders', 'discharge (planning band; DGA records not downloaded)', 'roughness',
                                  'velocities'],
                        validation=compare),
        notes=['Accepted only as described in docs/reconstruction-review-2026-09-07/futaleufu-terminator-evidence.md; not survey-grade.'])
    (scen_out / 'cooked_flow_fields/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (scen_out / 'evidence').mkdir()
    for srcf, name in ((ev / 'manifest.json', 'evidence_manifest.json'), (ev / 'profile.json', 'evidence_profile.json'),
                       (ev / 'boulders.json', 'inferred_boulders.json'), (ev / 'centreline.json', 'evidence_centreline.json'),
                       (sr / 'build_report.json', 'scenario_build_report.json'), (args.compare / 'compare.json', 'cook_compare.json')):
        shutil.copyfile(srcf, scen_out / 'evidence' / name)
    for png in ('classes.png', 'terrain_depth.png'):
        shutil.copyfile(ev / png, scen_out / 'evidence' / ('evidence_' + png))
    for png in ('profile.png', 'depth_speed_agreement.png'):
        shutil.copyfile(args.compare / png, scen_out / 'evidence' / ('cook_' + png))
    corr = evm.get('parameters', {}).get('bed_correction')
    if corr:
        # repo-relative, or relative to physics/scripts (where the builder may run)
        cp = next(c for c in ((args.bed_correction_file.resolve() if args.bed_correction_file else None), Path(corr), ROOT / corr,
                              (ROOT / 'physics/scripts' / corr).resolve()) if c is not None and c.is_absolute() and c.exists())
        assert sha(cp) == evm['parameters']['bed_correction_sha256']
        shutil.copyfile(cp, scen_out / 'evidence' / 'bed_correction.npz')
    (scen_out / 'runtime').mkdir()
    cm_path = scen_out / 'cooked_flow_fields/manifest.json'
    (scen_out / 'runtime/moving_water_streaming.json').write_text(json.dumps(dict(
        schema='raftsim.south_fork.moving_water_streaming.v1',
        purpose='Moving live-solver window for the evidence-based Futaleufu Terminator reach: the cooked field is cropped around the raft.',
        full_reach_transit_seed=dict(cooked_fields_manifest=rel(cm_path), cooked_fields_manifest_sha256=sha(cm_path)),
        windows=[dict(window_id='futaleufu_terminator_evidence_full', cooked_fields_manifest=rel(cm_path), station_range_m=[0.0, (nx - 1) * d],
                      note='single source field; the streamer only re-centres the crop')],
        moving_window=dict(station_extent_m=args.window_station_extent_m, lateral_extent_m=(ny - 1) * d, advance_m=args.window_advance_m),
        settled_hydraulics=False, procedural_reference_field=False), indent=2) + '\n')

    # ---------------- terrain (Landscape): the evidence surface (inferred bed in the channel)
    terr_out.mkdir(parents=True)
    ebed = evg['bed'].astype(np.float64)
    SPAN_X, SPAN_Y = float(NX), float(NY)
    jj = np.arange(LANDSCAPE) * (SPAN_X / (LANDSCAPE - 1)); ii = np.arange(LANDSCAPE) * (SPAN_Y / (LANDSCAPE - 1))
    FX, FY = np.meshgrid(jj - 0.5, ii - 0.5)
    height = bilinear(ebed, FX, FY)
    tmin, tmax = float(height.min()), float(height.max()); relief = tmax - tmin
    hf = np.round((height - tmin) / relief * 65535.0).astype(np.uint16)
    hf_path = terr_out / 'terminator_evidence_heightfield_2017.png'
    write_png_u16(hf_path, hf)
    quant = hf.astype(np.float64) / 65535.0 * relief + tmin

    # ---------------- colour: Sentinel-2 true colour (10 m), albedo-scaled
    s2m = json.loads(args.sentinel2_manifest.read_text())
    item = next(i for i in s2m['items'] if i['npz'] == args.sentinel2.name)
    s2 = np.load(args.sentinel2); sw = item['window_utm_m']
    s2_rgb = np.stack([s2[k].astype(np.float64) * 1e-4 - 0.1 for k in ('red', 'green', 'blue')], -1)
    s2_valid = (s2['red'] > 0) & (s2['green'] > 0) & (s2['blue'] > 0)

    def sample_colour(E, N):
        """Linear surface reflectance at UTM 18S points and its validity."""
        sc_ = (E - sw['xmin']) / 10.0 - 0.5; sr_ = (sw['ymax'] - N) / 10.0 - 0.5
        sat_ = np.stack([bilinear(s2_rgb[..., k], sc_, sr_) for k in range(3)], -1)
        return np.clip(sat_, 0, 1), bilinear(s2_valid.astype(np.float32), sc_, sr_) > 0.99

    E4, N4 = np.meshgrid(X0 + np.arange(0, NX, 4) + 2, Y1 - np.arange(0, NY, 4) - 2)
    s4, sv4 = sample_colour(E4, N4)
    dry4 = sv4 & ~evg['river'][::4, ::4][:s4.shape[0], :s4.shape[1]]
    lum4 = 0.2126 * s4[..., 0] + 0.7152 * s4[..., 1] + 0.0722 * s4[..., 2]
    albedo_scale = ALBEDO_MEDIAN / max(float(np.median(lum4[dry4])), 1e-6)

    def to_albedo(sat_):
        return np.clip(sat_ * albedo_scale, 0, ALBEDO_CAP)

    DE, DN = np.meshgrid(X0 + (np.arange(DRAPE) + 0.5) * (SPAN_X / DRAPE), Y1 - (np.arange(DRAPE) + 0.5) * (SPAN_Y / DRAPE))
    s_d, sv_d = sample_colour(DE, DN)
    assert sv_d.all(), 'the Sentinel-2 window must cover the Landscape'
    alb = to_albedo(s_d)
    wr = np.clip(((np.arange(DRAPE) + 0.5) * (NY / DRAPE)).astype(int), 0, NY - 1)
    wc = np.clip(((np.arange(DRAPE) + 0.5) * (NX / DRAPE)).astype(int), 0, NX - 1)
    water_px = evg['river'][wr][:, wc]
    keep = ~water_px
    cont = np.zeros_like(alb)
    for k in range(3):
        cont[..., k] = smooth_fill(alb[..., k], keep, 16, iters=400)[0]
    alb = np.where(water_px[..., None], cont * WET_BED_DARKENING ** 2.2, alb)
    drape = np.round(np.clip(alb, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)
    drape_path = terr_out / f'terminator_evidence_drape_{DRAPE}.png'
    write_png_rgb(drape_path, drape)

    # ---------------- backdrop: Copernicus GLO-30 around the window
    bx0 = float(np.floor((X0 - BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    bx1 = float(np.ceil((X0 + SPAN_X + BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    by0 = float(np.floor((Y1 - SPAN_Y - BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    by1 = float(np.ceil((Y1 + BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    BW, BH = int((bx1 - bx0) / BACKDROP_CELL), int((by1 - by0) / BACKDROP_CELL)
    BE, BN = np.meshgrid(bx0 + (np.arange(BW) + 0.5) * BACKDROP_CELL, by1 - (np.arange(BH) + 0.5) * BACKDROP_CELL)
    dem_g, lon0, lat0, step = load_glo30()
    lon, lat = tm_inverse(BE, BN, UTM18S)
    back = catmull_rom(dem_g, (lat0 - lat) / step, (lon - lon0) / step)
    del dem_g
    z3 = back.copy()
    under = (BE > X0) & (BE < X0 + SPAN_X) & (BN > Y1 - SPAN_Y) & (BN < Y1)
    inside = ((BE > X0 + BACKDROP_RING_M) & (BE < X0 + SPAN_X - BACKDROP_RING_M)
              & (BN > Y1 - SPAN_Y + BACKDROP_RING_M) & (BN < Y1 - BACKDROP_RING_M))
    land_here = bilinear(ebed, BE - X0 - 0.5, Y1 - BN - 0.5)
    land_lo = np.full(z3.shape, np.inf)
    for i_, j_ in zip(*np.nonzero(inside)):
        c0 = int(max(BE[i_, j_] - X0 - 25, 0)); c1 = int(min(BE[i_, j_] - X0 + 25, NX))
        r0 = int(max(Y1 - BN[i_, j_] - 25, 0)); r1 = int(min(Y1 - BN[i_, j_] + 25, NY))
        land_lo[i_, j_] = ebed[r0:r1, c0:c1].min()
    z3 = np.where(under & ~inside, np.minimum(z3, land_here) - BACKDROP_RING_DROP_M, z3)
    z3 = np.where(inside, np.minimum(z3, land_lo) - BACKDROP_MARGIN_M, z3)
    idx = np.arange(BH * BW).reshape(BH, BW)
    a_, b_, c_, d_ = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]
    quad = ~(inside[:-1, :-1] & inside[:-1, 1:] & inside[1:, :-1] & inside[1:, 1:])
    tri = np.concatenate([np.stack([a_[quad], b_[quad], c_[quad]], 1), np.stack([b_[quad], d_[quad], c_[quad]], 1)])
    e0, n0 = float(BE[0, 0]), float(BN[0, 0])
    xyz_all = np.stack([(BE - e0).ravel(), (BN - n0).ravel(), (z3 - DATUM).ravel()], 1)
    used = np.zeros(len(xyz_all), bool); used[tri.ravel()] = True
    remap = -np.ones(len(xyz_all), np.int64); remap[used] = np.arange(int(used.sum()))
    xyz_b = xyz_all[used]; tri_b = remap[tri]
    backdrop_path = terr_out / 'terminator_evidence_backdrop_glo30_20m.npz'
    np.savez_compressed(backdrop_path, xyz_local_m=xyz_b, triangles=tri_b)
    BDE, BDN = np.meshgrid(bx0 + (np.arange(BACKDROP_DRAPE) + 0.5) * ((bx1 - bx0) / BACKDROP_DRAPE),
                           by1 - (np.arange(BACKDROP_DRAPE) + 0.5) * ((by1 - by0) / BACKDROP_DRAPE))
    s_b, sv_b = sample_colour(BDE, BDN)
    bdrape = np.round(np.clip(to_albedo(s_b), 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)
    bdrape_path = terr_out / f'terminator_evidence_backdrop_drape_{BACKDROP_DRAPE}.png'
    write_png_rgb(bdrape_path, bdrape)

    # ---------------- centreline (Unreal frame) and coordinate map
    ox, oy = ORIGIN
    pts = np.array(cmap['points'])
    E, N = pts[:, 1] + ox, pts[:, 2] + oy
    midr = ny // 2
    surf = np.array([np.median(f['eta'][wet[:, j], j]) if wet[:, j].any() else np.nan for j in range(nx)])
    surf = np.interp(np.arange(nx), np.nonzero(np.isfinite(surf))[0], surf[np.isfinite(surf)])
    bedc = np.array([np.median(bed[wet[:, j], j]) if wet[:, j].any() else bed[midr, j] for j in range(nx)])
    cl = dict(schema='raftsim.local_centerline.v1', river_id='futaleufu', section_id='terminator_evidence_2026',
              local_metric_policy=f'Unreal frame: X = (E - {X0:.0f}) m * 100, Y = ({Y1:.0f} - N) m * 100 from the Landscape north-west corner; '
                                  'E/N EPSG:32718 UTM 18S; heights EGM2008 orthometric',
              points=[dict(station_m=float(s), unreal_local_cm=[float((e - X0) * 100), float((Y1 - n) * 100)],
                           conditioned_visual_surface_elevation_m=float(zs), conditioned_visual_bed_elevation_m=float(zb),
                           conditioned_visual_surface_normalized=float((zs - tmin) / relief),
                           conditioned_visual_bed_normalized=float((zb - tmin) / relief))
                      for s, e, n, zs, zb in zip(pts[:, 0], E, N, surf, bedc)])
    cl_path = terr_out / 'terminator_evidence_local_centerline.json'
    cl_path.write_text(json.dumps(cl, indent=1) + '\n')
    cm_out = terr_out / 'terminator_evidence_runtime_coordinate_map.json'
    cm_out.write_text(json.dumps(cmap, indent=1) + '\n')
    land_at_cells = bilinear(quant, (wx - X0) / (SPAN_X / (LANDSCAPE - 1)), (Y1 - wy) / (SPAN_Y / (LANDSCAPE - 1)))
    diff = (land_at_cells - bed)[wet]
    tm = dict(schema='raftsim.futaleufu.terminator_evidence_terrain.v1',
              status='evidence_based_reconstruction_glo30_terrain_inferred_bed',
              river_id='futaleufu', section_id='terminator_evidence_2026',
              inputs=dict(evidence_manifest=rel(scen_out / 'evidence/evidence_manifest.json'), evidence_grid_sha256=sha(ev / 'evidence_grid.npz'),
                          sources_manifest=rel(SRC / 'manifest.json'), sources_manifest_sha256=sha(SRC / 'manifest.json'),
                          sentinel2=dict(npz=args.sentinel2.name, sha256=sha(args.sentinel2), datetime=item['datetime']), glo30=evm['inputs']['glo30']),
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
                             world_origin_epsg32718_m=dict(west_edge_e=X0, centre_n=ORIGIN[1]), world_min_x_cm=0.0),
              drape=dict(size_px=[DRAPE, DRAPE], source='Sentinel-2 L2A true colour at 10 m (' + item['datetime'][:10] + '), bilinear',
                         under_water=f'Sentinel-2 water replaced by the continuation of dry-bank colours x {WET_BED_DARKENING} (sRGB) (invented bed colour)',
                         albedo_median=ALBEDO_MEDIAN, albedo_cap=ALBEDO_CAP, albedo_scale=float(albedo_scale),
                         uv=f'U = world_x / {SPAN_X * 100:.0f} cm; V = (world_y + {SPAN_Y * 50:.0f}) / {SPAN_Y * 100:.0f} cm (north up)',
                         note='10 m satellite colour with its capture lighting and canopy; appearance evidence, not albedo'),
              composition=dict(class_share={str(k): float((evg['class_code'] == k).mean()) for k in range(5)},
                               terrain='Copernicus GLO-30 bicubic beyond the bank zone; harmonic bank zone between the water edge and GLO-30'),
              backdrop=dict(mesh=rel(backdrop_path), vertices=int(len(xyz_b)), triangles=int(len(tri_b)), spacing_m=BACKDROP_CELL,
                            source=f'Copernicus GLO-30 (bicubic) on a {BACKDROP_CELL:.0f} m UTM grid, {BACKDROP_EXTENT_M:.0f} m around the Landscape',
                            origin_epsg32718_m=[e0, n0], xyz='local metres east, north, height - datum from origin',
                            actor_translation_cm=[(e0 - ORIGIN[0]) * 100.0, -(n0 - ORIGIN[1]) * 100.0, 0.0], actor_scale=[1.0, -1.0, 1.0],
                            expected_mesh_bounds_cm=[(xyz_b.min(0) * 100).tolist(), (xyz_b.max(0) * 100).tolist()],
                            mesh_frame='imported static mesh: X east, Y north (cm) from the origin; the actor scale (1, -1, 1) maps it to Unreal +Y south',
                            under_landscape=f'outside the Landscape: unchanged; under it within {BACKDROP_RING_M:.0f} m of the edge: {BACKDROP_RING_DROP_M} m below; '
                                            f'deeper: {BACKDROP_MARGIN_M} m below the lowest Landscape height within 25 m, quads fully inside dropped',
                            drape=dict(file=rel(bdrape_path), size_px=[BACKDROP_DRAPE, BACKDROP_DRAPE], north_up=True,
                                       uv=f'U = (world_x + {(ORIGIN[0] - bx0) * 100:.0f}) / {(bx1 - bx0) * 100:.0f} cm; '
                                          f'V = (world_y + {(by1 - ORIGIN[1]) * 100:.0f}) / {(by1 - by0) * 100:.0f} cm'),
                            collision=False, note='GLO-30 is a surface model: forest canopy is part of the shape'),
              solver_consistency=dict(terrain_minus_solver_bed_wet_cells_m_p5_p50_p95=np.percentile(diff, [5, 50, 95]).tolist()))
    (terr_out / 'terminator_evidence_terrain_manifest.json').write_text(json.dumps(tm, indent=2) + '\n')
    print(json.dumps(dict(landscape=tm['landscape'], consistency=tm['solver_consistency'],
                          backdrop={k: tm['backdrop'][k] for k in ('vertices', 'triangles', 'actor_translation_cm')},
                          albedo_scale=float(albedo_scale)), indent=1))


if __name__ == '__main__':
    main()
