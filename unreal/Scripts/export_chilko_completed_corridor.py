"""Export the full one-metre Chilko terrain only after its full depth fit passes.

No partial fit, smaller corridor, changed bank guard or relaxed flow target is
accepted. Resource limits interrupt only this owned exporter and preserve its
partial outputs; a partial directory is never an accepted terrain manifest.
"""
import argparse
import _thread
import json
from pathlib import Path
import threading
import time

import numpy as np

from qualify_futaleufu_native_ports import ROOT, sha, resources
from export_chilko_corridor_terrain import export, corridor_chunks
from chilko_corridor_bed import CorridorBed


def validate_depth_arrays(arrays, expected_sections=25552):
    stations = arrays['station_m']
    depth = arrays['depth_amplitude_m']
    previous = arrays['previous_depth_amplitude_m']
    chart = arrays['capacity_chart_station_m']
    capacity = arrays['inferred_capacity_m3s']
    width = arrays['available_width_m']
    if (stations.ndim != 1 or len(stations) != 55725 or depth.shape != stations.shape or previous.shape != depth.shape
            or chart.shape != (expected_sections,) or capacity.shape != chart.shape or width.shape != chart.shape
            or not all(np.isfinite(a).all() for a in (stations, depth, previous, chart, capacity, width))
            or np.any(np.diff(stations) <= 0) or np.any(np.diff(chart) <= 0)
            or np.any(depth < previous) or np.any(depth > 10.) or np.any(depth <= 0)
            or np.any(capacity < 45.) or np.any(width <= 0)):
        raise ValueError('Entire source-bound depth fit must be finite, ordered and pass unchanged capacity/depth limits')
    return dict(profile_samples=len(stations), complete_chart_sections=len(chart),
                capacity_minimum_m3s=float(capacity.min()), maximum_amplitude_m=float(depth.max()),
                changed_profile_samples=int(np.count_nonzero(depth > previous+1e-6)))


def run(fit_job, depth, output, job):
    fit_job, depth, output, job = [Path(p).resolve() for p in (fit_job, depth, output, job)]
    for p in (fit_job, depth, output, job): p.relative_to(ROOT)
    if output.exists() or job.exists(): raise ValueError('Fresh full terrain output and job directories required')
    completion_path = fit_job/'completed.json'
    completion = json.loads(completion_path.read_text())
    manifest_path = depth/'manifest.json'
    if completion['exit_code'] or not completion['inputs_unchanged'] or sha(manifest_path) != completion['manifest_sha256']:
        raise ValueError('The actual full depth fit did not finish with unchanged inputs')
    request_path = fit_job/'request.json'
    request = json.loads(request_path.read_text())
    pins = {Path(p): h for p, h in request['pinned_sha256'].items()}
    for p in (completion_path, request_path, manifest_path, Path(__file__).resolve()): pins[p] = sha(p)
    manifest = json.loads(manifest_path.read_text())
    if (manifest['schema'] != 'raftsim.chilko_available_channel_depth.v1' or manifest['discharge_m3s'] != 45.
            or manifest['manning_n'] != .045 or manifest['maximum_allowed_amplitude_m'] != 10.
            or manifest['capacity_grid']['spacing_m'] != 1.
            or manifest['capacity_grid']['horizontal_origin_m'] != [442000., 5749000.]):
        raise ValueError('Reviewed exact one-metre capacity lattice required')
    pins[depth/'depth.npz'] = manifest['depth_sha256']

    def verify():
        for p, h in pins.items():
            if sha(p) != h: raise ValueError('Changed Chilko export input: '+str(p))

    verify()
    with np.load(depth/'depth.npz', allow_pickle=False) as z:
        checked = validate_depth_arrays(z)
    profile = ROOT/'tmp/chilko-full-corridor-profile-v13-source-local-1m'
    terrain = ROOT/'tmp/chilko-full-corridor-conditioned-terrain-v1'
    model = CorridorBed(terrain, profile, 45., .045, depth_profile=depth)
    indices = corridor_chunks(model.line, [442000., 5749000.], 600., spacing_m=1.)
    # Conservative uncompressed allowance for the encoded PNG and provenance
    # arrays; the monitor still enforces the reserve throughout construction.
    allowance = len(indices)*127*127*128+1024**3
    initial = resources()
    if (initial['free_disk_bytes'] < 40*1024**3+allowance
            or min(initial['available_physical_bytes'], initial['available_commit_bytes']) < 6*1024**3):
        raise ValueError('Full corridor resource allowance unavailable; do not export a smaller substitute')
    job.mkdir(parents=True)

    def save(name, value): (job/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')

    save('request.json', dict(complete_fit=checked, expected_chunks=len(indices), route_length_m=model.line.length,
        origin_m=[442000.,5749000.], vertical_datum_m=900., spacing_m=1., buffer_m=600.,
        uncompressed_storage_allowance_bytes=allowance, initial_resources=initial, timeout_seconds=24*3600,
        inputs_sha256={p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        scope='Complete encoded terrain construction only; no native hydraulic, boat, vegetation or packaged-FPS acceptance'))
    del model
    started = time.monotonic()
    done = threading.Event()
    minimum = initial.copy()
    failure = []

    def monitor():
        while not done.wait(5.):
            r = resources()
            minimum.update({k: min(minimum[k], r[k]) for k in r})
            if r['free_disk_bytes'] < 40*1024**3: failure.append('Owned export disk reserve reached')
            if min(r['available_physical_bytes'], r['available_commit_bytes']) < 3*1024**3:
                failure.append('Owned export memory/commit reserve reached')
            if time.monotonic()-started > 24*3600: failure.append('Owned export exceeded one-day bound')
            if failure:
                _thread.interrupt_main()
                return

    guard = threading.Thread(target=monitor, daemon=True)
    guard.start()
    try:
        result = export(terrain, profile, output, [442000.,5749000.], 900., buffer_m=600.,
                        discharge=45., roughness=.045, depth_profile=depth, spacing_m=1.)
        verify()
        if failure or len(result['chunks']) != len(indices): raise ValueError('Full export incomplete or resource guard failed')
        save('completed.json', dict(elapsed_seconds=time.monotonic()-started, minimum_resources=minimum,
            manifest_sha256=sha(output/'manifest.json'), chunks=len(result['chunks']),
            maximum_shared_edge_encoded_difference=result['shared_edge_max_encoded_difference'],
            inputs_unchanged=True, hydraulic_accepted=False, engine_validated=False))
        print('Complete source-exact Chilko terrain export finished', flush=True)
    except BaseException as exc:
        save('failure.json', dict(error=failure or [str(exc)], elapsed_seconds=time.monotonic()-started,
             minimum_resources=minimum, partial_output_preserved=str(output)))
        raise
    finally:
        done.set(); guard.join(timeout=10.)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('fit-job', 'depth', 'out', 'job'): p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args(); run(a.fit_job, a.depth, a.out, a.job)
