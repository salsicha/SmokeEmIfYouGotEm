"""Compare hydraulic spin-up snapshots without replacing shipped river fields.

The scene needs a resolved breaking control, not just nonzero downstream flux.
These measurements diagnose the existing interpreted channel; they are not a
photorealism gate or a claim that the bathymetry is surveyed.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np

from raftsim.dual_solver import CppSolverRunConfig, run_cpp_solver_scenario
from raftsim.scenario2_5d import InitialWaterState2_5D, read_scenario2_5d_package
from raftsim.south_fork_full_hydraulics import _troublemaker_s_bend_centerline_m


def validated_frame_state(scenario, data):
    """Reject incomplete/mismatched frames before constructing a warm start."""
    required = {'row', 'col', 'x', 'y', 'h', 'eta', 'u', 'v', 'hu', 'hv', 'wet'}
    if not required.issubset(data.dtype.names or ()):
        raise ValueError('resume frame is missing state columns')
    if data.size != scenario.grid.nx * scenario.grid.ny:
        raise ValueError('resume frame does not contain the complete grid')
    if any(not np.isfinite(data[name]).all() for name in required):
        raise ValueError('resume frame contains non-finite values')
    r, c = data['row'].astype(int), data['col'].astype(int)
    if (np.any(r != data['row']) or np.any(c != data['col']) or
            np.any(r < 0) or np.any(r >= scenario.grid.ny) or
            np.any(c < 0) or np.any(c >= scenario.grid.nx) or
            np.unique(r * scenario.grid.nx + c).size != data.size):
        raise ValueError('resume frame contains invalid or duplicate cell indices')
    if (not np.allclose(data['x'], scenario.grid.origin_x+c*scenario.grid.dx, atol=1e-8, rtol=0) or
            not np.allclose(data['y'], scenario.grid.origin_y+r*scenario.grid.dy, atol=1e-8, rtol=0)):
        raise ValueError('resume frame coordinates do not match this scenario')
    if np.any(data['h'] < 0) or not np.allclose(
            data['eta']-data['h'], scenario.bed[r, c], atol=1e-7, rtol=0):
        raise ValueError('resume frame depth/bed does not match this scenario')
    if (not np.allclose(data['hu'], data['h']*data['u'], atol=1e-8, rtol=1e-8) or
            not np.allclose(data['hv'], data['h']*data['v'], atol=1e-8, rtol=1e-8) or
            np.any((data['wet'] != 0) & (data['wet'] != 1)) or
            np.any(data['wet'].astype(bool) != (data['h'] > 1e-6))):
        raise ValueError('resume frame momentum or wet mask is inconsistent')
    arrays = {}
    for name in ['h', 'eta', 'u', 'v', 'hu', 'hv', 'wet']:
        arrays[name] = np.empty(scenario.grid.shape)
        arrays[name][r, c] = data[name]
    return InitialWaterState2_5D(depth=arrays['h'], eta=arrays['eta'],
        u=arrays['u'], v=arrays['v'], hu=arrays['hu'], hv=arrays['hv'], wet=arrays['wet'])


def warm_start(scenario, frame_path, elapsed_seconds):
    """Restart conserved fields with the same bed and constant boundaries.

    This is not a bitwise solver checkpoint: its internal clock is restarted.
    The diagnostic disables feature forcing and uses constant boundaries.
    """
    state = validated_frame_state(scenario, np.genfromtxt(frame_path, delimiter=',', names=True))
    provenance = {**scenario.metadata.provenance,
        'warm_start_frame': str(frame_path.resolve()),
        'warm_start_sha256': hashlib.sha256(frame_path.read_bytes()).hexdigest(),
        'warm_start_elapsed_seconds': elapsed_seconds, 'production_promoted': False}
    return replace(scenario, initial_state=state, metadata=replace(scenario.metadata,
        scenario_id=scenario.metadata.scenario_id+'_warm_start', provenance=provenance))


def interpreted_throat(scenario, width_m):
    """Raise a compact pair of shoulders, leaving the center sill/drop intact.

    Width is an experimental authoring choice, not a measurement from footage.
    No velocity forcing is applied during the solve. Initial section flux is
    preserved when the changed wetted area is initialized.
    """
    if not np.isfinite(width_m) or not 8 <= width_m <= 24:
        raise ValueError('experimental throat width must be 8–24 m')
    provenance = scenario.metadata.provenance
    station = float(provenance['station_m'])
    x, y = scenario.grid.meshgrid()
    center = _troublemaker_s_bend_centerline_m(x, station)
    def smooth(a, b, value):
        t = np.clip((value-a)/(b-a), 0., 1.)
        return t*t*(3.-2.*t)
    along = smooth(station-34., station-16., x) * (1.-smooth(station-6., station+12., x))
    across = smooth(width_m*.5-1.5, width_m*.5+1.5, abs(y-center))
    original = scenario.initial_state
    # Do not raise unrelated dry terrain beyond the existing wetted channel.
    weight = along*across*smooth(0., .2, original.depth)
    raised = np.maximum(scenario.bed, original.eta+.8)
    bed = scenario.bed + weight*(raised-scenario.bed)
    depth = np.maximum(original.eta-bed, 0.)
    changed_columns = np.any(bed != scenario.bed, axis=0)
    target_flux = np.sum(original.depth*original.u, axis=0)*scenario.grid.dy
    area = depth.sum(axis=0)*scenario.grid.dy
    velocity = target_flux/np.maximum(area, 1e-6)
    if np.any(velocity[changed_columns] > 8.):
        raise ValueError('experimental throat cannot convey initial flux below the 8 m/s seed limit')
    wet = depth > 1e-6
    u = np.where(changed_columns[None, :], np.where(wet, velocity[None, :], 0.), original.u)
    tangent = np.divide(original.v, original.u, out=np.zeros_like(original.v), where=abs(original.u)>1e-6)
    v = np.where(changed_columns[None, :], u*tangent, original.v)
    metadata = replace(scenario.metadata,
        scenario_id=scenario.metadata.scenario_id + '_throat_' + str(width_m).replace('.', 'p'),
        provenance={**provenance, 'experimental_throat_width_m': width_m,
                    'production_promoted': False, 'not_for_navigation': True})
    return replace(scenario, metadata=metadata, bed=bed,
        initial_state=InitialWaterState2_5D.from_depth_velocity(bed, depth, u, v))


def bank_connected_throat(scenario, width_m):
    """Distinct interpreted trial: tie shoulders into high ground, not wet cells.

    The legacy experiment is deliberately unchanged so saved frames retain
    their exact source bed. Crest level is relative to the original wet-channel
    stage, never dry-cell eta (which equals terrain). No surveyed width or
    elevation is claimed, and the centre sill/drop remains untouched.
    """
    legacy = interpreted_throat(scenario, width_m)  # Shared width/seed guards.
    station = float(scenario.metadata.provenance['station_m'])
    x, y = scenario.grid.meshgrid()
    center = _troublemaker_s_bend_centerline_m(x, station)
    def smooth(a, b, value):
        t = np.clip((value-a)/(b-a), 0., 1.)
        return t*t*(3.-2.*t)
    along = smooth(station-34., station-16., x) * (1.-smooth(station-6., station+12., x))
    across = smooth(width_m*.5-1.5, width_m*.5+1.5, abs(y-center))
    original = scenario.initial_state
    stage = np.ma.median(np.ma.masked_where(original.depth <= .1, original.eta), axis=0)
    active_columns = np.any(along > 0., axis=0)
    if np.any(np.ma.getmaskarray(stage)[active_columns]):
        raise ValueError('connected throat requires a wet-channel stage in every modified section')
    crest = stage.filled(0.)[None, :] + .8
    bed = scenario.bed + along*across*np.maximum(crest-scenario.bed, 0.)
    if np.any(bed-scenario.bed > 4.):
        raise ValueError('connected throat exceeds the four-metre experimental bed-change bound')
    if not np.array_equal(bed[[0, -1], :], scenario.bed[[0, -1], :]):
        raise ValueError('connected throat reaches a lateral domain boundary; widen the source corridor first')
    depth = np.maximum(original.eta-bed, 0.)
    changed = np.any(bed != scenario.bed, axis=0)
    flux = np.sum(original.depth*original.u, axis=0)
    area = depth.sum(axis=0)
    velocity = flux/np.maximum(area, 1e-6)
    if np.any(velocity[changed] > 8.):
        raise ValueError('connected throat cannot convey initial section flux below the 8 m/s seed bound')
    u = np.where(changed[None, :], np.where(depth > 1e-6, velocity[None, :], 0.), original.u)
    tangent = np.divide(original.v, original.u, out=np.zeros_like(original.v), where=abs(original.u)>1e-6)
    v = np.where(changed[None, :], u*tangent, original.v)
    metadata = replace(legacy.metadata,
        scenario_id=legacy.metadata.scenario_id+'_bank_connected_v1',
        provenance={**legacy.metadata.provenance,
                    'experimental_throat_shoulders': 'bank_connected_v1',
                    'experimental_shoulder_crest_above_initial_wet_stage_m': .8})
    return replace(scenario, metadata=metadata, bed=bed,
        initial_state=InitialWaterState2_5D.from_depth_velocity(bed, depth, u, v))


def measure(depth, u, v, stage, grid):
    x = grid.origin_x + np.arange(grid.nx) * grid.dx
    y = grid.origin_y + np.arange(grid.ny) * grid.dy
    speed = np.hypot(u, v)
    froude = speed / np.sqrt(9.80665 * np.maximum(depth, 1e-6))
    regions = []
    for start, end in [(8340, 8360), (8360, 8380), (8380, 8410), (8410, 8440)]:
        wet = (x[None, :] >= start) & (x[None, :] < end) & (abs(y[:, None]) < 15) & (depth > .1)
        forward_flux = depth*np.maximum(u, 0.)
        total_forward_flux = float(forward_flux[wet].sum())
        regions.append({
            'station_range_m': [start, end],
            'wet_cells': int(wet.sum()),
            'speed_p10_p50_p90_mps': np.percentile(speed[wet], [10, 50, 90]).tolist() if wet.any() else [],
            'froude_p50_p90_p99': np.percentile(froude[wet], [50, 90, 99]).tolist() if wet.any() else [],
            'supercritical_wet_fraction': float(np.mean(froude[wet] > 1)) if wet.any() else 0.,
            'supercritical_downstream_flux_fraction': float(forward_flux[wet & (froude > 1)].sum()) / max(total_forward_flux, 1e-12),
            'stage_p10_p50_p90_m': np.percentile(stage[wet], [10, 50, 90]).tolist() if wet.any() else [],
        })
    sections = []
    for station in [8180, 8348, 8362, 8378, 8400, 8440, 8550]:
        col = int(np.argmin(abs(x - station)))
        sections.append({'station_m': float(x[col]), 'discharge_m3s': float(np.sum(depth[:, col] * u[:, col]) * grid.dy)})
    return {'regions': regions, 'sections': sections, 'volume_m3': float(depth.sum() * grid.dx * grid.dy)}


def measure_throat_conveyance(depth, u, grid, rapid_station_m, width_m=12.):
    """Cell-centre section bands expose side-route flow, including its sign.

    The nominal width is an analysis band on the original-channel control,
    not a claim that its banks are that narrow. Partial edge cells are not
    reconstructed; retain dy and the explicit centre-selection convention.
    """
    xs = grid.origin_x + np.arange(grid.nx)*grid.dx
    ys = grid.origin_y + np.arange(grid.ny)*grid.dy
    sections = []
    for offset in (-28., -20., -16., -10., -6., 2.):
        col = int(np.argmin(abs(xs-(rapid_station_m+offset))))
        center = float(_troublemaker_s_bend_centerline_m(np.array(xs[col]), rapid_station_m))
        lateral = abs(ys-center)
        q = depth[:, col]*u[:, col]*grid.dy
        core = lateral <= width_m*.5
        outside = lateral > width_m*.5+3.
        forward = np.maximum(q, 0.)
        sections.append(dict(station_m=float(xs[col]), center_lateral_m=center,
            net_discharge_m3s=float(q.sum()), core_net_discharge_m3s=float(q[core].sum()),
            outside_net_discharge_m3s=float(q[outside].sum()),
            outside_forward_discharge_fraction=float(forward[outside].sum()/max(forward.sum(), 1e-12))))
    return dict(analysis_width_m=width_m, outer_band_margin_m=3., dy_m=grid.dy,
        convention='cell-centre membership; net hu*dy and positive-downstream flux fraction', sections=sections)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=96)
    parser.add_argument('--throat-width', type=float, default=None,
        help='Experimental interpreted constriction width, 8–24 m; writes only to output directory.')
    parser.add_argument('--bank-connected-shoulders', action='store_true',
        help='Separate interpreted variant tying shoulders into high ground; requires --throat-width.')
    parser.add_argument('--prescribed-discharge', type=float,
        help='Experimental constant west inflow in m3/s; frees inlet stage. No production promotion.')
    parser.add_argument('--resume-frame', type=Path,
        help='Full solver CSV snapshot from this exact bed/grid; does not replace shipped fields.')
    parser.add_argument('--resume-seconds', type=float, default=0.,
        help='Elapsed simulation time represented by the resume frame, for provenance only.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    rapid = root / 'physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/rapids/troublemaker'
    scenario_path = rapid / 'scenario/median_runnable'
    scenario = read_scenario2_5d_package(scenario_path)
    if not 9.6 <= args.seconds <= 600:
        parser.error('--seconds must be between 9.6 and 600')
    if args.bank_connected_shoulders and args.throat_width is None:
        parser.error('--bank-connected-shoulders requires --throat-width')
    if args.throat_width is not None:
        scenario = (bank_connected_throat if args.bank_connected_shoulders else interpreted_throat)(scenario, args.throat_width)
    if not np.isfinite(args.resume_seconds) or args.resume_seconds < 0 or (args.resume_seconds and not args.resume_frame):
        parser.error('--resume-seconds must be nonnegative and requires --resume-frame')
    if args.resume_frame:
        scenario = warm_start(scenario, args.resume_frame, args.resume_seconds)
    run = run_cpp_solver_scenario(scenario if args.throat_width is not None or args.resume_frame else scenario_path, output_dir=args.output, config=CppSolverRunConfig(
        executable=args.solver.resolve(), steps=round(args.seconds/scenario.fixed_dt), frame_interval=480,
        solver_mode='finite_volume', boundary_mode='scenario', flux_scheme='hll', cfl=.38,
        feature_strength_scale=0., roughness_scale=1., bed_slope_source_scale=1.,
        preserve_initial_mass=False, disable_fixture_calibrations=True, allow_validation_failure=True,
        experimental_west_discharge_m3s=args.prescribed_discharge))
    frames = json.loads(run.manifest_path.read_text())['frames']
    rows = []
    for frame_index, frame in enumerate(frames):
        data = np.genfromtxt(run.output_dir / frame, delimiter=',', names=True)
        arrays = {name: np.zeros(scenario.grid.shape) for name in ['h', 'u', 'v', 'eta']}
        r, c = data['row'].astype(int), data['col'].astype(int)
        for name in arrays:
            arrays[name][r, c] = data[name]
        rows.append({'frame_file': frame,
            'nominal_cumulative_seconds': args.resume_seconds + min(frame_index*480, round(args.seconds/scenario.fixed_dt))*scenario.fixed_dt,
            'throat_conveyance': measure_throat_conveyance(arrays['h'], arrays['u'], scenario.grid,
                float(scenario.metadata.provenance['station_m']), args.throat_width or 12.),
            **measure(arrays['h'], arrays['u'], arrays['v'], arrays['eta'], scenario.grid)})
    shipped = {name: np.load(rapid / 'cooked/median_runnable' / (name+'.npy')) for name in ['h', 'u', 'v', 'bed']}
    report = {'scope': 'Troublemaker median flow; diagnostic only; shipped arrays unchanged',
        'solver_command': list(run.command), 'solver_returncode': run.returncode,
        'runtime_seconds': run.runtime_seconds, 'requested_simulated_seconds': args.seconds,
        'initial_elapsed_seconds': args.resume_seconds,
        'warm_start_provenance': scenario.metadata.provenance if args.resume_frame else None,
        'experimental_throat_width_m': args.throat_width,
        'experimental_throat_shoulders': scenario.metadata.provenance.get('experimental_throat_shoulders'),
        'experimental_prescribed_discharge_m3s': args.prescribed_discharge,
        'solver_validation': json.loads(run.validation_path.read_text()),
        'shipped': measure(shipped['h'], shipped['u'], shipped['v'], shipped['h']+shipped['bed'], scenario.grid), 'snapshots': rows}
    output = args.output / 'hydraulic-spinup-audit.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(output)
    for row in rows:
        hole = row['regions'][1]
        print(row['frame_file'], 'hole median speed', round(hole['speed_p10_p50_p90_mps'][1], 3),
              'supercritical fraction', round(hole['supercritical_wet_fraction'], 3), flush=True)


if __name__ == '__main__':
    main()
