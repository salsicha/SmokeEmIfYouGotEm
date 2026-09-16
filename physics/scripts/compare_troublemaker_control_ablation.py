"""Compare matched open-boundary prior experiments; never claim game acceptance."""
import argparse
import json
from pathlib import Path
import numpy as np
from prepare_troublemaker_control_ablation import ROOT, sha
from audit_troublemaker_hydraulic_spinup import validated_frame_state
from raftsim.scenario2_5d import read_scenario2_5d_package


def centered_wet_slopes(eta, depth, cell):
    if eta.shape != depth.shape or eta.ndim != 2 or min(eta.shape) < 3:
        raise ValueError('Matching two-dimensional fields of at least 3 by 3 required')
    if not np.isfinite(eta).all() or not np.isfinite(depth).all() or not np.isfinite(cell) or cell <= 0:
        raise ValueError('Finite fields and positive spacing required')
    wet = depth > .1
    valid = (wet[1:-1, 1:-1] & wet[:-2, 1:-1] & wet[2:, 1:-1]
             & wet[1:-1, :-2] & wet[1:-1, 2:])
    dx = (eta[1:-1, 2:]-eta[1:-1, :-2])/(2*cell)
    dy = (eta[2:, 1:-1]-eta[:-2, 1:-1])/(2*cell)
    return np.degrees(np.arctan(np.hypot(dx, dy))), valid


def load(work):
    work = work.resolve()
    registration_path = work/'registration.json'
    run_path = work/'run_result.json'
    reg = json.loads(registration_path.read_text())
    run = json.loads(run_path.read_text())
    if run['returncode'] != 0 or reg['cell_m'] != 1.:
        raise ValueError('Completed one-metre experiment required')
    if reg.get('same_grid_continuation') or reg.get('refinement_warm_start') or reg.get('resume_frame'):
        raise ValueError('This comparison requires fresh initial states, not reset-clock continuations')
    folder = ROOT/run['output_dir']
    manifest_path = ROOT/run['manifest']
    manifest = json.loads(manifest_path.read_text())
    scenario_path = next((work/'scenario').glob('*/scenario.json'))
    scenario = read_scenario2_5d_package(scenario_path.parent)
    command = run['command']
    steps = int(command[command.index('--steps')+1])
    interval = int(command[command.index('--frame-interval')+1])
    expected_frames = len(range(0, steps+1, interval))
    if steps % interval or len(manifest['frames']) != expected_frames:
        raise ValueError('Complete equally spaced frame sequence required')
    paths = [registration_path, run_path, manifest_path, ROOT/run['validation']]
    paths += sorted(p for p in scenario_path.parent.iterdir() if p.is_file())
    return dict(reg=reg, run=run, manifest=manifest, scenario=scenario,
                folder=folder, interval=interval, steps=steps, paths=paths)


def compare(original, candidate):
    a, b = load(original), load(candidate)
    for key in a['reg']:
        if key != 'geometry_sha256' and a['reg'][key] != b['reg'].get(key):
            raise ValueError('Experiment registration differs: '+key)
    if a['reg']['geometry_sha256'] == b['reg']['geometry_sha256']:
        raise ValueError('Distinct source hypotheses required')
    if a['manifest'] != b['manifest'] or a['interval'] != b['interval'] or a['steps'] != b['steps']:
        raise ValueError('Numerics or output sampling differ')
    sa, sb = a['scenario'], b['scenario']
    if sa.grid != sb.grid or sa.boundaries != sb.boundaries or sa.fixed_dt != sb.fixed_dt or sa.roughness != sb.roughness:
        raise ValueError('Physical lattice, forcing, timestep or roughness differ')
    x, y = sa.grid.meshgrid()
    region = (x[1:-1,1:-1] >= 0) & (x[1:-1,1:-1] <= 30) & (abs(y[1:-1,1:-1]) <= 20)
    rows = []
    for index, name in enumerate(a['manifest']['frames']):
        states, slopes, valid = [], [], []
        for value in (a, b):
            path = value['folder']/name
            state = validated_frame_state(value['scenario'], np.genfromtxt(path, delimiter=',', names=True))
            if state.depth.max() > 10 or np.hypot(state.u, state.v).max() > 20:
                raise ValueError('State exceeds unchanged hydraulic gates')
            angle, mask = centered_wet_slopes(state.eta, state.depth, sa.grid.dx)
            states.append(state); slopes.append(angle); valid.append(mask)
            value['paths'].append(path)
        common = region & valid[0] & valid[1]
        if not common.any():
            raise ValueError('No comparable wet crux stencil')
        row = dict(seconds=index*a['interval']*sa.fixed_dt, common_wet_stencils=int(common.sum()))
        for label, state, slope in zip(('original', 'control_removed'), states, slopes):
            section_x = [-125., -50., 0., 25., 75., 125.]
            cols = [int(np.argmin(abs(x[0]-value))) for value in section_x]
            banks = np.r_[state.depth[0], state.depth[-1]]
            row[label] = dict(volume_m3=float(state.depth.sum()*sa.grid.dx*sa.grid.dy),
                maximum_artificial_side_bank_depth_m=float(banks.max()),
                section_discharge_m3s=[float((state.depth[:,c]*state.u[:,c]).sum()*sa.grid.dy) for c in cols],
                crux_centered_slope_max_degrees=float(slope[common].max()),
                crux_centered_slope_at_least_30_degrees_area_m2=float((slope[common]>=30).sum()*sa.grid.dx*sa.grid.dy),
                crux_stage_p10_p50_p90_m=np.quantile(state.eta[1:-1,1:-1][common],[.1,.5,.9]).tolist())
        rows.append(row)
    paths = a['paths']+b['paths']+[Path(__file__)]
    return dict(schema='raftsim.troublemaker.control_ablation_comparison.v1', accepted=False,
        comparison='Same 271 by 161 metre rotated open-boundary rapid, 1 metre cells; NOT full river or landward rock-cap union.',
        initial_state='Fresh captured-stage/conveyance seed on each bed; different initial inventory, no evolved state transfer.',
        metric='Centered two-metre stage gradient on the intersection of five-cell wet stencils; NOT submitted engine triangles.',
        crux_bounds_downstream_left_m=[0.,-20.,30.,20.], section_downstream_m=[-125.,-50.,0.,25.,75.,125.],
        target_discharge_m3s=a['reg']['target_discharge_m3s'], snapshots=rows,
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},
        settled_flow_accepted=False, measured_bathymetry=False, engine_or_visual_or_fps_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    report = compare(args.original, args.candidate)
    with args.report.open('x') as out:
        json.dump(report, out, indent=2, allow_nan=False)
    print(json.dumps(report['snapshots'][-1], indent=2))


if __name__ == '__main__':
    main()
