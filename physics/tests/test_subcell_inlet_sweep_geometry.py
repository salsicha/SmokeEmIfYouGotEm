from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_exact_geometry import SourceFragment, clip
from subcell_inlet_sweep_geometry import InletSweep, polynomial_bounds, shared_inlet_edge


def fixture():
    # Original receiver falls five metres/metre away from a high inlet.
    polygon = tuple(tuple(map(F, p)) for p in ((0, 0, 10), (2, 0, 0), (0, 2, 12)))
    receiver = SourceFragment(17, polygon, (F(-5), F(1)))
    sweep = InletSweep((polygon[0], polygon[2]), (2, 0), 1, F(1, 4))
    return sweep, receiver


def test_full_inlet_strip_retains_original_source_and_exact_four_moments():
    sweep, receiver = fixture()
    sweep.validate_receiver(receiver)
    before = receiver.polygon
    result = sweep.moments(receiver)
    assert result['source_id'] == 17
    assert result['lower'] == result['upper'] == tuple(sweep.full_moment(p) for p in range(4))
    assert receiver.polygon == before
    assert not result['full_force_or_time_or_native_or_gameplay_accepted']
    # Integrated ORIGINAL wet-branch mass J*(k*t^(1/3))^2/(2*B).
    assert sweep.full_moment(1) == F(3, 10)*sweep.jacobian*sweep.height_scale**2*sweep.time_root**5/sweep.bed_span


def test_water_stays_at_high_inlet_not_at_receiver_minimum():
    sweep, receiver = fixture()
    xy, depth = sweep.point(sweep.time_root, F(1, 32))
    assert xy == (0, F(1, 16)) and depth > 0
    assert min(p[2] for p in receiver.polygon) == 0
    # The dry low vertex has no preimage in the inlet support.
    assert max(sweep.point(r, 0)[0][0] for r in (0, sweep.time_root)) < 2
    inlet_bed = receiver.polygon[0][2]+sum(g*x for g, x in zip(receiver.gradient, xy))
    assert inlet_bed+depth > 10


@pytest.mark.parametrize('cut', [F(7, 256), F(3, 200)])
def test_crossed_source_edge_keeps_all_mass_with_certified_bounds(cut):
    sweep, receiver = fixture()
    pieces = [SourceFragment(i, clip(receiver.polygon, 0, cut, side), receiver.gradient)
              for i, side in enumerate((False, True))]
    result = [sweep.moments(piece) for piece in pieces]
    for power in range(4):
        low, high = (sum(r[key][power] for r in result) for key in ('lower', 'upper'))
        total = sweep.full_moment(power)
        assert low <= total <= high
        assert high-low <= 2*F(1, 10**12)*total
        # Independent analytic switch r=(R^3-cut/u_x)^(1/3).
        root = np.cbrt(float(sweep.time_root**3-cut/sweep.velocity[0]))
        expected = float(sweep.full_moment(power))*(1-(root/float(sweep.time_root))**(power+4))
        np.testing.assert_allclose(float(sum(result[0][k][power] for k in ('lower', 'upper'))/2), expected, rtol=1e-12)
    assert result[1]['lower'][1] > 0  # Must be routed, never silently clipped away.


def test_oblique_source_edge_matches_independent_slice_quadrature():
    sweep, _ = fixture()
    # x+y <= 1/8 cuts the strip with a cubic/linear envelope switch.
    polygon = tuple(tuple(map(F, p)) for p in ((0, 0, 10), (F(1, 8), 0, F(75, 8)), (0, F(1, 8), F(81, 8))))
    piece = SourceFragment(99, polygon, (F(-5), F(1)))
    result = sweep.moments(piece)
    for p in range(4):
        def integrand(r):
            x = 2*(float(sweep.time_root)**3-r**3)
            upper = min(r/2, max(0, (1/8-x)/2))
            return 12*r*r*(r**(p+1)-(r-2*upper)**(p+1))/(2*(p+1))
        observed = quad(integrand, 0, .25, epsabs=1e-16, epsrel=1e-12, points=[.1, .125, .2])[0]
        midpoint = float((result['lower'][p]+result['upper'][p])/2)
        np.testing.assert_allclose(midpoint, observed, rtol=1e-10, atol=1e-17)


def test_orientation_translation_and_original_fragments_are_preserved():
    sweep, receiver = fixture()
    result = sweep.moments(receiver)
    offset = (F(10**12), F(-10**12))
    moved = lambda p: (p[0]+offset[0], p[1]+offset[1], p[2])
    other = InletSweep(tuple(moved(p) for p in reversed(sweep.edge)), sweep.velocity, 1, F(1, 4))
    piece = SourceFragment(17, tuple(moved(p) for p in reversed(receiver.polygon)), receiver.gradient)
    assert other.moments(piece)['lower'] == result['lower']


def test_tiny_positive_velocity_is_not_a_fan_or_epsilon_sweep():
    sweep, _ = fixture()
    with pytest.raises(ValueError, match='fan branch'):
        InletSweep(sweep.edge, (F(1, 10**126), 0), 1, F(1, 10**6))
    tiny = InletSweep(sweep.edge, (F(1, 10**126), 0), 1, F(1, 10**255))
    assert tiny.full_moment(1) > 0
    assert float(tiny.full_moment(1)) == 0  # Remains rational; not an accepted float water state.


def test_insufficient_switch_resolution_fails_without_discarding_slivers():
    sweep, receiver = fixture()
    piece = SourceFragment(18, clip(receiver.polygon, 0, F(3, 200), False), receiver.gradient)
    with pytest.raises(ValueError, match='bound unresolved'):
        sweep.moments(piece, max_depth=1)


@pytest.mark.parametrize('edge,velocity,k,r', [
    (((0, 0, 1), (0, 1, 1)), (1, 0), 1, F(1, 4)),
    (((0, 0, 1), (0, 1, 2)), (0, 1), 1, F(1, 4)),
    (((0, 0, 1), (0, 1, 2)), (4, 0), 1, 1),
    (((0, 0, 1), (0, 1, 2)), (4, 0), 1, -1),
])
def test_invalid_geometry_or_knot_rejected(edge, velocity, k, r):
    with pytest.raises(ValueError):
        InletSweep(edge, velocity, k, r)


def test_bernstein_bound_contains_cubic_extrema():
    polynomial = (F(2), F(-7), F(3), F(11))
    lo, hi = polynomial_bounds(polynomial, F(-2), F(3))
    for x in np.linspace(-2, 3, 1001):
        value = sum(float(c)*x**i for i, c in enumerate(polynomial))
        assert float(lo)-1e-12 <= value <= float(hi)+1e-12


def test_inlet_direction_and_shared_original_edge_validation():
    sweep, receiver = fixture()
    left = SourceFragment(18, tuple(tuple(map(F, p)) for p in
        ((0, 0, 10), (0, 2, 12), (-2, 0, 10))), (F(0), F(1)))
    assert set(shared_inlet_edge(left, receiver)) == set(sweep.edge)
    sweep.validate_receiver(receiver)
    with pytest.raises(ValueError, match='does not enter'):
        sweep.validate_receiver(left)
    reverse = InletSweep(sweep.edge, (-2, 0), 1, F(1, 4))
    with pytest.raises(ValueError, match='does not enter'):
        reverse.validate_receiver(receiver)
    reverse.validate_receiver(left)
    with pytest.raises(ValueError, match='bed elevations disagree'):
        shared_inlet_edge(receiver, SourceFragment(19,
            tuple((x, y, z+1) for x, y, z in left.polygon), left.gradient))
    point_only = SourceFragment(20, tuple(tuple(map(F, p)) for p in
        ((0, 0, 10), (-1, 0, 10), (0, -1, 9))), (F(0), F(1)))
    with pytest.raises(ValueError, match='point contact'):
        shared_inlet_edge(point_only, receiver)
    with pytest.raises(ValueError, match='original receiving boundary'):
        sweep.validate_receiver(point_only)
