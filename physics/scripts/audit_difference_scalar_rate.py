"""Compare original/candidate full captured rates; no evolution or promotion."""
import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import total_depth_bank_replay as bank
from audit_reconstructed_polynomial_sweep import source_fields
from reconstructed_pressure_adapter import reconstructed_pressure
from pressure_cut_endpoint_reference import exact_endpoint_cuts
from shared_pressure_construction_reference import shared_pressure_coefficients
from difference_scalar_gradient_reference import difference_scalar_gradients


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    arrays_path = args.report.with_suffix('.npz')
    assert not args.report.exists() and not arrays_path.exists()
    hashes = {str(p): sha(p.read_bytes()) for p in Path(__file__).parent.glob('*.py')}
    state, bed, dx, kwargs, metadata = source_fields('captured', args.input)
    with np.load(args.snapshot, allow_pickle=False) as archive:
        assert state.tobytes() == archive['state'].tobytes() and bed.tobytes() == archive['bed'].tobytes()
        original_rate = archive['rate'].copy()
    state.flags.writeable = bed.flags.writeable = False
    runs, values = [], []
    for name, scope in [('original', nullcontext), ('difference_scalar', difference_scalar_gradients)]:
        stages = []
        begin = time.perf_counter()
        with exact_endpoint_cuts(), shared_pressure_coefficients(), scope(), reconstructed_pressure(stages.append):
            rate, cfl = bank.rate(state, bed, dx, second_order=True, **kwargs, dispersive=True,
                pressure_model='rational_sgn', pressure_interpolation='depth_weighted',
                pressure_formulation='kinematic', pressure_bed_slope='geometry', shoreline_limiter='unscaled')
        assert np.isfinite(rate).all() and len(stages) == 1
        runs.append(dict(name=name, seconds=time.perf_counter()-begin, cfl_s=cfl,
            full_rate_sha256=sha(rate.tobytes()), pressure=stages[0]))
        values.append(rate)
        if name == 'original':
            assert rate.tobytes() == original_rate.tobytes(), 'Original full rate differs from retained original-start trial'
        print(json.dumps(dict(event='full_rate_completed', **runs[-1])), flush=True)
    assert values[0][..., 0].tobytes() == values[1][..., 0].tobytes()
    assert runs[0]['cfl_s'] == runs[1]['cfl_s']
    delta = values[1][..., 1:3]-values[0][..., 1:3]
    index = np.unravel_index(np.argmax(np.linalg.norm(delta, axis=-1)), state.shape[:-1])
    for path, expected in hashes.items():
        assert sha(Path(path).read_bytes()) == expected, path
    with arrays_path.open('xb') as stream:
        np.savez(stream, original_rate=values[0], candidate_rate=values[1], state=state, bed=bed)
    report = dict(source=metadata, snapshot_sha256=sha(args.snapshot.read_bytes()),
        implementation_hashes=hashes, original_full_rate_bit_exact=True,
        unchanged_mass_rate_and_cfl=True, runs=runs,
        maximum_momentum_rate_change=float(abs(delta).max()),
        largest_change_cell=dict(yx=list(map(int,index)), depth_m=float(state[index][0]),
            original=values[0][index].tolist(), candidate=values[1][index].tolist()),
        arrays_sha256=sha(arrays_path.read_bytes()),
        evolved_history_completed=False, physical_or_native_or_scene_accepted=False)
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps({k:v for k,v in report.items() if k != 'implementation_hashes'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
