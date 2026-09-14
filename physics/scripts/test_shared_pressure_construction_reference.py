import numpy as np
import pytest
from reconstructed_acceleration_system import ReconstructedAccelerationSystem as Original
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
import reconstructed_nonlinear_pressure as nonlinear
from shared_pressure_construction_reference import shared_pressure_coefficients


def geometry(h, bed=None, periodic=True):
    return ReconstructedPressureGeometry(h, np.zeros_like(h) if bed is None else bed, .5,
        periodic=periodic, pressure_trace='integrated_column', bed_quadrature='shared_bottom')


def exact(actual, expected):
    for name in ('rows', 'columns', 'w_coefficients', 'v_coefficients', 'fraction', 'diagonal', 'off_diagonal'):
        a, b = getattr(actual, name), getattr(expected, name)
        assert a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes(), name
        assert not a.flags.writeable


@pytest.mark.parametrize('shape', [(1, 1), (1, 2), (2, 2), (3, 4)])
@pytest.mark.parametrize('periodic', [True, False])
def test_reuse_keeps_coefficient_and_preconditioner_order(shape, periodic):
    rng = np.random.default_rng(515)
    g = geometry(rng.uniform(.3, 2, shape), rng.uniform(0, .5, shape), periodic)
    rhs = rng.normal(size=(*shape, 2))
    with shared_pressure_coefficients() as counters:
        for i, length in enumerate((.4052787713439809, .03916567310046354, 1/3)):
            fraction = rng.uniform(0, 1, shape); fraction.flat[0] = 0
            expected = Original(g, length, dispersion_fraction=fraction)
            actual = nonlinear.ReconstructedAccelerationSystem(g, length, dispersion_fraction=fraction)
            assert actual.construction_reused == (i != 0)
            exact(actual, expected)
            assert actual.apply(rhs).tobytes() == expected.apply(rhs).tobytes()
            a, sa = actual.solve(rhs, preconditioner='block')
            b, sb = expected.solve(rhs, preconditioner='block')
            assert a.tobytes() == b.tobytes() and sa == sb
        assert counters == dict(builds=1, reuses=2, uncacheable_builds=0)


@pytest.mark.parametrize('depth', [1e-200, 1e-300, 2.**-1070, 1.])
@pytest.mark.parametrize('project', [False, True])
def test_dry_rows_and_positive_films_have_no_threshold(depth, project):
    h = np.full((1, 4), depth) if depth != 1. else np.array([[1., 0., 0., 2.]])
    g = geometry(h)
    with shared_pressure_coefficients():
        nonlinear.ReconstructedAccelerationSystem(g, .4, project_zero_mass_rows=project)
        actual = nonlinear.ReconstructedAccelerationSystem(g, .03, project_zero_mass_rows=project)
        assert actual.construction_reused
        exact(actual, Original(g, .03, project_zero_mass_rows=project))


def test_geometry_identity_bits_projection_and_mutability_invalidate_reuse():
    g = geometry(np.ones((2, 3)))
    with shared_pressure_coefficients() as counts:
        nonlinear.ReconstructedAccelerationSystem(g, .4)
        copy = geometry(g.h)
        assert not nonlinear.ReconstructedAccelerationSystem(copy, .03).construction_reused
        # A caller can replace an array despite its old read-only flag. Check
        # current bits, never just geometry identity or cached flags.
        value = copy.edges[0]['aa'].copy(); value[0, 0] += .125; value.flags.writeable = False
        copy.edges[0]['aa'] = value
        actual = nonlinear.ReconstructedAccelerationSystem(copy, .04)
        assert not actual.construction_reused
        exact(actual, Original(copy, .04))
        assert not nonlinear.ReconstructedAccelerationSystem(copy, .05, project_zero_mass_rows=True).construction_reused
        copy.edges[0]['aa'] = value.copy()
        assert not nonlinear.ReconstructedAccelerationSystem(copy, .06, project_zero_mass_rows=True).construction_reused
        assert counts == dict(builds=5, reuses=0, uncacheable_builds=1)


@pytest.mark.parametrize('kwargs', [dict(length=0), dict(length=np.nan), dict(length=-1),
    dict(project_zero_mass_rows=1), dict(dispersion_fraction=np.ones((1, 2))),
    dict(dispersion_fraction=np.full((2, 3), np.nan)), dict(dispersion_fraction=np.full((2, 3), -1)),
    dict(dispersion_fraction=np.full((2, 3), 2))])
def test_validation_not_skipped_on_cache_hit(kwargs):
    g = geometry(np.ones((2, 3))); args = dict(length=.03, **kwargs) if 'length' not in kwargs else kwargs
    with shared_pressure_coefficients():
        nonlinear.ReconstructedAccelerationSystem(g, .4)
        with pytest.raises(ValueError) as a: Original(g, **args)
        with pytest.raises(ValueError) as b: nonlinear.ReconstructedAccelerationSystem(g, **args)
        assert str(a.value) == str(b.value)


def test_context_restores_after_error_and_nested_scope():
    before = nonlinear.ReconstructedAccelerationSystem
    with pytest.raises(RuntimeError):
        with shared_pressure_coefficients():
            outer = nonlinear.ReconstructedAccelerationSystem
            with shared_pressure_coefficients():
                assert nonlinear.ReconstructedAccelerationSystem is not outer
            assert nonlinear.ReconstructedAccelerationSystem is outer
            raise RuntimeError('test cleanup')
    assert nonlinear.ReconstructedAccelerationSystem is before


def test_caller_mutation_of_cached_coefficients_forces_reconstruction():
    g = geometry(np.ones((2, 3)))
    with shared_pressure_coefficients() as counts:
        first = nonlinear.ReconstructedAccelerationSystem(g, .4)
        first.w_coefficients.flags.writeable = True
        first.w_coefficients[0] += .125
        first.w_coefficients.flags.writeable = False
        second = nonlinear.ReconstructedAccelerationSystem(g, .03)
        assert not second.construction_reused
        exact(second, Original(g, .03))
        assert counts['builds'] == 2 and counts['reuses'] == 0
