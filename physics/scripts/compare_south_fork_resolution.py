"""Compare nested survey grids without calling a two-grid difference convergence.

Restrict fine depth/momentum by cell area, not by centre interpolation. Compare
stage only where the coarse cell and every fine child are wet. Wet-edge changes
are reported separately. Both runs must use identical source geometry/forcing.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
sys.path.insert(0, str(ROOT / 'physics/src'))
import numpy as np
from raftsim.scenario2_5d import read_scenario2_5d_package
from south_fork_survey_sanity import check_frame
from audit_troublemaker_hydraulic_spinup import validated_frame_state


def restrict(field, ratio):
    field = np.asarray(field)
    if field.ndim != 2 or ratio < 2 or int(ratio) != ratio or any(n % ratio for n in field.shape):
        raise ValueError('Expected an integer nested two-dimensional refinement')
    if not np.isfinite(field).all():
        raise ValueError('Nonfinite fine-grid field')
    ratio = int(ratio)
    ny, nx = field.shape
    return field.reshape(ny // ratio, ratio, nx // ratio, ratio).mean(axis=(1, 3))


def comparable(coarse, fine, c_registration, f_registration):
    if c_registration.get('bed_sampling','bilinear')!=f_registration.get('bed_sampling','bilinear'):
        raise ValueError('Resolution comparison changed terrain interpolation')
    for key in ('geometry_sha256', 'solver_binary_sha256', 'boundary_mode', 'cfl',
                'target_discharge_m3s', 'origin_utm_m', 'downstream_unit', 'left_unit',
                'vertical_origin_navd88_m', 'inlet_stage_navd88_m', 'outlet_stage_navd88_m'):
        if c_registration[key] != f_registration[key]:
            raise ValueError(f'Resolution comparison changed {key}')
    if (coarse.fixed_dt != fine.fixed_dt or coarse.roughness != fine.roughness or
            coarse.boundaries != fine.boundaries):
        raise ValueError('Resolution comparison changed numerical settings or boundaries')
    a, b = coarse.grid, fine.grid
    ratio = round(a.dx / b.dx)
    if ratio < 2 or a.dx != b.dx * ratio or a.dy != b.dy * ratio:
        raise ValueError('Grids are not integer nested refinements')
    for origin, spacing, count in (('origin_x', 'dx', 'nx'), ('origin_y', 'dy', 'ny')):
        if (getattr(a, count) * ratio != getattr(b, count) or
                abs(getattr(a, origin) - getattr(a, spacing) / 2 -
                    getattr(b, origin) + getattr(b, spacing) / 2) > 1e-9):
            raise ValueError('Physical cell-edge bounds changed')
    return ratio


def differences(values):
    values = np.asarray(values)
    if not values.size or not np.isfinite(values).all():
        raise ValueError('No finite, comparable wet samples')
    return {'signed_median': float(np.median(values)),
            'absolute_p95': float(np.percentile(abs(values), 95)),
            'absolute_maximum': float(np.max(abs(values)))}


def temporal_envelope_gap(coarse_stages, fine_stages, mask):
    """A separation of sampled ranges, not a confidence interval or error bar."""
    c, f = np.asarray(coarse_stages), np.asarray(fine_stages)
    if (c.ndim != 3 or f.ndim != 3 or c.shape[1:] != mask.shape or f.shape[1:] != mask.shape or
            len(c) < 2 or len(f) < 2 or not mask.any() or
            not np.isfinite(c[:, mask]).all() or not np.isfinite(f[:, mask]).all()):
        raise ValueError('Finite temporal samples on a nonempty matching wet mask required')
    below = np.min(c[:, mask], axis=0) - np.max(f[:, mask], axis=0)
    above = np.min(f[:, mask], axis=0) - np.max(c[:, mask], axis=0)
    gap = np.maximum(0., np.maximum(below, above))
    return {'sampled_cells': int(mask.sum()),
        'fraction_fine_entirely_lower_by_more_than_1cm': float(np.mean(below > .01)),
        'fraction_fine_entirely_higher_by_more_than_1cm': float(np.mean(above > .01)),
        'gap_p50_p95_max_m': np.percentile(gap, [50, 95, 100]).tolist()}


def inspect(work):
    registration = json.loads((work / 'registration.json').read_text())
    scenario = read_scenario2_5d_package(next((work / 'scenario').glob('*/scenario.json')))
    run = json.loads((work / 'run_result.json').read_text())
    folder = ROOT / run['output_dir']
    manifest = json.loads((folder / 'manifest.json').read_text())
    if not manifest['frames']:
        raise ValueError('No saved frames')
    reports = []
    steps = int(run['command'][run['command'].index('--steps') + 1])
    interval = int(run['command'][run['command'].index('--frame-interval') + 1])
    saved_steps = [0, *range(interval, steps + 1, interval)]
    if saved_steps[-1] != steps: saved_steps.append(steps)
    if len(saved_steps) != len(manifest['frames']): raise ValueError('Frame timing mismatch')
    tail = []
    for index, name in enumerate(manifest['frames']):
        path = (folder / name).resolve()
        if not path.is_relative_to(folder.resolve()):
            raise ValueError('Frame outside solver output')
        data = np.genfromtxt(path, delimiter=',', names=True)
        reports.append({'frame': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        **check_frame(data)})
        state = validated_frame_state(scenario, data)
        if index >= len(manifest['frames']) - 4:
            tail.append({'h': state.depth, 'eta': state.eta})
        print(f"Screened {work.name}: {name}: {reports[-1]['passed']}", flush=True)
    fields = {'h': state.depth, 'hu': state.hu, 'hv': state.hv, 'eta': state.eta}
    return scenario, registration, fields, {'work': work.relative_to(ROOT).as_posix(),
        'runtime_seconds': run['runtime_seconds'], 'saved_frames': reports,
        'tail_times_seconds': [step * scenario.fixed_dt for step in saved_steps[-4:]],
        'all_saved_frames_sane': all(r['passed'] for r in reports),
        'native_validation': json.loads((folder / 'validation.json').read_text())}, tail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coarse', type=Path, required=True)
    parser.add_argument('--fine', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Choose a new report path; retain earlier comparisons')
    c, cr, cd, ca, ct = inspect(args.coarse.resolve())
    f, fr, fd, fa, ft = inspect(args.fine.resolve())
    ratio = comparable(c, f, cr, fr)
    report = {'scope': __doc__.strip(), 'coarse': ca, 'fine': fa,
        'source_bed_sampling': cr.get('bed_sampling','bilinear'),
        'geometry_sha256': cr['geometry_sha256'], 'identical_forcing_verified': True,
        'refinement_initialization': fr['refinement_warm_start'],
        'same_grid_continuation': fr.get('same_grid_continuation'),
        'resolution_converged': False, 'measured_bathymetry': False,
        'visual_acceptance': False, 'production_promoted': False}
    if ca['all_saved_frames_sane'] and fa['all_saved_frames_sane']:
        coarse = {k: cd[k].reshape(c.grid.ny, c.grid.nx) for k in ('h', 'hu', 'hv', 'eta')}
        fine = {k: fd[k].reshape(f.grid.ny, f.grid.nx) for k in ('h', 'hu', 'hv', 'eta')}
        restricted = {k: restrict(v, ratio) for k, v in fine.items()}
        full_wet = (coarse['h'] > .1) & (restrict((fine['h'] > .1).astype(float), ratio) == 1)
        x, y = c.grid.meshgrid()
        regions = {'all_common_wet': full_wet,
                   'crux_common_wet': full_wet & (abs(x) < 25) & (abs(y) < 30)}
        metrics = {}
        for name, mask in regions.items():
            dc = coarse['h'][mask]
            df = restricted['h'][mask]
            velocity_difference = np.hypot(
                restricted['hu'][mask] / df - coarse['hu'][mask] / dc,
                restricted['hv'][mask] / df - coarse['hv'][mask] / dc)
            metrics[name] = {'area_m2': float(mask.sum() * c.grid.dx * c.grid.dy),
                'stage_difference_m': differences(restricted['eta'][mask] - coarse['eta'][mask]),
                'depth_difference_m': differences(df - dc),
                'velocity_vector_difference_mps': differences(velocity_difference)}
        area = c.grid.dx * c.grid.dy
        report['final_state_differences_not_convergence'] = metrics
        report['storage_difference_m3'] = float((restricted['h'] - coarse['h']).sum() * area)
        report['wet_area_difference_m2'] = float(((fine['h'] > .1).sum() / ratio**2 -
                                                  (coarse['h'] > .1).sum()) * area)
        tail_wet = (np.logical_and.reduce([t['h'] > .1 for t in ct]) &
            np.logical_and.reduce([restrict((t['h'] > .1).astype(float), ratio) == 1 for t in ft]))
        report['sampled_tail_stage_envelope_separation'] = {
            name: temporal_envelope_gap([t['eta'] for t in ct],
                [restrict(t['eta'], ratio) for t in ft], mask & tail_wet)
            for name, mask in regions.items()}
        report['note'] = ('Single final snapshots after different settling histories; inspect temporal '
                          'settling and numerical flux audits separately. Tail envelopes cover different '
                          'sampled durations and cannot bound unsampled extrema. No convergence threshold asserted.')
    else:
        report['note'] = 'At least one saved frame failed sanity; no final-state comparison accepted.'
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in report.items() if k not in ('coarse', 'fine')}, indent=2))
    if not ca['all_saved_frames_sane'] or not fa['all_saved_frames_sane']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
