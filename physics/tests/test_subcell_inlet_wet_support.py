from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_exact_geometry import SourceFragment
from subcell_inlet_sweep_geometry import InletSweep
from test_subcell_inlet_sweep_geometry import fixture


def test_owned_source_can_have_water_without_any_inlet_overlap():
    sweep, fragment = fixture()
    assert fragment.depth_moments(1)[1] > 0
    result = sweep.initial_wet_support_moments(fragment, 1, 0)
    assert result['on_initial_wet_support']['upper'] == (F(0),)*4
    assert result['on_initial_dry_support']['lower'] == tuple(sweep.full_moment(p) for p in range(4))
    assert not result['positive_initial_wet_overlap_possible']
    assert not result['merged_state_or_force_or_time_or_gameplay_accepted']


@pytest.mark.parametrize('surface', [F(-1), F(0), F(12), F(13)])
def test_dry_and_fully_wet_extremes_preserve_all_four_moments(surface):
    sweep, fragment = fixture()
    result = sweep.initial_wet_support_moments(fragment, surface, 0)
    wet = surface >= 12
    for p in range(4):
        assert result['on_initial_wet_support']['lower'][p] == (sweep.full_moment(p) if wet else 0)
        assert result['on_initial_dry_support']['lower'][p] == (0 if wet else sweep.full_moment(p))
        assert result['on_initial_wet_support']['upper'][p] == result['on_initial_wet_support']['lower'][p]


@pytest.mark.parametrize('surface', [F(999, 100), F(1001, 100), F(1005, 100)])
def test_oblique_wet_shoreline_matches_independent_quadrature_and_retains_complement(surface):
    sweep, fragment = fixture()
    original = fragment.polygon
    result = sweep.initial_wet_support_moments(fragment, surface, 0)
    assert result['positive_initial_wet_overlap_proven']
    assert result['on_initial_dry_support']['lower'][1] > 0
    for p in range(4):
        # Original bed: z=10-5*x+y. This integrates incoming h, not pool h.
        def integrand(r):
            x = 2*(.25**3-r**3)
            end = min(r/2, max(0, (float(surface)-10+5*x)/2))
            return 12*r*r*(r**(p+1)-(r-2*end)**(p+1))/(2*(p+1))
        expected = quad(integrand, 0, .25, epsabs=1e-17, epsrel=1e-11,
                        points=np.linspace(0, .25, 17)[1:-1])[0]
        wet, dry = result['on_initial_wet_support'], result['on_initial_dry_support']
        midpoint = float((wet['lower'][p]+wet['upper'][p])/2)
        np.testing.assert_allclose(midpoint, expected, rtol=1e-9, atol=1e-17)
        low, high = wet['lower'][p]+dry['lower'][p], wet['upper'][p]+dry['upper'][p]
        assert low <= sweep.full_moment(p) <= high
        assert high-low <= 2*F(1, 10**12)*sweep.full_moment(p)
    assert fragment.polygon == original


def test_stage_datum_never_rounds_away_a_positive_thin_film():
    sweep, fragment = fixture()
    flat = SourceFragment(fragment.source_id, tuple((x, y, F(10**12)) for x, y, z in fragment.polygon), (F(0), F(0)))
    film = F(1, 10**400)
    dry = sweep.initial_wet_support_moments(flat, 0, F(10**12))
    wet = sweep.initial_wet_support_moments(flat, film, F(10**12))
    assert dry['on_initial_wet_support']['upper'] == (F(0),)*4
    assert wet['original_stage'] > F(10**12)
    assert wet['on_initial_wet_support']['lower'] == tuple(sweep.full_moment(p) for p in range(4))
    assert wet['positive_initial_wet_overlap_proven']


def test_large_vertical_datum_and_polygon_orientation_do_not_change_intersection():
    sweep, fragment = fixture()
    expected = sweep.initial_wet_support_moments(fragment, F(999, 100), 0)
    dz = F(10**15)
    moved = SourceFragment(fragment.source_id, tuple((x, y, z+dz) for x, y, z in reversed(fragment.polygon)), fragment.gradient)
    other = InletSweep(tuple((x, y, z+dz) for x, y, z in sweep.edge), sweep.velocity, sweep.height_scale, sweep.time_root)
    result = other.initial_wet_support_moments(moved, F(999, 100), dz)
    for key in ('on_initial_wet_support', 'on_initial_dry_support'):
        assert result[key]['lower'] == expected[key]['lower']
        assert result[key]['upper'] == expected[key]['upper']


@pytest.mark.parametrize('offset,datum', [(float('nan'), 0), (0, float('inf')), (float('-inf'), 0)])
def test_nonfinite_stage_rejected(offset, datum):
    sweep, fragment = fixture()
    with pytest.raises(ValueError, match='Finite exact original stage'):
        sweep.initial_wet_support_moments(fragment, offset, datum)


def test_insufficient_wet_shoreline_resolution_rejects_without_deleting_water():
    sweep, fragment = fixture()
    with pytest.raises(ValueError, match='bound unresolved'):
        sweep.initial_wet_support_moments(fragment, F(999, 100), 0, max_depth=1)
