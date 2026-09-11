"""Export one completed diagnostic frame for a process-local Unreal preview.

Never edits production fields. This is a review package, not hydraulic or
photorealism acceptance. Use -RaftSimTroublemakerReviewFields=<output> in a
non-shipping game process with the median flow selected.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_troublemaker_hydraulic_spinup import bank_connected_throat, interpreted_throat, measure, validated_frame_state
from raftsim.cooked_flow_fields import apply_monotone_surface_shock_limiter
from raftsim.scenario2_5d import read_scenario2_5d_package
from raftsim.south_fork_full_hydraulics import _array_record


def validate_review_scenario(base, candidate):
    """Accept only this reach/datum/grid and the explicit local throat experiment.

    The source CSV is separately checked against the candidate's exact bed.
    Keeping these two checks separate prevents a valid frame for the wrong river
    or datum from becoming a visually plausible but misplaced preview.
    """
    fields = ('nx', 'ny', 'dx', 'dy', 'origin_x', 'origin_y')
    if any(getattr(base.grid, k) != getattr(candidate.grid, k) for k in fields):
        raise ValueError('review scenario grid does not match Troublemaker')
    for key in ('river_id', 'flow_band', 'coordinate_reference_system'):
        if getattr(base.metadata, key) != getattr(candidate.metadata, key):
            raise ValueError('review scenario identity/coordinates do not match Troublemaker median')
    for key in ('source_elevation_datum_m', 'rapid_name', 'station_m'):
        if base.metadata.provenance.get(key) != candidate.metadata.provenance.get(key):
            raise ValueError('review scenario datum or rapid does not match Troublemaker')
    if candidate.boundaries != base.boundaries:
        raise ValueError('review boundary definitions differ from the supported trial')
    width = candidate.metadata.provenance.get('experimental_throat_width_m')
    shoulders = candidate.metadata.provenance.get('experimental_throat_shoulders')
    if shoulders not in (None, 'bank_connected_v1') or (shoulders and width is None):
        raise ValueError('unsupported interpreted throat shoulder identity')
    generator = bank_connected_throat if shoulders == 'bank_connected_v1' else interpreted_throat
    expected_bed = base.bed if width is None else generator(base, float(width)).bed
    if not np.array_equal(expected_bed, candidate.bed):
        raise ValueError('review bed is not the original or the declared interpreted throat')


def validate_solver_manifest(frame: Path, path: Path):
    data = json.loads(path.read_text())
    if frame.resolve() not in {(path.parent / f).resolve() for f in data.get('frames', [])}:
        raise ValueError('source solver manifest does not contain the supplied frame')
    expected = {'solver_mode': 'finite_volume', 'boundary_mode': 'scenario',
                'spatial_order': 2, 'flux_scheme': 'hll',
                'disable_fixture_calibrations': True, 'preserve_initial_mass': False}
    if any(data.get(k) != v for k, v in expected.items()):
        raise ValueError('source solver settings are not the supported diagnostic solve')
    return data


def export_review(frame: Path, output: Path, elapsed_seconds: float,
                  source_scenario: Path | None = None, source_solver_manifest: Path | None = None):
    root = Path(__file__).resolve().parents[2]
    rapid = root / 'physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/rapids/troublemaker'
    output = output.resolve()
    # Preview artifacts have no reason to overwrite an existing package or
    # escape the repository's diagnostic area.
    if not output.is_relative_to(root / 'tmp') or output.exists():
        raise ValueError('review output must be a new directory beneath repository tmp')
    if not np.isfinite(elapsed_seconds) or elapsed_seconds <= 0:
        raise ValueError('elapsed simulation time must be positive')
    base = read_scenario2_5d_package(rapid / 'scenario/median_runnable')
    source_scenario = source_scenario or rapid / 'scenario/median_runnable'
    scenario = read_scenario2_5d_package(source_scenario)
    validate_review_scenario(base, scenario)
    if not np.array_equal(scenario.bed, base.bed) and source_solver_manifest is None:
        raise ValueError('changed-bed review requires its source solver manifest')
    offline_solver = validate_solver_manifest(frame, source_solver_manifest) if source_solver_manifest else None
    state = validated_frame_state(scenario, np.genfromtxt(frame, delimiter=',', names=True))
    arrays, limiter = apply_monotone_surface_shock_limiter({
        'h': state.depth.astype(np.float32), 'u': state.u.astype(np.float32),
        'v': state.v.astype(np.float32), 'bed': scenario.bed.astype(np.float32),
        'wet_mask': state.wet.astype(np.uint8)})
    manifest = json.loads((rapid / 'cooked/manifest.json').read_text())
    band = copy.deepcopy(next(b for b in manifest['bands'] if b['band_id'] == 'median_runnable'))
    band['scenario_package'] = str(source_scenario.resolve())
    band['runtime_boundaries'] = [b.to_json_dict() for b in scenario.boundaries]
    for stale in ['validation', 'solver_return_code', 'solver_runtime_seconds']:
        band.pop(stale, None)
    directory = output / 'median_runnable'
    directory.mkdir(parents=True)
    band['arrays'] = {}
    for name, array in arrays.items():
        path = directory / (name + '.npy')
        np.save(path, np.ascontiguousarray(array))
        band['arrays'][name] = _array_record(output, path, name, array)
    band['surface_shock_limiter'] = limiter
    band['validation'] = {'passed': False, 'reason': 'diagnostic preview; not accepted'}
    manifest['bands'] = [band]
    manifest['all_bands_passed'] = False
    manifest['generated_on'] = '2026-09-05'
    # Do not retain the short production cook's steps/binary hash as if they
    # described this diagnostic snapshot.
    manifest['solver'].pop('binary_sha256', None)
    manifest['solver'].pop('steps', None)
    manifest['solver'].update({
        'source': 'completed diagnostic CSV snapshot', 'simulated_seconds': elapsed_seconds})
    manifest['review'] = {'production_promoted': False, 'photorealism_accepted': False,
        'frame': str(frame.resolve()), 'frame_sha256': hashlib.sha256(frame.read_bytes()).hexdigest(),
        'scope': 'Troublemaker median only; validated original or interpreted throat bed',
        'experimental_throat_width_m': scenario.metadata.provenance.get('experimental_throat_width_m'),
        'scenario_provenance': scenario.metadata.provenance,
        'source_solver_manifest': str(source_solver_manifest.resolve()) if source_solver_manifest else None,
        'source_solver_manifest_sha256': hashlib.sha256(source_solver_manifest.read_bytes()).hexdigest() if source_solver_manifest else None,
        'offline_solver_config': {k: v for k, v in offline_solver.items() if k not in
            ('frames', 'probes', 'cross_sections', 'diagnostics')} if offline_solver else None,
        'runtime_replays_offline_boundary': False,
        'runtime_evolution': 'first-order cropped live solver; transmissive crop edges; authored boundaries at full-grid edges; offline prescribed-Q option is not enabled',
        'post_limiter_metrics': measure(arrays['h'], arrays['u'], arrays['v'],
            arrays['h']+arrays['bed'], scenario.grid)}
    path = output / 'manifest.json'
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frame', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--elapsed-seconds', required=True, type=float)
    parser.add_argument('--source-scenario', type=Path,
        help='Exact source scenario for an interpreted-throat frame; same grid/datum/rapid required.')
    parser.add_argument('--source-solver-manifest', type=Path,
        help='Completed solver manifest containing this frame; required for changed-bed previews.')
    args = parser.parse_args()
    print(export_review(args.frame, args.output, args.elapsed_seconds,
                       args.source_scenario, args.source_solver_manifest))
