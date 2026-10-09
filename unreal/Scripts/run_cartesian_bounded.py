"""Run one bounded native Cartesian cook and record its terminal receipt.

Layout matches the Futaleufu continuation audit: <run>/request.json,
<run>/native/ (the cook's own output) and <run>/completed.json. The receipt
records the exit code and whether the saved frame 0 and clock are exactly
the package's declared start (manifest 'restart': array hashes and time).
Physics, steps and timestep are the package's own; nothing is forced.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(package, output, solver, steps, interval, lanes):
    package, output, solver = (Path(p).resolve() for p in (package, output, solver))
    if output.exists():
        raise ValueError('Fresh run directory required')
    manifest_path = package / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    native = output / 'native'
    command = [str(solver), str(manifest_path), str(native), str(steps), str(interval), str(lanes)]
    output.mkdir(parents=True)
    request = dict(command=command, steps=steps, snapshot_interval_steps=interval, dt_seconds=manifest['dt_seconds'],
                   source_time_seconds=manifest.get('initial_time_seconds', 0.0), solver_sha256=sha(solver),
                   package_manifest_sha256=sha(manifest_path))
    (output / 'request.json').write_text(json.dumps(request, indent=2) + '\n')
    started = time.time()
    with open(output / 'native.log', 'w') as log:
        code = subprocess.call(command, stdout=log, stderr=subprocess.STDOUT)
    exact = False
    first = native / 'frame_000000'
    restart = manifest.get('restart')
    if restart and (first / 'complete.json').is_file():
        receipt = json.loads((first / 'complete.json').read_text())
        exact = (receipt['time_seconds'] == restart['source_time_seconds'] and
                 all(sha(first / (k + '.npy')) == restart['source_arrays_sha256'][k] for k in 'huv'))
    completion = dict(exit_code=code, elapsed_seconds=time.time() - started,
                      native_restart_fields_and_clock_exact=exact,
                      settled_hydraulics=False, normal_map_integrated=False)
    (output / 'completed.json' if code == 0 else output / 'failure.json').write_text(json.dumps(completion, indent=2) + '\n')
    print(json.dumps(completion))
    return completion


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--solver', required=True, type=Path)
    parser.add_argument('--steps', type=int, default=3000)
    parser.add_argument('--interval', type=int, default=300)
    parser.add_argument('--lanes', type=int, default=12)
    args = parser.parse_args()
    run(args.package, args.out, args.solver, args.steps, args.interval, args.lanes)
