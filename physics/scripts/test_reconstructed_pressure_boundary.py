import numpy as np
import pytest
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate, kinematic_forcing
from reconstructed_nonlinear_pressure import nonlinear_pressure
from test_prescribed_pressure_boundary import traces


def make(h, bed, periodic=False, exterior_bed=None):
    return ReconstructedPressureGeometry(h, bed, .5, periodic=periodic,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom', exterior_bed=exterior_bed)


@pytest.mark.parametrize('shape', [(3, 5), (1, 5), (5, 1), (1, 1)])
@pytest.mark.parametrize('velocity', [(1., 0.), (0., -1.)])
def test_prescribed_uniform_throughflow_has_zero_reconstructed_pressure(shape, velocity):
    h = np.ones(shape); zero = np.zeros_like(h); u = np.broadcast_to(velocity, (*shape, 2)).copy()
    force, report = nonlinear_pressure(make(h, zero), u, zero, u*0,
                                        boundary_velocity=traces(shape, velocity))
    np.testing.assert_array_equal(force, 0)
    assert all(p['relative_residual'] == 0 for p in report['poles'])


def test_uniform_acceleration_requires_prescribed_trace_time_rate():
    h = np.ones((3, 5)); z = h*0
    u = np.broadcast_to((.75, -.25), (*h.shape, 2)).copy()
    acceleration = np.array([.125, -.375]); mt = h[..., None]*acceleration
    g = make(h, z)
    force, _ = nonlinear_pressure(g, u, z, mt, boundary_velocity=traces(h.shape, (.75, -.25), acceleration))
    np.testing.assert_allclose(force, 0, atol=2e-15)
    wrong, _ = nonlinear_pressure(g, u, z, mt, boundary_velocity=traces(h.shape, (.75, -.25)))
    assert abs(wrong).max() > .01


def test_affine_work_and_time_identity_on_original_variable_bed_geometry():
    rng = np.random.default_rng(924)
    h = rng.uniform(.5, 2, (4, 5)); z = rng.uniform(0, 1, h.shape)
    ht = rng.normal(size=h.shape)*.03
    u = rng.normal(size=(*h.shape, 2))*.1; ut = rng.normal(size=u.shape)*.02
    trace = rng.normal(size=(2*sum(h.shape), 2))*.1; original = trace.copy()
    trace.flags.writeable = False
    exterior = rng.uniform(0, 1, 2*sum(h.shape))
    g = make(h, z, exterior_bed=exterior)
    rate = PressureGeometryRate(g, z, ht)
    q, c, adv = kinematic_forcing(g, rate, u, boundary_velocity=trace)
    d, e = g.kinematic_components(u); d += g.prescribed_divergence_lift(trace)[..., 0]
    p, b = rng.normal(size=h.shape), rng.normal(size=h.shape)
    work = np.sum(u*g.gradient_traction(p, b))+np.sum(p*d)-np.sum(b*e)
    np.testing.assert_allclose(work, np.sum(p*g.prescribed_divergence_lift(trace)[..., 0]), atol=2e-15)
    eps = 1e-4
    def full(sign):
        gg = make(h+sign*eps*ht, z, exterior_bed=exterior)
        tt = trace.copy(); tt[:, 0] += sign*eps*trace[:, 1]
        dd, ee = gg.kinematic_components(u+sign*eps*ut)
        return dd+gg.prescribed_divergence_lift(tt)[..., 0], ee
    dp, ep = full(1); dm, em = full(-1)
    grad = lambda scalar: g.gradient_traction(scalar, h*0)
    da, ea = g.kinematic_components(ut+adv)
    np.testing.assert_allclose(q-da, d*d-(dp-dm)/(2*eps)-np.sum(u*grad(d), axis=-1), atol=2e-11)
    np.testing.assert_allclose(c+ea, (ep-em)/(2*eps)+np.sum(u*grad(e), axis=-1), atol=2e-11)
    np.testing.assert_array_equal(trace, original)


@pytest.mark.parametrize('failure', ['count', 'nonfinite_value', 'nonfinite_rate', 'periodic'])
def test_invalid_prescribed_boundary_is_not_dropped(failure):
    h = np.ones((2, 3)); trace = traces(h.shape, (1., 0.))
    if failure == 'count': trace = trace[:-1]
    if failure == 'nonfinite_value': trace[0, 0] = np.nan
    if failure == 'nonfinite_rate': trace[0, 1] = np.inf
    g = make(h, h*0, periodic=failure == 'periodic')
    with pytest.raises(ValueError): g.prescribed_divergence_lift(trace)


def test_missing_trace_is_not_mislabeled_throughflow():
    h = np.ones((3, 5)); u = np.zeros((*h.shape, 2)); u[..., 0] = 1
    force, _ = nonlinear_pressure(make(h, h*0), u, h*0, u*0)
    assert abs(force).max() > .1
