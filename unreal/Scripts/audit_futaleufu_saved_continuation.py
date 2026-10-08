"""Audit a completed native continuation without changing its pinned ancestors.

The earlier 30-second audit remains immutable because the native restart pins
it. This reader validates the actual command's snapshot schedule, then applies
the same numerical, route-connectivity and exterior-bank checks to every frame.
Passing is not settled-hydraulics or playable-map acceptance.
"""
import argparse
import json
from pathlib import Path

import numpy as np

import audit_futaleufu_native_continuation as prior
from build_futaleufu_continuous_water_domain import (
    ROOT, PREFIX, sha, FutaleufuBed, connected_tiles, observe_branches)


def schedule(request, manifest):
    steps = request.get('steps')
    command = request.get('command', [])
    if type(steps) is not int or len(command) != 6:
        raise ValueError('Complete native command and integer step count required')
    try:
        command_steps, interval, workers = map(int, command[3:])
    except (TypeError, ValueError) as exc:
        raise ValueError('Invalid native command schedule') from exc
    if ((steps, interval) not in ((3000, 300), (30000, 3000)) or
            command_steps != steps or workers != 4 or
            request.get('snapshot_interval_steps', interval) != interval or
            request.get('dt_seconds') != .01 or manifest.get('dt_seconds') != .01):
        raise ValueError('Only the reviewed native continuation schedules are supported')
    initial = manifest.get('initial_time_seconds')
    if not isinstance(initial, (int, float)) or not np.isfinite(initial) or initial < 0:
        raise ValueError('Finite nonnegative native restart clock required')
    if request.get('source_time_seconds') != initial:
        raise ValueError('Request and native restart clocks disagree')
    target = initial + steps*.01
    if request.get('target_time_seconds', target) != target:
        raise ValueError('Request terminal clock disagrees with native steps')
    return list(range(0, steps+1, interval))


def require_complete_snapshots(native, expected):
    actual = sorted(int(p.name[6:]) for p in native.glob('frame_*')
                    if p.is_dir() and p.name[6:].isdigit())
    if actual != expected or any(not (native/('frame_%06d'%s)/'complete.json').is_file() for s in expected):
        raise ValueError('Every requested native snapshot must be present and complete')


def audit(run, output):
    run, output = Path(run).resolve(), Path(output).resolve()
    run.relative_to(ROOT)
    output.relative_to(ROOT/'tmp')
    if output.exists():
        raise ValueError('Fresh audit output required; preserve prior evidence')
    if (run/'failure.json').exists() or not (run/'completed.json').is_file():
        raise ValueError('Successful terminal wrapper receipt required')
    completion = json.loads((run/'completed.json').read_text())
    if completion.get('exit_code') != 0 or not completion.get('native_restart_fields_and_clock_exact'):
        raise ValueError('Native wrapper did not validate exact continuation')
    native = run/'native'
    source = Path((native/'input_manifest_path.txt').read_text().strip()).resolve()
    source.relative_to(ROOT)
    if sha(source) != sha(native/'input_manifest.json'):
        raise ValueError('Actual native input manifest changed')
    manifest = json.loads(source.read_text())
    request = json.loads((run/'request.json').read_text())
    expected = schedule(request, manifest)
    if manifest['schema'] != 'raftsim.cartesian_flow_cook.v1' or manifest['grid']['cell_m'] != 1.:
        raise ValueError('Reviewed native one-metre domain required')
    if (Path(request['command'][1]).resolve() != source or
            Path(request['command'][2]).resolve() != native):
        raise ValueError('Request belongs to another native input/output')
    require_complete_snapshots(native, expected)
    pins = {}
    for name, digest in manifest['sources_sha256'].items():
        path = (ROOT/name).resolve()
        path.relative_to(ROOT)
        if path in pins and pins[path] != digest:
            raise ValueError('Conflicting ancestor pin')
        pins[path] = digest
    # Do not replace old provenance entries if this reader imports a historical
    # helper. A changed ancestor must fail, not get silently repinned.
    def pin(path):
        path = Path(path).resolve()
        path.relative_to(ROOT)
        digest = sha(path)
        if path in pins and pins[path] != digest:
            raise ValueError('Changed pinned ancestor: '+str(path))
        pins[path] = digest
    for path in (source, native/'input_manifest.json', native/'input_manifest_path.txt',
                 native/'completed.json', run/'request.json', run/'completed.json',
                 Path(__file__), Path(prior.__file__)):
        pin(path)
    for row in manifest['inputs']:
        for filename, digest in row['files'].items():
            path = (source.parent/row['name']/filename).resolve()
            path.relative_to(ROOT)
            if path in pins and pins[path] != digest:
                raise ValueError('Conflicting source pin')
            pins[path] = digest
    def verify():
        for path, digest in pins.items():
            if sha(path) != digest:
                raise ValueError('Changed native audit source: '+str(path))
    verify()
    reference = FutaleufuBed(ROOT/'tmp/futaleufu-continuous-source-window-v2',
        PREFIX/'hydrology/channel_profile_2026_10_v2',
        PREFIX/'hydrography/confluence_network_2026_10_v1/network.json', depth_m=1.8)
    size = manifest['grid']['tile_cells']
    keys = [tuple(k) for k in manifest['tile_indices']]
    shape = (len(keys)*size, size)
    frames, errors, initial, previous = [], [], None, None
    for step in expected:
        folder = native/('frame_%06d'%step)
        receipt_path = folder/'complete.json'
        pin(receipt_path)
        receipt = json.loads(receipt_path.read_text())
        prior.validate_receipt(receipt, step, manifest['initial_time_seconds'], .01)
        arrays = {}
        for name in ('h', 'u', 'v'):
            path = folder/(name+'.npy')
            pin(path)
            arrays[name] = np.load(path, mmap_mode='r', allow_pickle=False)
        if any(a.shape != shape or not np.isfinite(a).all() for a in arrays.values()):
            raise ValueError('Incomplete or nonfinite native arrays')
        h, u, v = (arrays[k] for k in ('h', 'u', 'v'))
        speed = np.hypot(u, v)
        if h.min() < 0 or h.max() > 10 or speed.max() > 20:
            raise ValueError('Unchanged native depth/speed gate failed')
        volume = float(h.sum())
        if abs(volume-receipt['volume_m3']) > 1e-6:
            raise ValueError('Native saved volume and receipt disagree')
        if initial is None:
            initial, initial_volume = arrays, volume
            restart = manifest['restart']
            if receipt['time_seconds'] != restart['source_time_seconds'] or any(
                    pins[folder/(k+'.npy')] != restart['source_arrays_sha256'][k] for k in arrays):
                raise ValueError('Restart bytes or clock changed')
        if abs(volume-initial_volume-receipt['boundary_volume_m3']-receipt['conservation_residual_m3']) > 1e-6:
            raise ValueError('Integrated native boundary flux and saved storage disagree')
        labels, offset, counts = connected_tiles({key: h[i*size:(i+1)*size] > .05
                                                  for i, key in enumerate(keys)})
        observations, common = observe_branches(reference, labels, offset,
            manifest['horizontal_origin_utm18s_m'], 1.)
        closed = prior.closed_wet_faces(h, keys, size, manifest['boundary_probes'])
        dry = [r for r in observations if not r['wet_components']]
        if not common or dry:
            errors.append(dict(step=step, reason='Original route disconnected or cross-section dry'))
        if closed:
            errors.append(dict(step=step, reason='Unintended wet exterior banks'))
        balance = prior.boundary_balance(manifest['boundary_probes'], receipt['exterior_fluxes'], manifest['inlet_budget'])
        wet = h > .05
        row = dict(step=step, time_seconds=receipt['time_seconds'], volume_m3=volume,
            maximum_depth_m=float(h.max()), maximum_speed_mps=float(speed.max()), wet_cells=int(wet.sum()),
            wet_speed_percentiles_mps=np.percentile(speed[wet], [10, 50, 90, 99]).tolist(),
            common_original_route_components=common, original_cross_sections=len(observations),
            dry_cross_sections=dry, wet_closed_exterior_faces=closed, boundary_balance=balance,
            maximum_step_residual_m3=receipt['maximum_step_residual_m3'],
            cumulative_mass_residual_m3=receipt['conservation_residual_m3'],
            storage_change_from_restart_m3=volume-initial_volume,
            maximum_depth_change_from_restart_m=float(np.max(np.abs(h-initial['h']))),
            arrays_sha256={k: pins[folder/(k+'.npy')] for k in arrays})
        if previous is not None:
            row['interval_storage_rate_m3s'] = (volume-previous['volume_m3'])/(row['time_seconds']-previous['time_seconds'])
        frames.append(row)
        previous = row
        print('Audited complete native frame %d at %.2f seconds' % (step, row['time_seconds']), flush=True)
    verify()
    report = dict(schema='raftsim.futaleufu_native_continuation_audit.v1',
        native_run=run.relative_to(ROOT).as_posix(), terminal_run_audited=True,
        requested_native_snapshot_steps=expected, errors=errors, numerical_geographic_checks_passed=not errors,
        frames=frames, settled_hydraulics=False, normal_map_integrated=False, packaged_fps_verified=False,
        assumptions='400 m3/s total (30 Azul + 370 upstream mainstem) is inferred, not local gauging',
        scope='Every requested complete native snapshot; unchanged conservation/connectivity/bank gates, no resimulation or synthesized flow',
        sources_sha256={p.relative_to(ROOT).as_posix(): h for p, h in pins.items()})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps(dict(errors=errors, final_time_seconds=frames[-1]['time_seconds'],
                          boundary_balance=frames[-1]['boundary_balance'])), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run, args.out)
    if result['errors']:
        raise SystemExit(1)
