"""Compare the four original failed directions, without recomputing inputs.

The legacy context selects the retained block-Jacobi implementation only.
Both comparisons use exactly the same original geometry and old-stage rate
arrays, all original poles, and the existing forty-iteration solve budget.
This is not a native, time-integration, terrain, visual or FPS qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

from audit_reconstructed_closed_energy import fixture
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from reconstructed_energy_reference import metric
from smooth_rational_velocity_stage import make, stage
from rational_physical_momentum_rate import physical_rate


def array_hash(value):
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def run():
    rows = []
    current = ReconstructedAccelerationSystem.precondition

    def legacy(self, rhs, scheme='diagonal'):
        return current(self, rhs, 'block-jacobi' if scheme == 'block' else scheme)

    for seed in (2201, 2203, 2205, 2207):
        source, bed = fixture(seed, 'smooth', 128)
        h = source[..., 0]
        u = source[..., 1:]/h[..., None]
        g = make(h, bed, .125)
        k, _ = metric(g, rational=True)
        root = np.sqrt(h)[..., None]
        v = (k @ (root*u).ravel()).reshape(u.shape)/root
        with patch.object(ReconstructedAccelerationSystem, 'precondition', legacy):
            direction = stage(g, v)
            args = g, v, direction['depth_rate'], direction['canonical_velocity_rate']
            original = physical_rate(*args)
        arrays = [source, bed, v, args[2], args[3]]
        before = list(map(array_hash, arrays))
        candidate = physical_rate(*args)
        if list(map(array_hash, arrays)) != before:
            raise ValueError('Original source or direction mutated')
        record = dict(seed=seed, shape=list(h.shape), input_sha256=before, results=[])
        for name, result in (('block-jacobi', original), ('block-symmetric', candidate)):
            gate = 1e-10*max(1., abs(result['physical_energy_rate']), abs(result['canonical_energy_rate']))
            record['results'].append(dict(preconditioner=name,
                energy_coordinate_error=result['energy_coordinate_error'], gate=gate,
                passed=result['energy_coordinate_error'] <= gate,
                poles=result['poles'], primal_pressure_residuals=result['primal_pressure_residuals']))
        rows.append(record)
    scripts = Path(__file__).parent
    sources = {name: hashlib.sha256((scripts/name).read_bytes()).hexdigest() for name in (
        'audit_pressure_block_sweeps.py', 'symmetric_pressure_preconditioner.py',
        'reconstructed_acceleration_system.py', 'pressure_cg_range_reference.py',
        'rational_physical_momentum_rate.py', 'rational_dual_energy_reference.py',
        'smooth_rational_velocity_stage.py', 'audit_reconstructed_closed_energy.py')}
    return dict(schema='raftsim.pressure_block_sweeps.v1', rows=rows, source_sha256=sources,
        same_source_and_frozen_original_directions=True,
        passed=all(not r['results'][0]['passed'] and r['results'][1]['passed'] for r in rows),
        native_or_full_physics_or_gameplay_accepted=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('Preserve the previous report')
    result = run()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x') as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write('\n')
    print(json.dumps(dict(passed=result['passed'], report=str(args.report))))
    raise SystemExit(0 if result['passed'] else 1)
