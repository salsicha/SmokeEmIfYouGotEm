"""Independently audit saved native continuation fields, never synthesize flow.

This deliberately reports hydraulic transients separately from numerical and
geographic validity. A connected, conservative run is not a settled river or
playable-map acceptance. Only complete, immutable snapshot folders are read.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from build_futaleufu_continuous_water_domain import (
    ROOT, PREFIX, sha, FutaleufuBed, connected_tiles, observe_branches)
from prepare_futaleufu_hydraulic_ports import FACES


def boundary_balance(probes, fluxes, budget):
    """Native flux sign is positive INTO the domain on every edge."""
    if len(probes) != len(fluxes) or not np.isfinite(fluxes).all():
        raise ValueError('Incomplete/nonfinite native boundary fluxes')
    seen = set()
    incoming, outgoing = {}, {}
    for probe, value in zip(probes, fluxes):
        key = (probe['tile_index'], probe['edge'])
        if key in seen or probe['edge'] not in FACES:
            raise ValueError('Invalid or duplicate exterior face')
        seen.add(key)
        if probe['role'] not in ('upstream', 'downstream'):
            raise ValueError('Unclassified physical boundary')
        dest = incoming if probe['role'] == 'upstream' else outgoing
        sign = 1. if probe['role'] == 'upstream' else -1.
        name = probe['branch']
        dest[name] = dest.get(name, 0.) + sign * float(value)
    if set(incoming) != set(budget):
        raise ValueError('Missing inlet budget/face')
    for name, actual in incoming.items():
        target = budget[name]['target_m3s']
        if not np.isfinite(target) or target <= 0 or abs(actual-target) > 1e-8*max(1., target):
            raise ValueError('Actual native inlet differs from prescribed discharge')
    inlet, outlet = sum(incoming.values()), sum(outgoing.values())
    return dict(inlets_m3s=incoming, outlets_m3s=outgoing,
                total_inlet_m3s=inlet, total_outlet_m3s=outlet,
                instantaneous_storage_rate_m3s=inlet-outlet,
                outlet_to_inlet_ratio=outlet/inlet,
                reverse_outlet_flow=any(q < 0 for q in outgoing.values()))


def validate_receipt(receipt, step, initial_time, dt):
    values = [receipt[k] for k in ('time_seconds', 'volume_m3', 'boundary_volume_m3',
              'conservation_residual_m3', 'maximum_step_residual_m3')]
    if not np.isfinite(values).all() or receipt['step'] != step or not receipt['snapshot']:
        raise ValueError('Invalid native snapshot receipt')
    if abs(receipt['time_seconds']-(initial_time+step*dt)) > 1e-9:
        raise ValueError('Actual native continuation clock differs')
    if receipt['maximum_step_residual_m3'] < 0 or receipt['maximum_step_residual_m3'] > .001*dt:
        raise ValueError('Unchanged native step-conservation gate failed')


def closed_wet_faces(h, keys, size, probes):
    if h.shape != (len(keys)*size, size) or len(set(keys)) != len(keys):
        raise ValueError('Invalid tile field layout')
    tile_set = set(keys)
    open_faces = {(p['tile_index'], p['edge']) for p in probes}
    result = []
    for i, key in enumerate(keys):
        for edge, (sl, delta, _, _) in FACES.items():
            if (key[0]+delta[0], key[1]+delta[1]) in tile_set or (i, edge) in open_faces:
                continue
            values = h[i*size:(i+1)*size][sl]
            if np.any(values > .05):
                result.append(dict(tile=list(key), edge=edge,
                                   maximum_depth_m=float(values.max())))
    return result


def audit(run, output):
    run, output = Path(run).resolve(), Path(output).resolve()
    run.relative_to(ROOT)
    output.relative_to(ROOT)
    if output.exists():
        raise ValueError('Fresh audit output required; preserve prior evidence')
    native = run/'native'
    source = Path((native/'input_manifest_path.txt').read_text().strip()).resolve()
    source.relative_to(ROOT)
    if sha(source) != sha(native/'input_manifest.json'):
        raise ValueError('Native manifest differs from its actual input')
    manifest = json.loads(source.read_text())
    if manifest['schema'] != 'raftsim.cartesian_flow_cook.v1' or manifest['grid']['cell_m'] != 1.:
        raise ValueError('Reviewed one-metre native domain required')
    request = json.loads((run/'request.json').read_text())
    if manifest['dt_seconds'] != .01 or request['steps'] != 3000:
        raise ValueError('Reviewed bounded continuation required')
    size = manifest['grid']['tile_cells']
    keys = [tuple(k) for k in manifest['tile_indices']]
    shape = (len(keys)*size, size)
    initial_time = manifest['initial_time_seconds']
    pins = {ROOT/p: h for p, h in manifest['sources_sha256'].items()}
    pins.update({source: sha(source), run/'request.json': sha(run/'request.json'),
                 Path(__file__): sha(__file__)})
    for row in manifest['inputs']:
        pins.update({source.parent/row['name']/f: h for f, h in row['files'].items()})

    def verify():
        for path, digest in pins.items():
            if sha(path) != digest:
                raise ValueError('Changed audit source: '+str(path))

    verify()
    reference = FutaleufuBed(ROOT/'tmp/futaleufu-continuous-source-window-v2',
        PREFIX/'hydrology/channel_profile_2026_10_v2',
        PREFIX/'hydrography/confluence_network_2026_10_v1/network.json', depth_m=1.8)
    # Freeze the available set first. A running producer may finish newer frames.
    steps = [s for s in range(0, request['steps']+1, 300)
             if (native/('frame_%06d'%s)/'complete.json').is_file()]
    if not steps or steps != list(range(0, steps[-1]+1, 300)):
        raise ValueError('Missing or noncontiguous completed native snapshots')
    frames, errors, initial, previous = [], [], None, None
    for step in steps:
        folder = native/('frame_%06d'%step)
        receipt_path = folder/'complete.json'
        pins[receipt_path] = sha(receipt_path)
        receipt = json.loads(receipt_path.read_text())
        validate_receipt(receipt, step, initial_time, manifest['dt_seconds'])
        arrays = {}
        for name in ('h', 'u', 'v'):
            path = folder/(name+'.npy')
            pins[path] = sha(path)
            arrays[name] = np.load(path, mmap_mode='r', allow_pickle=False)
        if any(a.shape != shape or not np.isfinite(a).all() for a in arrays.values()):
            raise ValueError('Incomplete/nonfinite saved native arrays')
        h, u, v = (arrays[k] for k in ('h', 'u', 'v'))
        speed = np.hypot(u, v)
        if h.min() < 0 or h.max() > 10 or speed.max() > 20:
            raise ValueError('Unchanged depth/speed/finite gate failed')
        volume = float(h.sum())
        if abs(volume-receipt['volume_m3']) > 1e-6:
            raise ValueError('Actual saved volume differs from native receipt')
        if initial is None:
            initial = arrays
            restart = manifest['restart']
            for k in arrays:
                if pins[folder/(k+'.npy')] != restart['source_arrays_sha256'][k]:
                    raise ValueError('Restart native field bytes changed')
            if receipt['time_seconds'] != restart['source_time_seconds']:
                raise ValueError('Restart native clock changed')
            initial_volume = volume
        if abs((volume-initial_volume)-receipt['boundary_volume_m3']-receipt['conservation_residual_m3']) > 1e-6:
            raise ValueError('Saved volume and integrated native boundary flux disagree')
        labels, offset, counts = connected_tiles({key: h[i*size:(i+1)*size] > .05
                                                  for i, key in enumerate(keys)})
        observations, common = observe_branches(reference, labels, offset,
                                                manifest['horizontal_origin_utm18s_m'], 1.)
        closed = closed_wet_faces(h, keys, size, manifest['boundary_probes'])
        balance = boundary_balance(manifest['boundary_probes'], receipt['exterior_fluxes'], manifest['inlet_budget'])
        if not common: errors.append(dict(step=step, reason='Original route disconnected'))
        if closed: errors.append(dict(step=step, reason='Unintended wet exterior banks'))
        # Preserve even nanolitre-scale outlet sign changes as diagnostics.
        # A cold-start transient is not itself a numerical/geographic failure;
        # this audit never grants settled-hydraulics acceptance in either case.
        wet = h > .05
        row = dict(step=step, time_seconds=receipt['time_seconds'], volume_m3=volume,
            maximum_depth_m=float(h.max()), maximum_speed_mps=float(speed.max()),
            wet_cells=int(wet.sum()), wet_speed_percentiles_mps=np.percentile(speed[wet], [10, 50, 90, 99]).tolist(),
            common_original_route_components=common, original_cross_sections=len(observations),
            dry_cross_sections=[r for r in observations if not r['wet_components']],
            wet_closed_exterior_faces=closed, boundary_balance=balance,
            maximum_step_residual_m3=receipt['maximum_step_residual_m3'],
            cumulative_mass_residual_m3=receipt['conservation_residual_m3'],
            storage_change_from_restart_m3=volume-initial_volume,
            maximum_depth_change_from_restart_m=float(np.max(np.abs(h-initial['h']))),
            arrays_sha256={k: pins[folder/(k+'.npy')] for k in arrays})
        if previous is not None:
            elapsed = row['time_seconds']-previous['time_seconds']
            row['interval_storage_rate_m3s'] = (volume-previous['volume_m3'])/elapsed
        frames.append(row)
        previous = row
        print('Audited actual native frame %d at %.2f seconds' % (step, receipt['time_seconds']), flush=True)
    verify()
    terminal = (run/'completed.json').is_file() and steps[-1] == request['steps']
    if terminal:
        completion = json.loads((run/'completed.json').read_text())
        if completion['exit_code'] or not completion['native_restart_fields_and_clock_exact']:
            raise ValueError('Native terminal wrapper did not validate success')
        pins[run/'completed.json'] = sha(run/'completed.json')
    report = dict(schema='raftsim.futaleufu_native_continuation_audit.v1',
        native_run=run.relative_to(ROOT).as_posix(), terminal_run_audited=terminal,
        errors=errors, numerical_geographic_checks_passed=not errors, frames=frames,
        assumptions='400 m3/s total (30 Azul + 370 upstream mainstem) is an inferred construction, not local gauging',
        settled_hydraulics=False, normal_map_integrated=False, packaged_fps_verified=False,
        scope='Actual fixed-step native states only; no terrain changes, velocity seed, or gameplay acceptance',
        sources_sha256={p.relative_to(ROOT).as_posix(): h for p, h in pins.items()})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(terminal_run_audited=terminal, errors=errors,
        final_time_seconds=frames[-1]['time_seconds'], final_boundary_balance=frames[-1]['boundary_balance'])), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run, args.out)
    if result['errors']: raise SystemExit(1)
