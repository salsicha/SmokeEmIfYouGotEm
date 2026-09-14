import numpy as np
import pytest

from triangle_cell_storage import TriangleCellStorage
from subcell_mechanical_energy import squared_depth_integral
from subcell_pressure_kinetic_geometry import quadrature, local_form, energy


def cell(levels):
    return TriangleCellStorage(np.array([[[0., 0., levels[0]], [1., 0., levels[1]], [0., 1., levels[2]]]]))


@pytest.mark.parametrize('levels', ([0., 0., 0.], [0., 0., 2.], [0., 2., 2.], [0., 1., 2.]))
def test_moments_match_independent_storage_and_polynomials(levels):
    storage = cell(levels)
    for height in (.001, .1, .7, 1., 1.4, 2., 2.7):
        weights, h, _ = quadrature(storage, height)
        moments = np.array([np.sum(weights*h**k) for k in range(4)])
        v, wet = storage.relative_volume_and_wet_area(height)
        np.testing.assert_allclose(moments[:3], [wet, v, squared_depth_integral(storage, height, True)],
                                   atol=2e-14, rtol=2e-13)
        a, b, c = levels
        if height >= c:
            ha, hb, hc = height-np.array(levels)
            expected = .05*sum(ha**i*hb**j*hc**(3-i-j) for i in range(4) for j in range(4-i))
        elif height <= b:
            expected = .05*height**3*(height/(b-a))*(height/(c-a))
        else:
            t, l, r, span = height-b, b-a, c-b, c-a
            expected = .5*(l**4/10+l**3*t/2+l*l*t*t+l*t**3+t**4*(.5-t/(10*r)))/span
        np.testing.assert_allclose(moments[3], expected, atol=2e-14, rtol=2e-13)


@pytest.mark.parametrize('height', (.1, .7, 1.3, 1.8, 2.7))
def test_volume_tangent_of_exact_positive_kinetic_form(height):
    storage = cell([0., 1., 2.])
    volume = storage.relative_volume_and_wet_area(height)[0]
    form = local_form(storage, volume)
    jet = np.array([.7, -.3, .4])
    value, derivative = energy(form, jet)
    assert value >= 0.
    np.testing.assert_allclose(form['gram'], form['factor'].T@form['factor'], atol=0)
    errors = []
    for fraction in (1e-3, 5e-4, 2.5e-4):
        step = fraction*volume
        low = energy(local_form(storage, volume-step), jet)[0]
        high = energy(local_form(storage, volume+step), jet)[0]
        errors.append(abs((high-low)/(2*step)-derivative))
    assert errors[-1] < max(1e-8, abs(derivative)*1e-7)
    assert errors[0] > 3*errors[1] and errors[1] > 3*errors[2]


def test_subdivision_preserves_exact_geometry_energy_and_tangent():
    triangle = np.array([[0., 0., 0.], [1., 0., 1.], [0., 1., 2.]])
    center = triangle.mean(axis=0)
    original = TriangleCellStorage(triangle[None])
    divided = TriangleCellStorage(np.array([[triangle[i], triangle[(i+1)%3], center] for i in range(3)]))
    for height in (.1, .7, 1.2, 2.7):
        volume = original.relative_volume_and_wet_area(height)[0]
        first, second = local_form(original, volume), local_form(divided, volume)
        for key in ('gram', 'volume_derivative', 'depth_moments'):
            np.testing.assert_allclose(first[key], second[key], atol=1e-13, rtol=2e-12)


def test_flat_limit_and_datum_relative_thin_water():
    storage = cell([220., 220., 220.])
    for h in (1.5, 1e-20, 1e-100):
        form = local_form(storage, .5*h)
        assert form['stage_offset'] == h
        expected = np.diag([.5*h*h*h, 0., 0.])
        np.testing.assert_allclose(form['gram'], expected, atol=0., rtol=1e-13)
        assert form['represented_volume'] > 0.
        assert not form['intercell_or_two_pole_or_nonlinear_or_dry_or_gameplay_accepted']


def test_dry_and_level_shoreline_derivative_are_not_fabricated():
    with pytest.raises(ValueError, match='Strictly positive'):
        local_form(cell([0., 1., 2.]), 0.)
    triangles = np.array([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]],
                          [[2., 0., 1.], [3., 0., 1.], [2., 1., 1.]]])
    with pytest.raises(ValueError, match='two-sided'):
        local_form(TriangleCellStorage(triangles), .5)


def test_opposing_slopes_cannot_be_replaced_by_one_mean_slope():
    triangles = np.array([[[0., 0., 0.], [1., 0., 1.], [0., 1., 0.]],
                          [[1., 0., 1.], [2., 0., 0.], [1., 1., 1.]]])
    storage = TriangleCellStorage(triangles)
    volume = storage.relative_volume_and_wet_area(2.)[0]
    form = local_form(storage, volume)
    weights, h, slopes = quadrature(storage, form['stage_offset'])
    mean = np.sum((weights*h)[:, None]*slopes, axis=0)/volume
    collapsed = 3*volume*np.outer(mean, mean)
    lost = form['gram'][1:, 1:]-collapsed
    assert np.trace(lost) > 4.
    assert energy(form, [0., 1., 0.])[0] > .5*collapsed[0, 0]+2.


def test_clipped_source_triangle_ids_preserve_original_affine_surface():
    from test_triangle_cell_storage import mesh
    from south_fork_registered_mesh import RegisteredMeshSampler
    from triangle_cell_storage import cell_triangles
    sampler = RegisteredMeshSampler(mesh(lambda x, y: x*x+y*y))
    center = np.array([.1, -.1])
    triangles, ids = cell_triangles(sampler, center, [1.2, .8], with_source_ids=True)
    np.testing.assert_array_equal(triangles, cell_triangles(sampler, center, [1.2, .8]))
    for triangle, index in zip(triangles, ids):
        source = sampler.xyz[sampler.faces[index]]
        plane = np.linalg.solve(np.column_stack((source[:, :2], np.ones(3))), source[:, 2])
        expected = np.column_stack((triangle[:, :2]+center, np.ones(3)))@plane
        np.testing.assert_allclose(expected, triangle[:, 2], atol=1e-13)
    storage = TriangleCellStorage(triangles, ids)
    np.testing.assert_array_equal(storage.source_triangle_indices, ids)
    assert not storage.source_triangle_indices.flags.writeable
    ids[:] = 0
    assert np.any(storage.source_triangle_indices != 0)


def test_malformed_source_triangle_ids_rejected():
    triangle = np.array([[[0., 0., 0.], [1., 0., 1.], [0., 1., 2.]]])
    for ids in ([-1], [1.5], [1, 2]):
        with pytest.raises(ValueError, match='source triangle index'):
            TriangleCellStorage(triangle, ids)
