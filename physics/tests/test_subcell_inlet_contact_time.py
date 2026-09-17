from fractions import Fraction as F

import numpy as np
import pytest
from scipy.optimize import minimize_scalar

from subcell_exact_geometry import SourceFragment
from subcell_inlet_sweep_geometry import InletSweep
from subcell_inlet_contact_time import first_contact, initial_wet_contact
from test_subcell_inlet_sweep_geometry import fixture


def transformed_polygon(points):
    # Fixture D=(0,2), u=(2,0), original bed z=10-5*x+y.
    return SourceFragment(19, tuple((2*a, 2*s, 10-10*a+2*s) for s, a in points), (F(-5), F(1)))


def test_high_inlet_reaches_existing_low_pool_only_at_exact_later_contact():
    sweep, fragment = fixture()
    result = initial_wet_contact(sweep, fragment, 1, 0)
    assert result['time_lower'] == result['time_upper'] == F(9, 10)
    assert sweep.time_root**3 < result['time_lower']
    assert not result['within_sweep_own_branch_bound']
    assert not result['physical_update_accepted']


def test_inlet_already_touches_positive_wet_support_at_time_zero():
    sweep, fragment = fixture()
    result = initial_wet_contact(sweep, fragment, 11, 0)
    assert result['time_lower'] == result['time_upper'] == 0
    assert result['within_sweep_own_branch_bound']


def test_interior_edge_minimum_not_just_polygon_vertices():
    sweep, _ = fixture()
    polygon = transformed_polygon(tuple((F(s), F(a)) for s, a in
        ((0, F(2, 5)), (F(1, 2), F(7, 25)), (F(1, 2), F(1, 2)), (0, F(1, 2)))))
    result = first_contact(sweep, polygon)
    assert result['stationary_candidates'] > 0
    assert result['time_lower'] == result['time_upper'] == F(48, 125)


def test_irrational_contact_is_bounded_and_matches_independent_minimization():
    sweep, _ = fixture()
    polygon = transformed_polygon(((F(0), F(7, 10)), (F(1, 2), F(1, 10)),
                                   (F(1, 2), F(4, 5)), (F(0), F(4, 5))))
    result = first_contact(sweep, polygon)
    low, high = result['time_lower'], result['time_upper']
    assert low < high and high-low <= F(1, 10**12)*high
    reference = minimize_scalar(lambda s: 8*s**3+.7-1.2*s, bounds=(0, .5), method='bounded',
                                options={'xatol': 1e-14})
    np.testing.assert_allclose(float((low+high)/2), reference.fun, atol=1e-12, rtol=0)
    with pytest.raises(ValueError, match='bound unresolved'):
        first_contact(sweep, polygon, relative_bound=F(1, 10**30), max_bits=16)


def test_time_bounds_predict_zero_before_and_positive_after_reachable_contact():
    sweep, fragment = fixture()
    # Bed=9.9 first occurs at x=.02, so time=.01 < outward branch limit.
    contact = initial_wet_contact(sweep, fragment, F(99, 10), 0)
    assert contact['time_lower'] == contact['time_upper'] == F(1, 100)
    before = InletSweep(sweep.edge, sweep.velocity, 1, F(1, 5))  # t=.008
    after = InletSweep(sweep.edge, sweep.velocity, 1, F(1, 4))   # t=.015625
    assert not before.initial_wet_support_moments(fragment, F(99, 10), 0)['positive_initial_wet_overlap_possible']
    assert after.initial_wet_support_moments(fragment, F(99, 10), 0)['positive_initial_wet_overlap_proven']


def test_dry_and_unreachable_support_cannot_be_marked_as_contact():
    sweep, fragment = fixture()
    assert not initial_wet_contact(sweep, fragment, 0, 0)['positive_contact_possible']
    behind = transformed_polygon(((F(0), F(-1)), (F(1), F(-1)), (F(1), F(0)), (F(0), F(0))))
    assert not first_contact(sweep, behind)['positive_contact_possible']


def test_coordinate_orientation_and_vertical_datum_preserve_contact():
    sweep, fragment = fixture()
    offset = (F(10**12), F(-10**12), F(10**15))
    move = lambda p: tuple(x+y for x, y in zip(p, offset))
    moved = SourceFragment(fragment.source_id, tuple(move(p) for p in reversed(fragment.polygon)), fragment.gradient)
    other = InletSweep(tuple(move(p) for p in reversed(sweep.edge)), sweep.velocity, 1, F(1, 4))
    result = initial_wet_contact(other, moved, F(99, 10), offset[2])
    assert result['time_lower'] == result['time_upper'] == F(1, 100)
