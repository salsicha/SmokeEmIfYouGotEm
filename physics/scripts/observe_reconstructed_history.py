"""Observe a separate full original-start replay, without changing its equations.

Original live jobs are never attached, restarted, modified or substituted.
Optional exact construction reuse is checked against retained original accepted
step diagnostics. Trial snapshots are explicitly not accepted water states.
"""
import argparse
from contextlib import contextmanager, ExitStack
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import total_depth_bank_replay as bank
from replay_requested_reconstructed_owner import requested_replay
from reconstructed_pressure_adapter import reconstructed_pressure
from pressure_cut_endpoint_reference import exact_endpoint_cuts
from shared_pressure_construction_reference import shared_pressure_coefficients


def digest(data):
    return hashlib.sha256(data).hexdigest()


def cell_metrics(state, bed, rate=None, pressure=None):
    """Read-only diagnostics, no thresholded wetness or arithmetic in solver."""
    h = state[..., 0]
    velocity = np.divide(state[..., 1:3], h[..., None], out=np.zeros_like(state[..., 1:3]), where=h[..., None] > 0)
    speed = np.linalg.norm(velocity, axis=-1)
    flat = np.argsort(speed.ravel(), kind='stable')[-4:][::-1]
    cells = []
    for index in flat:
        point = np.unravel_index(index, h.shape)
        cell = dict(yx=[int(i) for i in point], depth_m=float(h[point]),
                    momentum=state[point][1:3].tolist(), velocity_mps=velocity[point].tolist(),
                    speed_mps=float(speed[point]), bed_m=float(bed[point]))
        if rate is not None:
            cell['mass_rate'] = float(rate[point][0])
            cell['momentum_rate'] = rate[point][1:3].tolist()
            cell['pressure_momentum_rate'] = pressure[point].tolist()
            if h[point] > 0:
                # Diagnostic grouping only; these arrays never feed evolution.
                cell['partial_velocity_rate_mps2'] = ((rate[point][1:3]-velocity[point]*rate[point][0])/h[point]).tolist()
                cell['pressure_velocity_rate_mps2'] = (pressure[point]/h[point]).tolist()
        cells.append(cell)
    return dict(maximum_speed_mps=float(speed.max()), minimum_positive_depth_m=float(h[h > 0].min()) if np.any(h > 0) else None,
                wet_cells=int(np.count_nonzero(h)), fastest_cells=cells)


class Observer:
    def __init__(self, output, emit, native_start):
        self.output, self.emit, self.native = output, emit, native_start
        self.rate_count = self.accepted_count = self.archives = 0
        self.next_speed = 0.
        self.last_bin = -1
        self.stage_time = native_start
        self.pressure = None

    def archive(self, kind, state, bed, **arrays):
        path = self.output / f'{kind}-{self.archives:06d}.npz'
        with path.open('xb') as stream:
            np.savez(stream, state=state, bed=bed, **arrays)
        self.archives += 1
        return dict(path=str(path.resolve()), sha256=digest(path.read_bytes()))

    @contextmanager
    def installed(self):
        original_rate, original_pressure, original_advance = bank.rate, bank.nonlinear_pressure_force, bank.advance

        def pressure(*args, **kwargs):
            result = original_pressure(*args, **kwargs)
            self.pressure = result[0].copy()
            return result

        def rate(state, bed, *args, **kwargs):
            self.pressure = None
            result = original_rate(state, bed, *args, **kwargs)
            if self.pressure is None:
                raise RuntimeError('Missing original pressure contribution')
            self.rate_count += 1
            metrics = cell_metrics(state, bed, result[0], self.pressure)
            event = dict(event='observed_trial_rate', rate_index=self.rate_count,
                         trial_native_seconds=self.stage_time, cfl_bound_s=result[1], **metrics)
            if metrics['maximum_speed_mps'] >= self.next_speed:
                event['snapshot'] = self.archive('trial', state, bed, rate=result[0], pressure=self.pressure)
                self.next_speed = max(1., 2*metrics['maximum_speed_mps'])
            self.emit(event)
            return result

        def advance(state, bed, *args, **kwargs):
            begin = self.native
            callback = kwargs.get('on_step')
            boundary = kwargs.get('boundary_at_time')
            if boundary is not None:
                def observed_boundary(elapsed, current):
                    self.stage_time = begin+elapsed
                    return boundary(elapsed, current)
                kwargs['boundary_at_time'] = observed_boundary

            def accepted(previous, current, stats):
                if callback is not None:
                    callback(previous, current, stats)
                self.native = begin+stats['elapsed_s']
                self.accepted_count += 1
                event = dict(event='observed_accepted_state', native_seconds=self.native,
                             accepted_index=self.accepted_count, **cell_metrics(current, bed))
                native_bin = int(self.native/.1)
                if native_bin > self.last_bin:
                    event['snapshot'] = self.archive('accepted', current, bed, previous=previous)
                    self.last_bin = native_bin
                self.emit(event)
            kwargs['on_step'] = accepted
            return original_advance(state, bed, *args, **kwargs)

        bank.rate, bank.nonlinear_pressure_force, bank.advance = rate, pressure, advance
        try:
            yield self
        finally:
            bank.rate, bank.nonlinear_pressure_force, bank.advance = original_rate, original_pressure, original_advance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--original-progress', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--optimized-construction', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    raw = args.input.read_bytes(); record = json.loads(raw)
    request_raw = Path(record['source_history']).read_bytes(); request = json.loads(request_raw)
    original_raw = args.original_progress.read_bytes()
    # Capture only complete newline-terminated records from a concurrently
    # growing log. Retain this prefix's hash, not a claim about later bytes.
    original_raw = original_raw[:original_raw.rfind(b'\n')+1]
    original = [json.loads(line) for line in original_raw.splitlines() if line.strip()]
    provenance = original[0]
    if provenance.get('source_sha256') != digest(raw) or provenance.get('request_source_sha256') != digest(request_raw):
        raise ValueError('Original main replay provenance differs')
    expected = {(e['interval'], e['steps']): e for e in original if e.get('event') == 'requested_history_accepted_step'}
    hashes = {str(p): digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob('*.py'))}
    for name, sha in provenance['implementation_hashes'].items():
        if hashes[str(Path(__file__).with_name(name))] != sha:
            raise ValueError('Original main dependency differs: '+name)
    args.output.mkdir()
    start = time.perf_counter(); compared = 0
    with (args.output/'progress.jsonl').open('x', encoding='utf-8') as stream:
        def emit(event):
            nonlocal compared
            if event.get('event') == 'requested_history_accepted_step':
                reference = expected.get((event['interval'], event['steps']))
                if reference is not None:
                    actual = {k: v for k, v in event.items() if k != 'wall_seconds'}
                    wanted = {k: v for k, v in reference.items() if k != 'wall_seconds'}
                    if actual != wanted:
                        raise RuntimeError('Observed replay differs from original accepted-step diagnostics')
                    compared += 1
                    event = dict(event, original_step_diagnostics_exact=True)
            encoded = json.dumps(dict(event, wall_seconds=time.perf_counter()-start), allow_nan=False)
            stream.write(encoded+'\n'); stream.flush(); print(encoded, flush=True)

        emit(dict(event='observation_provenance', source_sha256=digest(raw), request_source_sha256=digest(request_raw),
                  original_progress_sha256=digest(original_raw), original_progress_records=len(original),
                  original_accepted_steps_available=len(expected), implementation_hashes=hashes,
                  optimized_construction=args.optimized_construction, full_requested_history=True))
        observer = Observer(args.output, emit, record['observations'][0]['native_seconds'])
        metrics = {}
        with ExitStack() as stack:
            if args.optimized_construction:
                stack.enter_context(exact_endpoint_cuts())
                stack.enter_context(shared_pressure_coefficients(metrics))
            stack.enter_context(reconstructed_pressure())
            stack.enter_context(observer.installed())
            state, history = requested_replay(record, request, emit)
        changed = [p for p, sha in hashes.items() if digest(Path(p).read_bytes()) != sha]
        path = args.output/'last-state.npy'
        with path.open('xb') as out: np.save(out, state)
        report = dict(schema='raftsim.observed_reconstructed_history.v1', source_sha256=digest(raw),
                      history=history, compared_original_accepted_steps=compared, construction_metrics=metrics,
                      changed_dependencies=changed, final_state_sha256=digest(path.read_bytes()),
                      native_or_physical_or_scene_accepted=False)
        with (args.output/'report.json').open('x', encoding='utf-8') as out:
            json.dump(report, out, indent=2, allow_nan=False)
        emit(dict(event='observation_terminal', completed=history['completed'], compared_original_steps=compared,
                  changed_dependencies=changed))
    if changed or not history['completed']:
        raise SystemExit(1)


if __name__ == '__main__': main()
