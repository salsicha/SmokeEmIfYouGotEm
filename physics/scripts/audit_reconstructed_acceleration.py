"""Manufactured linear-system audit on original captured pressure geometry.

Use the recorded velocity solely as a known physical TEST vector x. Construct
rhs=A*sqrt(h)*x, then recover x with the unchanged 40-iteration solver. This
exercises the actual-sized matrix, NOT the nonlinear physical pressure RHS.
"""
import time
import numpy as np
from finite_depth_pressure_reference import LENGTHS
from reconstructed_acceleration_system import ReconstructedAccelerationSystem


def inspect_system(geometry, fraction, test_velocity):
    u = np.asarray(test_velocity, dtype=float)
    if u.shape != (*geometry.h.shape, 2) or not np.isfinite(u).all() or np.any(u[geometry.h == 0] != 0):
        raise ValueError('Invalid physical test vector')
    root = np.sqrt(geometry.h)
    known = root[..., None]*u
    rows = []
    for length in LENGTHS:
        begin = time.perf_counter()
        system = ReconstructedAccelerationSystem(geometry, float(length), dispersion_fraction=fraction)
        build = time.perf_counter()-begin
        rhs = system.apply(known)
        solves = []
        for scheme in ('diagonal', 'block'):
            begin = time.perf_counter()
            result, stats = system.solve(rhs, preconditioner=scheme)
            elapsed = time.perf_counter()-begin
            error = result-known
            physical_error = np.divide(error, root[..., None], out=np.zeros_like(error), where=root[..., None] > 0)
            if not np.isfinite(physical_error).all(): raise ValueError('Recovered test-vector error exceeds range')
            solves.append(dict(preconditioner=scheme, seconds=elapsed, **stats,
                maximum_normalized_error=float(abs(error).max()),
                maximum_recovered_test_vector_error=float(abs(physical_error).max()),
                dry_unknown_maximum=float(abs(result[geometry.h == 0]).max()) if np.any(geometry.h == 0) else 0.))
        rows.append(dict(length=float(length), build_seconds=build,
            scalar_rows=geometry.h.size, vector_unknowns=2*geometry.h.size,
            stored_coefficients=len(system.rows), maximum_W_coefficient=float(abs(system.w_coefficients).max(initial=0)),
            maximum_V_coefficient=float(abs(system.v_coefficients).max(initial=0)),
            diagonal_minimum=float(system.diagonal.min()), diagonal_maximum=float(system.diagonal.max()), solves=solves))
    return dict(scope=__doc__, poles=rows,
        qualification='Manufactured linear RHS only. No nonlinear pressure solution, trajectory, boundary or performance acceptance.')
