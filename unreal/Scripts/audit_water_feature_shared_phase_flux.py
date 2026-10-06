"""Saved native velocities evaluated on common all-stencil liquid area bounds.

Not a new pressure solve, full incompressibility residual or physical budget.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from water_feature_phase_flux import cartesian_flux_bounds


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('phase', 'pressure', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    phase, pressure = (json.loads(p.read_text()) for p in (args.phase, args.pressure)); hashes = {}
    for report, path in ((phase, args.phase), (pressure, args.pressure)):
        for p, sha in {**report['dependency_sha256'], **report['outputs_sha256']}.items():
            if p in hashes and sha != hashes[p]:
                raise ValueError('Conflicting evidence versions')
            hashes[p] = sha
        hashes[str(path.resolve())] = digest(path)
    for p in (Path(__file__), Path(__file__).with_name('water_feature_phase_flux.py')):
        hashes[str(p.resolve())] = digest(p)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned checkpoint/phase fields changed')
    area_lo = [np.load(phase['arrays'][f'face-liquid-lower-axis-{a}-depth-2'], allow_pickle=False) for a in range(3)]
    area_hi = [np.load(phase['arrays'][f'face-liquid-upper-axis-{a}-depth-2'], allow_pickle=False) for a in range(3)]
    cell_lo = np.load(phase['arrays']['cell-liquid-lower-depth-2'], allow_pickle=False)
    cell_hi = np.load(phase['arrays']['cell-liquid-upper-depth-2'], allow_pickle=False)
    flags = np.load(pressure['native']['arrays']['flags'], allow_pickle=False)
    masks = dict(definitely_wet=cell_lo > 0, previously_empty_definitely_wet=((flags & 4) != 0) & (cell_lo > 0),
                 original_fluid=(flags & 1) != 0, unresolved_wet_support=(cell_lo == 0) & (cell_hi > 0))
    stages = []; allowance = 1e-8  # Fixed diagnostic float32 flux allowance, m3/s; not acceptance.
    for label, path in (('before_pressure', pressure['native']['arrays']['velocity-before']),
                        ('native_public_projected', pressure['native']['arrays']['velocity-projected']),
                        ('old_consistent_projected', pressure['arrays']['velocity-consistent-native'])):
        v = np.load(path, allow_pickle=False).astype(float)*phase['cell_m']*2.5
        lower, upper, boundary = cartesian_flux_bounds(v, area_lo, area_hi); rows = {}
        distance = np.where(lower > 0, lower, np.where(upper < 0, -upper, 0.))
        for name, mask in masks.items():
            count = int(mask.sum()); values = distance[mask]
            index = np.unravel_index(np.argmax(np.where(mask, distance, -1)), mask.shape) if count else None
            rows[name] = dict(cells=count, zero_excluded_beyond_allowance=int(np.count_nonzero(values > allowance)),
                maximum_zero_distance_m3_per_second=float(values.max()) if count else 0.,
                worst_index=[int(x) for x in index] if index is not None else None,
                worst_flux_interval_m3_per_second=[float(lower[index]), float(upper[index])] if index is not None else None)
        stages.append(dict(label=label, cohorts=rows, full_domain_cartesian_boundary_flux_interval_m3_per_second=boundary))
    result = dict(complete=True, accepted=False, originals_unchanged=True, stages=stages,
        fixed_diagnostic_flux_allowance_m3_per_second=allowance, source_flux_fitted=False,
        arrays_modified=False, dependency_sha256=hashes,
        scope='Cartesian liquid area-weighted flux intervals for unchanged saved velocities and common cohorts. Missing internal free-surface flux/emission/removal: NOT full incompressibility or conserved mass. No solver step or animation.')
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Flux interval audit changed preserved data')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print('SHARED_PHASE_FLUX', stages, flush=True)


if __name__ == '__main__':
    main()
