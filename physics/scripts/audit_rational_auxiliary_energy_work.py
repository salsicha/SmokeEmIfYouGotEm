"""Original physical profiles: local work decomposition, no repaired dynamics."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from audit_reconstructed_closed_energy import fixture
from conservative_rational_stress import stress_stage_physical
from rational_auxiliary_energy_work import local_work, stationary_density
from rational_primal_energy import evaluate
from smooth_rational_velocity_stage import make


def run(seed, n):
    source, bed = fixture(seed, 'smooth', n)
    before = [a.copy() for a in (source, bed)]
    h, p, dx = source[..., 0], source[..., 1:], 16/n
    g = make(h, bed, dx)
    stage = stress_stage_physical(g, p)
    ht, pt = stage['depth_rate'], stage['physical_momentum_rate']
    work = local_work(g, p, ht, pt)
    probes = []
    for eps in (1e-4, 1e-5, 1e-6):
        densities = []
        for sign in (-1, 1):
            moved = make(h+sign*eps*ht, bed, dx)
            moved_p = p+sign*eps*pt
            densities.append(stationary_density(moved, moved_p, evaluate(moved, moved_p)))
        rate = (densities[1]-densities[0])/(2*eps)
        probes.append(dict(epsilon=eps,
            maximum_local_density_rate_error=float(abs(rate-work['local_energy_rate']).max())))
    if not all(np.array_equal(a, b) for a, b in zip((source, bed), before)):
        raise RuntimeError('Audit changed the original physical state')
    maxima = {key:float(abs(work[key]).max()) for key in
              ('local_energy_rate','explicit_local_work','auxiliary_exchange','stationarity_residual_work')}
    return dict(seed=seed, resolution=n,
        source_state_sha256=hashlib.sha256(source.tobytes()).hexdigest(),
        bed_sha256=hashlib.sha256(bed.tobytes()).hexdigest(),
        probes=probes, maximum_absolute_local_terms=maxima,
        **{key:work[key] for key in ('local_balance_error','integrated_auxiliary_exchange',
            'integrated_stationarity_residual_work','integrated_energy_rate',
            'integrated_coordinate_work','coordinate_work_error','poles')},
        original_stress_energy_rate=stage['energy_rate'],
        original_stress_energy_rate_recovery_error=abs(work['integrated_energy_rate']-stage['energy_rate']),
        local_balance_gate_passed=work['local_balance_error']<1e-10,
        local_density_derivative_gate_passed=probes[-1]['maximum_local_density_rate_error']<1e-7,
        energy_conservation_gate_passed=abs(work['integrated_energy_rate'])<1e-10,
        energy_conservation_or_gameplay_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    scripts = Path(__file__).resolve().parent
    files = sorted({Path(m.__file__).resolve() for m in tuple(sys.modules.values())
                    if getattr(m, '__file__', None) and Path(m.__file__).resolve().parent == scripts})
    hashes = lambda:{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    initial = hashes()
    records = []
    for n in (64,128):
        for seed in (2200,2202,2204,2206):
            record = run(seed, n)
            records.append(record)
            print(json.dumps(record), flush=True)
    if hashes() != initial:
        raise RuntimeError('Implementation changed during audit')
    with args.report.open('x') as stream:
        json.dump(dict(scope=__doc__, records=records, implementation_hashes=initial),
                  stream, indent=2, allow_nan=False)


if __name__ == '__main__':
    main()
