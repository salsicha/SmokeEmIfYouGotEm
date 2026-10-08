"""Resource-guarded 300-second native advance from an independently audited state.

Copies unchanged physical scenarios and exact native h/u/v, not an authored
replacement current. Numerical completion still requires a new geographic and
settling audit. This never updates the normal game map by itself.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from qualify_futaleufu_native_ports import ROOT, sha, resources
from continue_futaleufu_native_flow import shared_native_work, require_launch_headroom


def prelaunch_check(output, verify):
    """Checkpoint serialization is not a reservation on the shared engine."""
    try:
        verify()
        current, busy = resources(), shared_native_work()
        (output/'prelaunch.json').write_text(json.dumps(
            dict(resources=current, shared_work=busy), indent=2, allow_nan=False)+'\n')
        require_launch_headroom(current, busy)
        return current
    except Exception as exc:
        (output/'failure.json').write_text(json.dumps(dict(stage='prelaunch',
            native_process_started=False, failure=str(exc)), indent=2, allow_nan=False)+'\n')
        raise


def watchdog_failure(current, busy, elapsed):
    if busy: return 'Shared engine/build/cook appeared; stopped only owned checkpoint continuation'
    if min(current['available_physical_bytes'], current['available_commit_bytes']) < 3*1024**3:
        return 'Owned cook resource floor reached'
    if current['free_disk_bytes'] < 40*1024**3: return 'Owned cook disk reserve reached'
    if elapsed > 4*3600: return 'Owned cook four-hour bound reached'
    return None


def require_terminal_audit(audit):
    if (audit.get('schema') != 'raftsim.futaleufu_native_continuation_audit.v1'
            or not audit.get('terminal_run_audited') or audit.get('errors')
            or not audit.get('numerical_geographic_checks_passed') or not audit.get('frames')):
        raise ValueError('Independent successful terminal geographic audit required')
    last = audit['frames'][-1]
    if (not last['common_original_route_components'] or last['dry_cross_sections']
            or last['wet_closed_exterior_faces']):
        raise ValueError('Audited river route or exterior banks failed')
    return last


def exact_state(h, u, v, shape):
    if any(a.shape != shape or not np.isfinite(a).all() for a in (h, u, v)):
        raise ValueError('Finite complete native restart arrays required')
    if h.min() < 0 or h.max() > 10 or np.hypot(u, v).max() > 20:
        raise ValueError('Restart violates unchanged native state gates')


def run(audit_path, solver, output):
    audit_path, solver, output = [Path(p).resolve() for p in (audit_path, solver, output)]
    output.relative_to(ROOT)
    if output.exists(): raise ValueError('Fresh bounded continuation output required')
    if sha(solver) != 'fb2624bb8cb210142ae17741c5358c86a48d6f42c60eedab64715def53c6e558':
        raise ValueError('Existing source-verified native executable required')
    require_launch_headroom(resources(), shared_native_work())
    audit = json.loads(audit_path.read_text())
    last = require_terminal_audit(audit)
    previous = ROOT/audit['native_run']
    native = previous/'native'
    source = Path((native/'input_manifest_path.txt').read_text().strip()).resolve()
    source.relative_to(ROOT)
    if sha(source) != sha(native/'input_manifest.json'):
        raise ValueError('Actual native source manifest changed')
    m = json.loads(source.read_text())
    if m['schema'] != 'raftsim.cartesian_flow_cook.v1' or m['dt_seconds'] != .01:
        raise ValueError('Reviewed full native domain required')
    frame = native/('frame_%06d'%last['step'])
    receipt = json.loads((frame/'complete.json').read_text())
    if receipt['time_seconds'] != last['time_seconds']:
        raise ValueError('Audited actual clock differs')
    pins = {ROOT/p: h for p, h in audit['sources_sha256'].items()}
    for p in (audit_path, solver, Path(__file__).resolve()): pins[p] = sha(p)
    guard_source=ROOT/'unreal/Scripts/continue_futaleufu_native_flow.py'
    if guard_source in pins and pins[guard_source] != sha(guard_source):
        raise ValueError('Audited launch-guard source changed')
    pins[guard_source]=sha(guard_source)

    def verify():
        for path, digest in pins.items():
            if sha(path) != digest: raise ValueError('Changed exact-continuation input: '+str(path))

    verify()
    state = {k: np.load(frame/(k+'.npy'), mmap_mode='r', allow_pickle=False) for k in ('h', 'u', 'v')}
    size = m['grid']['tile_cells']
    exact_state(*[state[k] for k in ('h', 'u', 'v')], (len(m['packages'])*size, size))
    initial_resources = resources()
    if (min(initial_resources['available_physical_bytes'], initial_resources['available_commit_bytes']) < 6*1024**3
            or initial_resources['free_disk_bytes'] < 43*1024**3):
        raise ValueError('Native run needs 6 GiB RAM/commit and 40 GiB disk plus 3 GiB allowance')
    output.mkdir(parents=True)
    packages = output/'packages'
    packages.mkdir()
    updated = copy.deepcopy(m)
    updated['inputs'] = []
    for i, name in enumerate(m['packages']):
        before, after = source.parent/name, packages/name
        after.mkdir()
        for filename in ('bed.npy', 'scenario.json', 'features.json', 'probes.json'):
            shutil.copyfile(before/filename, after/filename)
            if sha(before/filename) != sha(after/filename):
                raise ValueError('Physical scenario/bed changed during copy')
        h, u, v = [state[k][i*size:(i+1)*size] for k in ('h', 'u', 'v')]
        bed = np.load(after/'bed.npy', allow_pickle=False)
        np.savez_compressed(after/'initial_state.npz', depth=h, eta=bed+h, u=u, v=v, hu=h*u, hv=h*v, wet=h>1e-6)
        with np.load(after/'initial_state.npz', allow_pickle=False) as z:
            if any(not np.array_equal(z[k], a) for k, a in (('depth', h), ('u', u), ('v', v))):
                raise ValueError('Serialized actual checkpoint changed')
        updated['inputs'].append(dict(name=name, files={f: sha(after/f) for f in
            ('bed.npy', 'scenario.json', 'features.json', 'probes.json', 'initial_state.npz')}))
    verify()
    updated.update(initial_time_seconds=receipt['time_seconds'],
        initial_state='Exact native checkpoint; no source/geometry/velocity reconstruction',
        restart=dict(source_frame=frame.relative_to(ROOT).as_posix(), source_time_seconds=receipt['time_seconds'],
                     source_arrays_sha256=last['arrays_sha256'], added_tiles=0, physical_inputs_unchanged=True),
        sources_sha256={p.relative_to(ROOT).as_posix(): h for p, h in pins.items()})
    manifest = packages/'manifest.json'
    manifest.write_text(json.dumps(updated, indent=2, allow_nan=False)+'\n')
    pins[manifest] = sha(manifest)
    for row in updated['inputs']:
        pins.update({packages/row['name']/f: h for f, h in row['files'].items()})
    steps, interval, timeout = 30000, 3000, 4*3600
    command = [str(solver), str(manifest), str(output/'native'), str(steps), str(interval), '4']

    def save(name, value): (output/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')

    save('request.json', dict(command=command, steps=steps, snapshot_interval_steps=interval, dt_seconds=.01,
         source_time_seconds=receipt['time_seconds'], target_time_seconds=receipt['time_seconds']+300.,
         maximum_wall_seconds=timeout, source_audit_sha256=sha(audit_path), initial_resources=initial_resources,
         guard='Recheck actual shared work and resources after preparation; stop only the owned native process on overlap/resource floor/timeout; preserve complete/failure fields'))
    minimum = prelaunch_check(output, verify).copy()
    failure = None
    started = time.monotonic()
    with (output/'native.log').open('x') as log:
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        save('launch.json', dict(pid=child.pid))
        print('Exact native checkpoint continuation PID '+str(child.pid), flush=True)
        while child.poll() is None:
            try: child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                r = resources()
                minimum = {k: min(minimum[k], r[k]) for k in r}
                try:
                    busy=shared_native_work(child.pid)
                    elapsed=time.monotonic()-started
                    with (output/'resources.jsonl').open('a') as telemetry:
                        telemetry.write(json.dumps(dict(elapsed_seconds=elapsed, resources=r,
                                                        shared_work=busy), allow_nan=False)+'\n')
                    failure=watchdog_failure(r,busy,elapsed)
                except Exception as exc:
                    failure='Native guard observation failed: '+str(exc)
                if failure:
                    child.terminate(); child.wait(timeout=30); break
    result = dict(exit_code=child.returncode, elapsed_seconds=time.monotonic()-started, minimum_resources=minimum,
                  settled_hydraulics=False, normal_map_integrated=False, packaged_fps_verified=False)
    try:
        if failure or child.returncode or not (output/'native/completed.json').is_file():
            raise RuntimeError(failure or 'Native state gate failed; inspect preserved failure fields')
        first = output/'native/frame_000000'
        if json.loads((first/'complete.json').read_text())['time_seconds'] != receipt['time_seconds']:
            raise ValueError('Native restart clock changed')
        if any(sha(first/(k+'.npy')) != last['arrays_sha256'][k] for k in state):
            raise ValueError('Native restart field bytes changed')
        verify()
        result.update(native_restart_fields_and_clock_exact=True, saved_state_geographic_audit_pending=True)
        save('completed.json', result)
        print(json.dumps(result), flush=True)
    except Exception as exc:
        result['failure'] = str(exc)
        save('failure.json', result)
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('audit', 'solver', 'out'): p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    run(a.audit, a.solver, a.out)
