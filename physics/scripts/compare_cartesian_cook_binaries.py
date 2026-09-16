"""Compare unchanged full-domain inputs, physical records and saved native arrays.

Alternating-order component timings are NOT engine FPS or settled hydraulics.
Never overwrite evidence, kill a slow process, or alter either live executable.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def physical_records(rows):
    records = []
    for row in rows:
        seconds = row['elapsed_wall_seconds']
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError('Invalid native elapsed time')
        records.append({key: value for key, value in row.items() if key != 'elapsed_wall_seconds'})
    if not records or records[0]['step'] != 0:
        raise ValueError('Missing initial state record')
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--steps', type=int, default=20)
    parser.add_argument('--repeats', type=int, default=4)
    args = parser.parse_args()
    if args.steps < 1 or args.repeats < 2:
        parser.error('Positive steps and at least two alternating pairs required')
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text())
    if manifest['schema'] != 'raftsim.cartesian_flow_cook.v1':
        raise ValueError('Native Cartesian cook manifest required')
    inputs = {manifest_path: digest(manifest_path)}
    for record in manifest['inputs']:
        for name, expected in record['files'].items():
            path = manifest_path.parent / record['name'] / name
            if digest(path) != expected:
                raise ValueError(f'Changed source input: {path}')
            inputs[path] = expected
    binaries = dict(baseline=args.baseline.resolve(), candidate=args.candidate.resolve())
    binary_hashes = {name: digest(path) for name, path in binaries.items()}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = dict(schema='raftsim.cartesian_cook_binary_comparison.v1',
                  input_manifest=str(manifest_path), input_manifest_sha256=inputs[manifest_path],
                  input_files=len(inputs), binary_sha256=binary_hashes,
                  steps=args.steps, repeats=args.repeats, runs=[], pairs=[],
                  physical_acceptance=False, engine_fps_accepted=False, passed=False)
    try:
        for repeat in range(args.repeats):
            results = {}
            for variant in (('baseline', 'candidate') if repeat % 2 == 0 else ('candidate', 'baseline')):
                if digest(binaries[variant]) != binary_hashes[variant]:
                    raise ValueError('Executable changed during comparison')
                destination = output / f'{repeat}-{variant}'
                command = [str(binaries[variant]), str(manifest_path), str(destination), str(args.steps), str(args.steps)]
                start = time.perf_counter()
                with (output/f'{repeat}-{variant}.log').open('w') as log:
                    process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                    print(json.dumps(dict(repeat=repeat, variant=variant, pid=process.pid, status='running')), flush=True)
                    code = process.wait()
                elapsed = time.perf_counter()-start
                if code != 0 or not json.loads((destination/'completed.json').read_text())['completed']:
                    raise RuntimeError(f'{variant} repeat {repeat} failed with exit {code}')
                rows = [json.loads(line) for line in (destination/'progress.jsonl').read_text().splitlines()]
                if rows[-1]['step'] != args.steps or not rows[-1]['snapshot']:
                    raise ValueError('Native comparison stopped before final snapshot')
                frames = {}
                for row in rows:
                    if not row['snapshot']:
                        continue
                    frame = destination/f"frame_{row['step']:06d}"
                    if physical_records([rows[0], json.loads((frame/'complete.json').read_text())])[-1] != physical_records([rows[0], row])[-1]:
                        raise ValueError('Snapshot/progress record mismatch')
                    for field in ('h', 'u', 'v'):
                        frames[f"{frame.name}/{field}.npy"] = digest(frame/f'{field}.npy')
                # Exclude startup before the initial progress record, not any
                # solve work. Includes initial snapshot writes and later inspections.
                solve_seconds = rows[-1]['elapsed_wall_seconds']-rows[0]['elapsed_wall_seconds']
                if not math.isfinite(solve_seconds) or solve_seconds <= 0:
                    raise ValueError('Missing positive solve/capture interval')
                results[variant] = dict(physical=physical_records(rows), frames=frames)
                report['runs'].append(dict(repeat=repeat, variant=variant, command=command,
                    returncode=code, process_seconds=elapsed, solve_capture_seconds=solve_seconds,
                    snapshot_arrays=frames))
                print(json.dumps(dict(repeat=repeat, variant=variant, seconds=solve_seconds, status='complete')), flush=True)
            exact = results['baseline'] == results['candidate']
            report['pairs'].append(dict(repeat=repeat, candidate_first=bool(repeat % 2),
                                       all_records_and_snapshot_arrays_exact=exact))
            if not exact:
                raise ValueError('Physical record or saved array changed')
        for path, expected in inputs.items():
            if digest(path) != expected:
                raise ValueError(f'Comparison source changed: {path}')
        report['inputs_unchanged'] = True
        report['median_solve_capture_seconds'] = {
            variant: statistics.median(row['solve_capture_seconds'] for row in report['runs'] if row['variant'] == variant)
            for variant in binaries}
        report['passed'] = True
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['median_solve_capture_seconds'], indent=2))


if __name__ == '__main__':
    main()
