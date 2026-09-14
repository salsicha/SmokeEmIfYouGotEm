"""Diagnose actual nonlinear RHS convergence without replacing any solver.

Capture the unchanged research 40-iteration solve. Compare the same factored
matrix/RHS with independent SciPy CG at 40 iterations and sparse direct solve.
The direct solve is diagnostic truth for this matrix, not an allowed runtime
replacement, physical-model truth, evolved history or cost acceptance.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import scipy
from scipy import sparse
from scipy.sparse import linalg
import total_depth_bank_replay as bank
import reconstructed_nonlinear_pressure as nonlinear
from reconstructed_pressure_adapter import reconstructed_pressure
from audit_total_depth_dispersion import solitary


def assembled_matrix(system):
    shape = (system.h.size, 2*system.h.size)
    w = sparse.coo_matrix((system.w_coefficients, (system.rows, system.columns)), shape=shape).tocsr()
    v = sparse.coo_matrix((system.v_coefficients, (system.rows, system.columns)), shape=shape).tocsr()
    fraction = sparse.diags(system.fraction.ravel())
    return (sparse.eye(shape[1], format='csr')
        +system.length*(w.T@fraction@w+.75*v.T@fraction@v)).tocsr()


@contextmanager
def capture_systems(records):
    original = nonlinear.ReconstructedAccelerationSystem
    class Captured(original):
        def solve(self, rhs, iterations=40, *, preconditioner='diagonal'):
            value, stats = super().solve(rhs, iterations, preconditioner=preconditioner)
            records.append((self, rhs.copy(), value.copy(), dict(stats), preconditioner))
            return value, stats
    nonlinear.ReconstructedAccelerationSystem = Captured
    try: yield
    finally: nonlinear.ReconstructedAccelerationSystem = original


def diagnose(system, rhs, actual, stats, scheme):
    matrix = assembled_matrix(system); n = rhs.size; shape = rhs.shape
    rng = np.random.default_rng(510)
    probe = rng.normal(size=shape)
    original_action = system.apply(probe)
    assembly_error = float(np.linalg.norm((matrix@probe.ravel()).reshape(shape)-original_action)
        /np.linalg.norm(original_action))
    if assembly_error > 1e-12: raise ValueError('Assembled matrix does not match original action')
    original_preconditioner = lambda v: system.precondition(v.reshape(shape), scheme).ravel()
    operator = linalg.LinearOperator((n, n), matvec=lambda v: system.apply(v.reshape(shape)).ravel())
    preconditioner = linalg.LinearOperator((n, n), matvec=original_preconditioner)
    callbacks = []
    begin = time.perf_counter()
    independent, info = linalg.cg(operator, rhs.ravel(), M=preconditioner,
        rtol=0., atol=0., maxiter=40, callback=lambda x: callbacks.append(1))
    cg_seconds = time.perf_counter()-begin
    begin = time.perf_counter(); exact = linalg.spsolve(matrix, rhs.ravel())
    direct_seconds = time.perf_counter()-begin
    scale = np.linalg.norm(rhs.ravel())
    def residual(value):
        return float(np.linalg.norm(system.apply(value.reshape(shape)).ravel()-rhs.ravel())/scale)
    # Symmetrically scaled Jacobi spectrum. A same-cell block is identical to
    # Jacobi for this 1D flat-bed source; never silently assume that in 2D.
    if np.any(system.off_diagonal != 0):
        raise ValueError('This spectrum diagnostic requires block=Jacobi for the actual source')
    d = sparse.diags(1/np.sqrt(matrix.diagonal()))
    scaled = d@matrix@d
    smallest = float(linalg.eigsh(scaled, k=1, which='SA', return_eigenvectors=False,
        tol=1e-8, v0=np.ones(n))[0])
    largest = float(linalg.eigsh(scaled, k=1, which='LA', return_eigenvectors=False,
        tol=1e-8, v0=np.linspace(1, 2, n))[0])
    return dict(length=system.length, unknowns=n, matrix_nonzeros=matrix.nnz,
        original_stats=stats, preconditioner=scheme, assembly_relative_action_error=assembly_error,
        scipy_cg_iterations=len(callbacks), scipy_cg_info=int(info),
        scipy_cg_relative_residual=residual(independent), direct_relative_residual=residual(exact),
        original_relative_solution_error=float(np.linalg.norm(actual.ravel()-exact)/np.linalg.norm(exact)),
        scipy_relative_solution_error=float(np.linalg.norm(independent-exact)/np.linalg.norm(exact)),
        relative_difference_between_40_iteration_solutions=float(np.linalg.norm(actual.ravel()-independent)/np.linalg.norm(exact)),
        scaled_smallest_eigenvalue=smallest, scaled_largest_eigenvalue=largest,
        scaled_condition_number=largest/smallest,
        scipy_cg_seconds=cg_seconds, direct_seconds=direct_seconds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    names = ('diagnose_reconstructed_pressure_convergence.py', 'audit_total_depth_dispersion.py',
        'reconstructed_pressure_adapter.py', 'reconstructed_nonlinear_pressure.py',
        'reconstructed_acceleration_system.py', 'directional_pressure_geometry.py',
        'reconstructed_pressure_geometry.py', 'reconstructed_pressure_rates.py',
        'pressure_cut_face_reference.py', 'total_depth_bank_replay.py',
        'adaptive_hydrostatic_precision.py', 'continuous_shoreline_reconstruction.py',
        'total_depth_nonlinear_pressure.py', 'pressure_cg_range_reference.py',
        'finite_depth_pressure_reference.py', 'detail_nonlinear_flux.py', 'total_depth_pressure.py',
        'breaking_front_reference.py')
    paths = [Path(__file__).with_name(name) for name in names]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    dx = .125; x = (np.arange(round(96/dx))+.5)*dx
    initial, _ = solitary(x, 0.); original = initial.copy(); initial.flags.writeable = False
    records = []
    with capture_systems(records), reconstructed_pressure():
        bank.rate(initial[None], np.zeros((1, len(x))), dx, second_order=True, periodic=True,
            dispersive=True, pressure_model='rational_sgn', pressure_interpolation='depth_weighted',
            pressure_formulation='kinematic', pressure_bed_slope='geometry', shoreline_limiter='unscaled')
    if not np.array_equal(initial, original): raise AssertionError('Input changed')
    results = []
    for record in records:
        result = diagnose(*record); results.append(result)
        print(json.dumps(result, allow_nan=False), flush=True)
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != h for p, h in hashes.items()):
        raise RuntimeError('Implementation changed during diagnosis')
    report = dict(schema='raftsim.reconstructed_pressure_convergence.v1', scope=__doc__,
        numpy_version=np.__version__, scipy_version=scipy.__version__, implementation_hashes=hashes,
        source_state_sha256=hashlib.sha256(initial.tobytes()).hexdigest(),
        original_solver_qualified=False, scene_accepted=False, poles=results)
    encoded = json.dumps(report, indent=2, allow_nan=False)
    with args.report.open('x') as output: output.write(encoded)


if __name__ == '__main__': main()
