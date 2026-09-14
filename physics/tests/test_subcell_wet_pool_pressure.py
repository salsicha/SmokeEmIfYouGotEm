from decimal import Decimal, localcontext
from types import SimpleNamespace
import numpy as np
import pytest

from test_triangle_face_section import sampler
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_connectivity import components, shared_wet_edge
from subcell_wet_pool_partition import WetPoolPartition
from subcell_wet_pool_pressure import WetPoolPressureSystem, harmonic_area, response
from smooth_rational_velocity_stage import make
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from finite_depth_pressure_reference import LENGTHS, response as linear_response


def partition(height, stages, shape=(1, 1), spacing=(2., 2.), origin=(0., 0.), periodic=(False, False)):
    source = sampler(height)
    patch = SubcellGeometryPatch(source, origin, shape, spacing, periodic, relative_stages=True)
    v, p = patch.state_from_stages(stages, [.4, -.2])
    return WetPoolPartition(patch, source, origin, v, p), source, v, p


def test_source_topology_separates_pools_and_preserves_state_and_kinetic_form():
    pools, _, v, p = partition(lambda x, y: 1-abs(x), .37)
    assert len(pools.pools) == 2
    assert pools.parent_pools == [[0, 1]]
    np.testing.assert_allclose(pools.reassembled_volumes, v, atol=1e-14, rtol=0)
    np.testing.assert_allclose(pools.reassembled_momenta, p, atol=1e-14, rtol=0)
    assert pools.maximum_gram_partition_error < 1e-13
    assert pools.maximum_volume_tangent_partition_error < 1e-13


def test_dry_edge_point_contact_and_subnormal_width_do_not_use_a_threshold():
    source = SimpleNamespace(xyz=np.array([[-.5, 0., 1.], [.5, 0., 1.]]))
    assert not shared_wet_edge(source, (0, 1), [0., 0.], [1., 1.], 1., 0.)
    assert shared_wet_edge(source, (0, 1), [0., 0.], [1., 1.], 1., 1e-150)
    # Only the endpoint lies on this footprint; its positive depth is not an edge.
    assert not shared_wet_edge(source, (0, 1), [1., 0.], [1., 1.], 1., .1)
    point = SimpleNamespace(xyz=np.array([[0., 0., 0.], [0., 0., 1.]]))
    assert not shared_wet_edge(point, (0, 1), [0., 0.], [1., 1.], 0., 2.)


def test_pressure_does_not_bridge_the_two_sides_of_an_internal_rock_ridge():
    pools, _, _, _ = partition(lambda x, y: 1-abs(x), .37)
    system = WetPoolPressureSystem(pools, float(LENGTHS[0]))
    assert not system.connections
    assert system.maximum_wall_column_partition_error < 1e-12
    q = np.zeros((2, 1, 2)); q[0, 0] = [1., -.3]
    assert np.array_equal(system.apply(q)[1], np.zeros((1, 2)))
    result = response(pools, q)
    np.testing.assert_array_equal(result['value'][1], 0.)
    assert max(r['relative_residual'] for r in result['poles']) < 2e-5


@pytest.mark.parametrize('length', LENGTHS)
def test_flat_variable_depth_operator_reduces_to_original_reconstruction(length):
    depths = 1.+.2*np.random.default_rng(2410).random((3, 4))
    pools, _, _, _ = partition(lambda x, y: x*0, depths, (3, 4), (.5, .5), (-.75, -.5), (True, True))
    assert len(pools.pools) == depths.size
    system = WetPoolPressureSystem(pools, float(length))
    original = ReconstructedAccelerationSystem(make(depths, np.zeros_like(depths), .5), float(length))
    assert system.maximum_shared_column_partition_error < 1e-12
    q = np.random.default_rng(2412).normal(size=(*depths.shape, 2))
    np.testing.assert_allclose(system.apply(q.reshape(-1, 1, 2)).reshape(q.shape), original.apply(q), atol=1e-12, rtol=0)


def test_original_oblique_two_pole_linear_response():
    shape = (8, 8); dx = .25; depth = 1.5
    pools, _, _, _ = partition(lambda x, y: x*0, depth, shape, (dx, dx), (-.875, -.875), (True, True))
    y, x = np.indices(shape)
    phase = 2*np.pi*(x/8+2*y/8)
    k = np.array([np.sin(2*np.pi/8), np.sin(4*np.pi/8)])/dx
    q = (np.cos(phase)[..., None]*k/np.linalg.norm(k)).reshape(-1, 1, 2)
    result = response(pools, q)
    np.testing.assert_allclose(result['value'], q*linear_response(depth*np.linalg.norm(k)), atol=1e-12, rtol=0)


def test_factored_operator_adjoint_positive_form_and_local_blocks():
    pools, _, _, _ = partition(lambda x, y: .2*x+.1*y, .73, (2, 2), (.5, .5), (-.25, -.25))
    system = WetPoolPressureSystem(pools, .4)
    rng = np.random.default_rng(2414)
    a, b = rng.normal(size=(2, len(pools.pools), 1, 2))
    fa = system.factor_action(a)
    fb = [rng.normal(size=f.shape) for f in fa]
    assert abs(sum(float(x@y) for x, y in zip(fa, fb))-float(np.sum(a*system.factor_transpose(fb)))) < 1e-12
    assert abs(np.sum(a*system.apply(b))-np.sum(b*system.apply(a))) < 1e-12
    expected = np.sum(a*a)+.4*sum(float(f@f) for f in fa)
    assert abs(np.sum(a*system.apply(a))-expected) < 1e-12
    columns = []
    for i in range(a.size):
        basis = np.zeros_like(a); basis.flat[i] = 1.
        columns.append(system.apply(basis).ravel())
    matrix = np.stack(columns, axis=1)
    np.testing.assert_allclose(matrix.diagonal().reshape(-1, 2), system.diagonal, atol=1e-12)
    np.testing.assert_allclose(matrix[::2, 1::2].diagonal(), system.off_diagonal, atol=1e-12)
    actual, info = system.solve(a)
    np.testing.assert_allclose(actual.ravel(), np.linalg.solve(matrix, a.ravel()), atol=1e-11)
    assert info['relative_residual'] < 2e-5


def test_harmonic_face_integral_against_high_precision_antiderivative():
    for low, high, delta in ((0., 1., .3), (.2, 1.3, 2.), (0., .01, 20.), (.3, .30001, .2)):
        # Bed from -high to -low; lower water stage zero gives these depths.
        segment = np.array([[0., -high], [1., -low]])
        with localcontext() as ctx:
            ctx.prec = 70
            a, b, d = map(Decimal.from_float, (low, high, delta))
            primitive = lambda z: z*z/2+d*z/2-d*d*(2*z+d).ln()/4
            expected = float((primitive(b)-primitive(a))/(b-a))
        np.testing.assert_allclose(harmonic_area(segment, 0., delta, 0., 0.), expected, atol=0., rtol=2e-12)
        np.testing.assert_allclose(harmonic_area(segment, delta, 0., 0., 0.), expected, atol=0., rtol=2e-12)


def test_harmonic_face_dry_and_datum_relative_thin_limits():
    flat = np.array([[0., 220.], [1., 220.]])
    slope = np.array([[0., 220.], [1., 221.]])
    for h in (1e-10, 1e-50, 1e-150):
        assert harmonic_area(flat, 0., h, 220., 220.) == 0.
        np.testing.assert_allclose(harmonic_area(flat, h, h, 220., 220.), h, atol=0., rtol=1e-13)
        np.testing.assert_allclose(harmonic_area(slope, h, h, 220., 220.), .5*h*h, atol=0., rtol=1e-13)
        np.testing.assert_allclose(harmonic_area(slope, h, 1., 220., 220.), h*h, atol=0., rtol=1e-9)


def test_dry_cell_is_absent_and_topology_event_requires_explicit_transition():
    pools, _, _, _ = partition(lambda x, y: x*0, [[1., 0.]], (1, 2), (.5, .5), (-.25, 0.))
    assert len(pools.pools) == 1
    assert pools.parent_pools[1] == []
    with pytest.raises(ValueError, match='Topology event'):
        partition(lambda x, y: 1-abs(x), .5)
