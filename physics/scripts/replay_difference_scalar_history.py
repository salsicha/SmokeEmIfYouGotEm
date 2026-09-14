"""Separate full requested history for the research scalar-gradient candidate.

Never replaces or resumes the original history. Same original start, boundaries,
endpoint, ownership moves, FV/RK/CFL/residual gates and pressure solve. Changes
only the ordinary scalar derivative; full completion still is not physical or
native/gameplay qualification. Retains diagnostic snapshots without extra steps.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from difference_scalar_gradient_reference import difference_scalar_gradients
from pressure_cut_endpoint_reference import exact_endpoint_cuts
from shared_pressure_construction_reference import shared_pressure_coefficients
from reconstructed_pressure_adapter import reconstructed_pressure
from replay_requested_reconstructed_owner import requested_replay
from observe_reconstructed_history import Observer


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--rate-audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    raw = args.input.read_bytes(); record = json.loads(raw)
    request_raw = Path(record['source_history']).read_bytes(); request = json.loads(request_raw)
    audit_raw = args.rate_audit.read_bytes(); audit = json.loads(audit_raw)
    assert audit['source']['sha256'] == digest(raw)
    assert audit['original_full_rate_bit_exact'] and audit['unchanged_mass_rate_and_cfl']
    for run in audit['runs']:
        assert all(p['iterations'] == 40 and p['relative_residual'] < 2e-5 for p in run['pressure']['pressure_stats'])
    for path, expected in audit['implementation_hashes'].items():
        assert digest(Path(path).read_bytes()) == expected, path
    hashes = {str(p): digest(p.read_bytes()) for p in Path(__file__).parent.glob('*.py')}
    args.output.mkdir()
    begin = time.perf_counter()
    with (args.output/'progress.jsonl').open('x') as progress:
        def emit(event):
            line = json.dumps(dict(event, wall_seconds=time.perf_counter()-begin), allow_nan=False)
            progress.write(line+'\n'); progress.flush(); print(line, flush=True)
        emit(dict(event='difference_scalar_provenance', source_sha256=digest(raw),
            request_sha256=digest(request_raw), rate_audit_sha256=digest(audit_raw),
            implementation_hashes=hashes, full_requested_history=True,
            original_runs_untouched=True, scene_accepted=False))
        observer = Observer(args.output, emit, record['observations'][0]['native_seconds'])
        with exact_endpoint_cuts(), shared_pressure_coefficients(), difference_scalar_gradients(), \
                reconstructed_pressure(), observer.installed():
            state, history = requested_replay(record, request, emit)
        changed = [path for path, expected in hashes.items() if digest(Path(path).read_bytes()) != expected]
        state_path = args.output/'last-state.npy'
        with state_path.open('xb') as stream: np.save(stream, state)
        report = dict(history=history, changed_dependencies=changed,
            state_sha256=digest(state_path.read_bytes()), physical_or_native_or_scene_accepted=False)
        with (args.output/'report.json').open('x') as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
        emit(dict(event='difference_scalar_terminal', completed=history['completed'], changed_dependencies=changed))
    if changed or not history['completed']: raise SystemExit(1)


if __name__ == '__main__':
    main()
