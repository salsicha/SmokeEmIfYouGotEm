"""Audit paired live detail foam density/resolve; not a visual acceptance test."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_detail_wave_regime import read_snapshot


def smoothstep(low, high, values):
    t = np.clip((values - low) / (high - low), 0., 1.)
    return t * t * (3. - 2. * t)


def distribution(values):
    values = np.asarray(values, dtype=np.float64)
    if not values.size:
        return dict(count=0)
    return dict(count=int(values.size), minimum=float(values.min()),
                median=float(np.median(values)), p95=float(np.quantile(values, .95)),
                maximum=float(values.max()), mean=float(values.mean()))


def analyze(flow, state, surface, cell_m):
    if flow.ndim != 3 or flow.shape[-1] != 4 or flow.shape != state.shape or flow.shape != surface.shape:
        raise ValueError('Matching Y/X/float4 arrays required')
    if not np.isfinite(cell_m) or cell_m <= 0 or not all(np.isfinite(a).all() for a in (flow, state, surface)):
        raise ValueError('Nonfinite arrays or invalid cell size')
    if (flow[..., 0] < 0).any() or (state[..., 3] < 0).any():
        raise ValueError('Negative depth or transported foam density')
    if ((flow[..., 3] < 0) | (flow[..., 3] > 1)).any():
        raise ValueError('Entrainment potential outside [0,1]')
    h, w = flow.shape[:2]
    y, x = np.indices((h, w))
    edge_m = np.minimum.reduce((x, y, w - 1 - x, h - 1 - y)) * cell_m
    weight = smoothstep(0., 4., edge_m) * smoothstep(.02, .4, flow[..., 0].astype(float))
    density = state[..., 3].astype(float)
    expected = -np.expm1(-density) * weight
    coverage = surface[..., 3].astype(float)
    error = abs(coverage - expected)
    # Independent double equation vs float GPU arithmetic; numerical contract,
    # not a tunable photographic threshold or foam-production calibration.
    paired = bool(error.max() <= 1.e-6)
    groups = {}
    for name, mask in dict(wet=flow[..., 0] > .01,
                           full_weight=weight >= .999999,
                           tapered=(weight > 0) & (weight < .999999)).items():
        source = flow[..., 3][mask]
        foam = coverage[mask]
        groups[name] = dict(source_potential=distribution(source),
            transported_density=distribution(density[mask]), resolved_coverage=distribution(foam),
            detail_height_m=distribution(abs(state[..., 0][mask])),
            fraction_coverage_above_080=float(np.mean(foam > .8)) if foam.size else None,
            fraction_source_above_050=float(np.mean(source > .5)) if foam.size else None,
            dense_foam_with_current_source_below_005=int(np.count_nonzero((foam > .8) & (source < .05))))
    return dict(resolve_equation_passed=paired, maximum_resolve_error=float(error.max()),
        nonzero_coverage_on_zero_weight=int(np.count_nonzero(coverage[weight == 0])), groups=groups,
        density_sum_cell_area=float(density.sum() * cell_m**2),
        limitations='Density integral is not measured bubble mass. Current source cannot attribute accumulated/advection history. Resolved GPU coverage is not final lit pixel coverage. No realism or performance acceptance.')


def audit(path):
    metadata, arrays, hashes = read_snapshot(path)
    surface_path = path.with_suffix('.surface.f32')
    if surface_path.stat().st_size != arrays['flow'].size * 4:
        raise ValueError('Truncated or oversized surface array')
    surface = np.fromfile(surface_path, dtype='<f4').reshape(arrays['flow'].shape)
    hashes[str(surface_path)] = hashlib.sha256(surface_path.read_bytes()).hexdigest()
    return dict(snapshot=str(path.resolve()), metadata=metadata, sha256=hashes,
                analysis=analyze(arrays['flow'], arrays['state'], surface, metadata['cell_m']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshots', nargs='+', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    results = [audit(p) for p in args.snapshots]
    report = dict(schema='raftsim.detail.foam_snapshot_audit.v1',
                  resolve_equation_passed=all(r['analysis']['resolve_equation_passed'] for r in results),
                  physical_accepted=False, visual_accepted=False, performance_accepted=False, snapshots=results)
    with args.report.open('x', encoding='utf-8') as out:
        json.dump(report, out, indent=2, allow_nan=False)
        out.write('\n')
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report['resolve_equation_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
