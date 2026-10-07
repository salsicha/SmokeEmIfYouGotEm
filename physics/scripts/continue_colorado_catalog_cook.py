"""Continue an autonomous construction cook from its unmodified saved fields.

Unlike bed-edit warm starts, this must not recompute depth, clip velocity, change
wetness or rescale momentum. Native elapsed time restarts at zero; only constant
boundaries with all authored forcing/fixture calibration disabled are eligible.
"""
import argparse
import copy
import json
import shutil
from pathlib import Path

import numpy as np

from build_colorado_catalog_evidence import ROOT, sha
from review_colorado_catalog_cook import load_frame
from build_colorado_catalog_scenario import checked_roughness


def roughness_sensitivity(scenario, value):
    """Change only the declared resistance hypothesis, never saved fields."""
    result = copy.deepcopy(scenario)
    if value is None:
        return result, None
    value = checked_roughness(value)
    original = checked_roughness(scenario['roughness'])
    result['roughness'] = value
    return result, dict(parameter='roughness', original=original, candidate=value,
        scope='Uniform inferred resistance sensitivity, not measured resistance; bed, boundaries and saved state unchanged.')


def restart_state(frame, bed, grid):
    shape = (grid['ny'], grid['nx'])
    if bed.shape != shape or any(frame[k].shape != shape for k in ('h', 'eta', 'u', 'v', 'hu', 'hv', 'wet')):
        raise ValueError('Continuation grid shape differs')
    for k in ('h', 'eta', 'u', 'v', 'hu', 'hv', 'wet'):
        if not np.isfinite(frame[k]).all():
            raise ValueError('Nonfinite continuation state')
    if (frame['h'] < 0).any() or not np.isin(frame['wet'], [0, 1]).all():
        raise ValueError('Invalid continuation depth or wet mask')
    if not np.allclose(frame['eta']-frame['h'], bed, atol=1e-8, rtol=0):
        raise ValueError('Continuation bed changed; no surface remapping allowed')
    return {k: np.ascontiguousarray(frame[name], dtype=bool if k == 'wet' else '<f8')
            for k, name in [('depth', 'h'), ('eta', 'eta'), ('u', 'u'), ('v', 'v'),
                            ('hu', 'hu'), ('hv', 'hv'), ('wet', 'wet')]}


def prepare(inputs, cook, out, roughness=None):
    if out.exists():
        raise ValueError('Fresh continuation directory required')
    report = json.loads((inputs/'build_report.json').read_text())
    for name, digest in report['files_sha256'].items():
        if sha(inputs/name) != digest:
            raise ValueError('Changed original input')
    native = json.loads((cook/'manifest.json').read_text())
    validation = json.loads((cook/'validation.json').read_text())
    if (native['solver_mode'] != 'finite_volume' or native['boundary_mode'] != 'scenario' or
            native['feature_strength_scale'] != 0 or not native['disable_fixture_calibrations'] or
            not validation['passed'] or not validation['finite_state'] or validation['velocity_limit_reached']):
        raise ValueError('Only finite unforced native cooks can continue')
    scenario = json.loads((inputs/'scenario/scenario.json').read_text())
    allowed = {'edge', 'kind', 'ghost_cells', 'metadata', 'stage'}
    if (scenario.get('cascading') or any(set(b)-allowed or b['kind'] not in
            ('discharge_profile', 'outflow', 'bank', 'wall') for b in scenario['boundaries'])):
        raise ValueError('Continuation requires explicitly constant boundaries')
    frame_name = Path(native['frames'][-1])
    if frame_name.parent != Path('frames') or frame_name.suffix != '.csv':
        raise ValueError('Invalid final frame path')
    grid = scenario['grid']; bed = np.load(inputs/'scenario/bed.npy')
    frame = load_frame(cook/frame_name, bed.shape)
    if (not np.array_equal(frame['x'], np.broadcast_to(grid['origin_x']+np.arange(grid['nx'])*grid['dx'], bed.shape)) or
            not np.array_equal(frame['y'], np.broadcast_to((grid['origin_y']+np.arange(grid['ny'])*grid['dy'])[:, None], bed.shape))):
        raise ValueError('Continuation geographic coordinates differ')
    state = restart_state(frame, bed, grid)
    scenario, sensitivity = roughness_sensitivity(scenario, roughness)
    out.mkdir(parents=True)
    for name in report['files_sha256']:
        target = out/name; target.parent.mkdir(parents=True, exist_ok=True)
        if name.replace('\\', '/') != 'scenario/initial_state.npz':
            shutil.copyfile(inputs/name, target)
    np.savez_compressed(out/'scenario/initial_state.npz', **state)
    if sensitivity is not None:
        (out/'scenario/scenario.json').write_text(json.dumps(scenario, indent=2)+'\n')
    result = copy.deepcopy(report)
    result['native_continuation'] = dict(source_inputs=inputs.relative_to(ROOT).as_posix(),
        source_input_report_sha256=sha(inputs/'build_report.json'),
        native_manifest_sha256=sha(cook/'manifest.json'), validation_sha256=sha(cook/'validation.json'),
        frame=(cook/frame_name).relative_to(ROOT).as_posix(), frame_sha256=sha(cook/frame_name),
        policy='Exact saved state; same bed and constant boundaries; no forcing; native clock restarts at zero.')
    if sensitivity is not None:
        result['native_continuation']['parameter_sensitivity'] = sensitivity
        result['roughness_hypothesis'] = sensitivity['candidate']
    result['files_sha256'] = {p.relative_to(out).as_posix(): sha(p) for p in out.rglob('*') if p.is_file()}
    (out/'build_report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result['native_continuation']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('inputs', 'cook', 'out'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--roughness', type=float, help='Optional bounded resistance-only sensitivity; saved state is unchanged.')
    args = parser.parse_args()
    print(json.dumps(prepare(args.inputs.resolve(), args.cook.resolve(), args.out.resolve(), args.roughness), indent=2))
