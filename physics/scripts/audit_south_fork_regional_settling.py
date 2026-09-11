"""Locate temporal storage/stage changes in saved South Fork survey frames.

This is postprocessing, not a new solve or a convergence gate. Volume partitions
cover the full Cartesian domain; stage uses cells wet in every saved frame of
the selected tail. Cell-centred section transport is not numerical face flux.
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
from audit_troublemaker_hydraulic_spinup import validated_frame_state
from south_fork_survey_sanity import check_frame


def partition_masks(grid):
    x, _ = grid.meshgrid()
    lo = grid.origin_x - grid.dx / 2
    hi = lo + grid.nx * grid.dx
    # These are cell edges on both the 1 m and 0.5 m registered lattices.
    edges = [lo, -80.5, -25.5, 25.5, 80.5, hi]
    if any(b <= a for a, b in zip(edges, edges[1:])):
        raise ValueError('Expected the registered South Fork survey domain')
    masks = [(x >= a) & (x < b) for a, b in zip(edges, edges[1:])]
    if not np.all(np.sum(masks, axis=0) == 1):
        raise ValueError('Regional masks do not partition the complete domain')
    return edges, masks


def interval_rates(times, values):
    t = np.asarray(times, dtype=float)
    v = np.asarray(values, dtype=float)
    if (t.ndim != 1 or len(t) < 2 or len(v) != len(t) or
            not np.isfinite(t).all() or not np.isfinite(v).all() or np.any(np.diff(t) <= 0)):
        raise ValueError('Finite values and strictly increasing sample times required')
    return np.diff(v, axis=0) / np.diff(t).reshape((-1,) + (1,) * (v.ndim - 1))


def largest_masked_cells(scores, mask, count=5):
    if scores.shape != mask.shape or count < 1 or not np.isfinite(scores[mask]).all():
        raise ValueError('Finite scores on a matching mask required')
    indices = np.flatnonzero(mask)
    selected = indices[np.argsort(-scores.ravel()[indices], kind='stable')[:count]]
    return [tuple(map(int, np.unravel_index(i, scores.shape))) for i in selected]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Retain previous reports; choose a new output')
    work = args.run.resolve()
    registration = json.loads((work / 'registration.json').read_text())
    run = json.loads((work / 'run_result.json').read_text())
    scenario = read_scenario2_5d_package(next((work / 'scenario').glob('*/scenario.json')))
    folder = ROOT / run['output_dir']
    manifest = json.loads((folder / 'manifest.json').read_text())
    steps = int(run['command'][run['command'].index('--steps') + 1])
    interval = int(run['command'][run['command'].index('--frame-interval') + 1])
    sample_steps = [0, *range(interval, steps + 1, interval)]
    if sample_steps[-1] != steps:
        sample_steps.append(steps)
    if len(manifest['frames']) != len(sample_steps) or len(sample_steps) < 4:
        raise ValueError('Saved frame count/timing mismatch or insufficient history')
    times = np.array(sample_steps) * scenario.fixed_dt
    edges, masks = partition_masks(scenario.grid)
    area = scenario.grid.dx * scenario.grid.dy
    histories = [[] for _ in masks]
    wet_areas = [[] for _ in masks]
    tail = []
    hashes = []
    for i, name in enumerate(manifest['frames']):
        frame = (folder / name).resolve()
        if not frame.is_relative_to(folder.resolve()):
            raise ValueError('Frame outside run output')
        raw = np.genfromtxt(frame, delimiter=',', names=True)
        if not check_frame(raw)['passed']:
            raise ValueError(f'Failed hydraulic frame: {frame}')
        state = validated_frame_state(scenario, raw)
        for j, mask in enumerate(masks):
            histories[j].append(float(state.depth[mask].sum() * area))
            wet_areas[j].append(float(np.sum(state.depth[mask] > .1) * area))
        if i >= len(sample_steps) - 4:
            tail.append(state)
        hashes.append({'frame': name, 'sha256': hashlib.sha256(frame.read_bytes()).hexdigest()})
    common_wet = np.logical_and.reduce([s.depth > .1 for s in tail])
    stage_range = np.ptp(np.array([s.eta for s in tail]), axis=0)
    regions = []
    x, y = scenario.grid.meshgrid()
    for j, mask in enumerate(masks):
        sample = mask & common_wet
        if not sample.any():
            raise ValueError('No persistent wet stage samples in region')
        stages = np.array([s.eta[sample] for s in tail])
        peaks = []
        for row, col in largest_masked_cells(stage_range, sample):
            east_north = (np.asarray(registration['origin_utm_m']) +
                x[row,col] * np.asarray(registration['downstream_unit']) +
                y[row,col] * np.asarray(registration['left_unit']))
            peaks.append({'row_col': [row,col], 'downstream_left_m': [float(x[row,col]),float(y[row,col])],
                'east_north_utm_m': east_north.tolist(),
                'stage_range_m': float(stage_range[row,col]),
                'tail_depths_m': [float(s.depth[row,col]) for s in tail],
                'tail_speeds_mps': [float(np.hypot(s.u[row,col],s.v[row,col])) for s in tail],
                'tail_stages_navd88_m': [float(s.eta[row,col]+registration['vertical_origin_navd88_m']) for s in tail],
                'bed_3x3_navd88_m': (scenario.bed[max(0,row-1):row+2,max(0,col-1):col+2] +
                                     registration['vertical_origin_navd88_m']).tolist()})
        regions.append({'bounds_downstream_m': edges[j:j + 2],
            'volume_m3': histories[j], 'wet_area_above_10cm_m2': wet_areas[j],
            'interval_storage_rate_m3s': interval_rates(times, histories[j]).tolist(),
            'common_tail_wet_area_m2': float(sample.sum() * area),
            'tail_stage_median_navd88_m': (np.median(stages, axis=1) + registration['vertical_origin_navd88_m']).tolist(),
            'tail_per_cell_stage_range_p50_p95_max_m': np.percentile(np.ptp(stages, axis=0), [50, 95, 100]).tolist(),
            'largest_sampled_stage_variation_locations': peaks})
    report = {'scope': __doc__.strip(), 'source_run': work.relative_to(ROOT).as_posix(),
        'geometry_sha256': registration['geometry_sha256'], 'saved_frame_hashes': hashes,
        'source_bed_sampling': registration.get('bed_sampling','bilinear'),
        'sample_times_seconds': times.tolist(), 'tail_times_seconds': times[-4:].tolist(),
        'regions': regions, 'total_volume_m3': np.sum(histories, axis=0).tolist(),
        'total_interval_storage_rate_m3s': interval_rates(times, np.sum(histories, axis=0)).tolist(),
        'resolution_converged': False, 'production_promoted': False}
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps([{'region': r['bounds_downstream_m'],
        'tail_storage_rates_m3s': r['interval_storage_rate_m3s'][-3:],
        'tail_stage_ranges_p50_p95_max_m': r['tail_per_cell_stage_range_p50_p95_max_m']}
        for r in regions], indent=2))


if __name__ == '__main__': main()
