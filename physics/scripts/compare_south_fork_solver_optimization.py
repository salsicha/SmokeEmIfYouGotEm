"""A/B solver changes against identical survey inputs; never promote fields.

Compare every saved frame byte-for-byte, including dry masks and derived
fields. Alternate execution order to reduce warm-cache/thermal timing bias.
Timings include exports and are not engine FPS or physical acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time
import math

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reported_timings(stdout):
    """Old binaries have no internal timings; missing is not zero work."""
    result={}
    for line in stdout.splitlines():
        key, separator, value=line.partition('=')
        if separator and key in ('solve_and_capture_seconds','export_seconds'):
            seconds=float(value)
            if not math.isfinite(seconds) or seconds<0 or key in result:
                raise ValueError('Invalid or duplicate solver timing')
            result[key]=seconds
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-manifest', type=Path, default=ROOT / 'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-conservative-edge/run_result.json')
    parser.add_argument('--steps', type=int, default=100)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    if args.steps <= 0 or args.repeats <= 0:
        parser.error('steps and repeats must be positive')
    # No reuse: existing raw comparisons are evidence, not scratch to overwrite.
    args.output.mkdir(parents=True, exist_ok=False)
    command = json.loads(args.run_manifest.read_text())['command'][1:]
    binaries = {'baseline': args.baseline.resolve(), 'candidate': args.candidate.resolve()}
    report = {'schema': 'raftsim.survey.solver_equivalence.v1',
              'source_run_manifest': str(args.run_manifest.resolve()),
              'binary_sha256': {name: digest(path) for name, path in binaries.items()},
              'steps': args.steps, 'repeats': args.repeats, 'runs': [],
              'production_promoted': False, 'physical_acceptance': False}
    comparisons = []
    for repeat in range(args.repeats):
        frames = {}
        for name in (('baseline', 'candidate') if repeat % 2 == 0 else ('candidate', 'baseline')):
            output = args.output.resolve() / f'{repeat}-{name}'
            invocation = list(command)
            for flag, value in (('--output', output), ('--steps', args.steps),
                                ('--frame-interval', max(1, args.steps // 10))):
                invocation[invocation.index(flag) + 1] = str(value)
            start = time.perf_counter()
            result = subprocess.run([str(binaries[name]), *invocation], cwd=ROOT,
                                    capture_output=True, text=True, timeout=300)
            elapsed = time.perf_counter() - start
            (args.output / f'{repeat}-{name}.log').write_text(result.stdout + result.stderr)
            record = {'repeat': repeat, 'variant': name, 'seconds': elapsed,
                      'returncode': result.returncode, 'command': invocation,
                      'internal_timings': reported_timings(result.stdout)}
            report['runs'].append(record)
            frames[name] = {str(path.relative_to(output)): digest(path)
                            for path in sorted(output.glob('*/frames/*.csv'))}
        comparisons.append(bool(frames['baseline']) and frames['baseline'] == frames['candidate'])
    report['all_saved_frames_bitwise_identical'] = all(comparisons)
    report['all_processes_succeeded'] = all(run['returncode'] == 0 for run in report['runs'])
    report['median_seconds'] = {name: statistics.median(run['seconds'] for run in report['runs']
                               if run['variant'] == name) for name in binaries}
    report['candidate_time_reduction_fraction'] = 1 - report['median_seconds']['candidate'] / report['median_seconds']['baseline']
    if all('solve_and_capture_seconds' in run['internal_timings'] for run in report['runs']):
        report['median_solve_and_capture_seconds'] = {
            name: statistics.median(run['internal_timings']['solve_and_capture_seconds']
                for run in report['runs'] if run['variant']==name) for name in binaries}
        times=report['median_solve_and_capture_seconds']
        report['solve_and_capture_time_reduction_fraction']=1-times['candidate']/times['baseline'] if times['baseline']>0 else None
    report['passed'] = report['all_saved_frames_bitwise_identical'] and report['all_processes_succeeded']
    (args.output / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
