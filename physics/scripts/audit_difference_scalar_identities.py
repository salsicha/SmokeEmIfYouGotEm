"""Independent face-matrix identities and analytic boundary consistency checks.

Explains changed scalar/pressure identities; does not qualify a wave solver.
No existing solver, source, tolerance, or running replay is changed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate, kinematic_forcing
from difference_scalar_gradient_reference import difference_gradient, difference_scalar_gradients


def make(h, bed, periodic, exterior=None):
    return ReconstructedPressureGeometry(h, bed, .5, periodic=periodic,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom', exterior_bed=exterior)


def face_matrices(g):
    """Assemble cell/face contributions by explicit indices, not vector actions."""
    n = g.h.size
    d = np.zeros((n, 2*n)); e = np.zeros_like(d)
    indices = np.arange(n).reshape(g.h.shape)
    for component, axis in enumerate((1, 0)):
        edge = g.edges[component]
        for point in np.ndindex(g.h.shape):
            neighbor = list(point); neighbor[axis] = (neighbor[axis]+1) % g.h.shape[axis]
            i, j = int(indices[point]), int(indices[tuple(neighbor)])
            a, b, own, other, k, local, slope = (float(edge[name][point]) for name in
                ('aa', 'ab', 'own', 'other', 'shared_b', 'local_p', 'physical_b'))
            vi, vj = 2*i+component, 2*j+component
            d[i, vi] += a*own/g.dx; d[i, vj] += a*other/g.dx
            d[j, vi] -= b*own/g.dx; d[j, vj] -= b*other/g.dx
            d[i, vi] -= local/g.dx
            e[i, vi] += slope-k/g.dx; e[i, vj] += k/g.dx
            e[j, vj] -= k/g.dx; e[j, vi] += k/g.dx
    pressure = -d.T
    sigma = pressure.sum(axis=1)
    scalar = pressure.copy()
    for row in range(2*n):
        scalar[row, row//2] -= sigma[row]
    return d, e, pressure, scalar, sigma


def boundary_lift(trace, shape, dx):
    """Independent face indexing of affine divergence value/time rate."""
    ny, nx = shape
    result = np.zeros((*shape, 2))
    for y in range(ny):
        result[y, 0] -= trace[y]/dx
        result[y, nx-1] += trace[ny+y]/dx
    for x in range(nx):
        result[0, x] -= trace[2*ny+x]/dx
        result[ny-1, x] += trace[2*ny+nx+x]/dx
    return result


def identity_case(periodic):
    rng = np.random.default_rng(404 if periodic else 924)
    h = rng.uniform(.5, 2., (4, 5)); bed = rng.uniform(0., 1., h.shape)
    ht = rng.normal(size=h.shape)*.03
    u = rng.normal(size=(*h.shape, 2))*.1; ut = rng.normal(size=u.shape)*.02
    trace = None if periodic else rng.normal(size=(2*sum(h.shape), 2))*.1
    exterior = None if periodic else rng.uniform(0, 1, 2*sum(h.shape))
    g = make(h, bed, periodic, exterior)
    d, e, pressure, scalar, sigma = face_matrices(g)
    v, vt = u.ravel(), ut.ravel()
    sample = rng.normal(size=h.shape)
    scalar_error = float(abs(scalar@sample.ravel()-difference_gradient(g, sample).ravel()).max())
    ds, es = g.kinematic_components(u)
    matrix_error = max(float(abs(d@v-ds.ravel()).max()), float(abs(e@v-es.ravel()).max()))
    p, b = rng.normal(size=h.size), rng.normal(size=h.size)
    traction_error = float(abs(pressure@p+e.T@b-g.gradient_traction(p.reshape(h.shape), b.reshape(h.shape)).ravel()).max())
    force_work = float(v@(pressure@p+e.T@b)+p@(d@v)-b@(e@v))
    ordinary_work = float(v@(scalar@sample.ravel())+sample.ravel()@(d@v))
    expected_work = float(-np.sum(sample.ravel()*np.sum((v*sigma).reshape(-1, 2), axis=1)))
    tangent = PressureGeometryRate(g, bed, ht)
    with difference_scalar_gradients():
        q, c, adv = kinematic_forcing(g, tangent, u, boundary_velocity=trace)
    lift = np.zeros((*h.shape, 2)) if trace is None else boundary_lift(trace, h.shape, g.dx)
    div, bottom = d@v+lift[..., 0].ravel(), e@v
    errors = []
    for eps in (1e-3, 1e-4):
        states = []
        for sign in (-1, 1):
            gg = make(h+sign*eps*ht, bed, periodic, exterior)
            dd, ee, *_ = face_matrices(gg)
            ll = lift[..., 0]+sign*eps*lift[..., 1]
            states.append((dd@(v+sign*eps*vt)+ll.ravel(), ee@(v+sign*eps*vt)))
        dt = (states[1][0]-states[0][0])/(2*eps)
        et = (states[1][1]-states[0][1])/(2*eps)
        transport_d = np.sum((v*(scalar@div)).reshape(-1, 2), axis=1)
        transport_e = np.sum((v*(scalar@bottom)).reshape(-1, 2), axis=1)
        expected_q, expected_c = div*div-dt-transport_d, et+transport_e
        actual_q = q.ravel()-d@(vt+adv.ravel())
        actual_c = c.ravel()+e@(vt+adv.ravel())
        errors.append(max(float(abs(actual_q-expected_q).max()), float(abs(actual_c-expected_c).max())))
    return dict(periodic=periodic, explicit_matrix_kinematic_error=matrix_error,
        pressure_traction_error=traction_error, scalar_matrix_error=scalar_error,
        original_pressure_work_residual=force_work, ordinary_scalar_work_residual=ordinary_work,
        predicted_scalar_work_residual=expected_work, scalar_work_identity_error=abs(ordinary_work-expected_work),
        material_time_identity_errors=errors, changed_scalar_adjoint_is_not_zero=abs(ordinary_work)>1e-6)


def affine_boundary_case(n):
    dx = 1./n
    x = (np.arange(n)+.5)*dx
    h = np.ones((1, n)); bed = np.zeros_like(h)
    g = ReconstructedPressureGeometry(h, bed, dx, periodic=False,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')
    # Independent analytic reference: d(x)/dx=1 at EVERY cell, including edges.
    actual = difference_gradient(g, x[None])[0, :, 0]
    error = abs(actual-1.)
    return dict(n=n, dx=dx, endpoint_derivatives=actual[[0, -1]].tolist(),
        endpoint_max_error=float(error[[0, -1]].max()), interior_max_error=float(error[1:-1].max()),
        constant_gradient_exactly_zero=bool(np.all(difference_gradient(g, h)==0)),
        affine_boundary_consistent=bool(np.all(error < 1e-12)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    cases = [identity_case(True), identity_case(False)]
    boundary = [affine_boundary_case(n) for n in (8, 16, 32, 64)]
    result = dict(identity_cases=cases, affine_boundary_cases=boundary,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        candidate_boundary_qualified=all(c['affine_boundary_consistent'] for c in boundary),
        solver_modified=False, full_history_or_gameplay_accepted=False,
        limitation='Algebraically accounts for changed identities without changing old tests. '
        'Face matrices independently assemble existing coefficients, not new continuum physics. '
        'Analytic affine derivative is a separate necessary boundary-consistency check. '
        'No mechanical-energy closure, wet-front consistency or full-history acceptance follows.')
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
