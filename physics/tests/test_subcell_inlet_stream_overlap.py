from dataclasses import replace
from fractions import Fraction as F

import pytest

from subcell_inlet_sweep_geometry import InletSweep
from subcell_inlet_stream_overlap import footprint_bounds, overlap, signed_area, support_margin, simultaneous_pairs
from test_subcell_inlet_sweep_geometry import fixture


def shifted(sweep, dx=F(0), dy=F(0)):
    return replace(sweep, edge=tuple((x+dx, y+dy, z) for x, y, z in sweep.edge))


def test_chord_and_tangent_areas_bound_independent_exact_incoming_area():
    sweep, _ = fixture()
    widths = []
    for n in (1, 2, 4, 8, 16):
        inside, outside = footprint_bounds(sweep, n)
        lo, hi = abs(signed_area(inside)), abs(signed_area(outside))
        assert lo <= sweep.full_moment(0) <= hi
        widths.append(hi-lo)
    assert all(b < a for a, b in zip(widths, widths[1:]))


def test_identical_streams_have_a_certified_interior_witness():
    sweep, _ = fixture()
    result = overlap(sweep, sweep)
    assert result['status'] == 'positive-overlap'
    assert 0 < result['area_lower'] <= sweep.full_moment(0) <= result['area_upper']
    assert min(support_margin(sweep, result['witness_xy'])) > 0
    assert not result['physical_update_accepted']


def test_separated_and_oppositely_directed_streams_do_not_merge_on_touch():
    sweep, _ = fixture()
    assert overlap(sweep, shifted(sweep, dx=10))['status'] == 'disjoint'
    opposite = replace(sweep, velocity=tuple(-v for v in sweep.velocity))
    result = overlap(sweep, opposite)
    assert result['status'] == 'disjoint' and result['area_upper'] == 0


def test_overlapping_rectangular_bounds_are_not_positive_curved_overlap():
    sweep, _ = fixture()
    end = sweep.height_scale*sweep.time_root/sweep.bed_span
    other = shifted(sweep, dx=F(4, 5)*sweep.velocity[0]*sweep.time_root**3, dy=F(7, 10)*sweep.delta[1]*end)
    assert overlap(sweep, other)['status'] == 'disjoint'


def test_explicit_budget_exhaustion_stays_unresolved_then_refines():
    sweep, _ = fixture()
    end = sweep.height_scale*sweep.time_root/sweep.bed_span
    other = shifted(sweep, dx=F(2, 5)*sweep.velocity[0]*sweep.time_root**3, dy=F(4, 5)*sweep.delta[1]*end)
    coarse = overlap(sweep, other, max_segments=1)
    assert coarse['status'] == 'unresolved' and coarse['area_lower'] == 0 < coarse['area_upper']
    assert not coarse['physical_update_accepted'] and coarse['witness_xy'] is None
    assert overlap(sweep, other)['status'] == 'positive-overlap'


def test_sub_float_positive_overlap_is_not_deleted():
    sweep, _ = fixture()
    epsilon = F(1, 10**200)
    other = shifted(sweep, dx=(1-epsilon)*sweep.velocity[0]*sweep.time_root**3)
    result = overlap(sweep, other)
    assert result['status'] == 'positive-overlap' and result['area_lower'] > 0
    assert float(result['area_lower']) == 0.


def test_original_domain_can_exclude_an_external_overlap():
    sweep, _ = fixture()
    domain = ((F(2), F(2)), (F(3), F(2)), (F(3), F(3)), (F(2), F(3)))
    result = overlap(sweep, sweep, domain=domain)
    assert result['status'] == 'disjoint'
    with pytest.raises(ValueError, match='convex exact domain'):
        overlap(sweep, sweep, domain=((0,0), (2,0), (1,F(1,4)), (2,2), (0,2)))


def test_different_times_reject_and_pair_router_uses_common_original_time():
    sweep, _ = fixture()
    early = replace(sweep, time_root=sweep.time_root/2)
    with pytest.raises(ValueError, match='SAME physical time'):
        overlap(sweep, early)
    def record(s):
        return dict(original_inlet_xyz=s.edge, constant_inlet_velocity_mps=s.velocity,
                    primary_height_scale=s.height_scale, time_root=s.time_root)
    result = simultaneous_pairs([record(sweep), {'status': 'receding-or-fan-requires-coupled-front-law'}, record(early)])
    assert result['represented_conditional_streams'] == 2
    assert result['pairs'][0]['time_seconds'] == early.time_root**3
    assert result['pairs'][0]['first_record'] == 0 and result['pairs'][0]['second_record'] == 2
    assert result['unsupported_original_records'] == [1]
    assert not result['merged_state_or_force_or_time_or_gameplay_accepted']


def test_large_translation_and_orientation_preserve_exact_bounds():
    sweep, _ = fixture()
    other = shifted(sweep, dx=F(1, 100))
    before = overlap(sweep, other)
    a, b = (shifted(s, F(10**15), F(-10**15)) for s in (sweep, other))
    after = overlap(replace(a, edge=tuple(reversed(a.edge))), b)
    assert (after['status'], after['area_lower'], after['area_upper']) == (before['status'], before['area_lower'], before['area_upper'])


def test_window_closure_bounds_earlier_separation_and_cannot_exceed_branch():
    sweep, _ = fixture()
    limit = F(2, 5)  # Above current R=.25 but below u_n^2/g.
    far = shifted(sweep, dx=10)
    result = overlap(sweep, far, closure_time_root=limit)
    assert result['status'] == 'disjoint' and result['closure_bound_only']
    assert result['time_seconds'] == limit**3
    for root in (sweep.time_root/2, sweep.time_root, F(3, 8)):
        assert overlap(replace(sweep, time_root=root), replace(far, time_root=root))['status'] == 'disjoint'
    with pytest.raises(ValueError, match='branch bounds'):
        overlap(sweep, sweep, closure_time_root=1)


def test_positive_endpoint_overlap_has_a_strictly_earlier_exact_witness():
    sweep, _ = fixture()
    result = overlap(sweep, shifted(sweep, dx=F(1, 50)), closure_time_root=F(2, 5))
    assert result['status'] == 'positive-overlap'
    earlier, endpoint = result['positive_witness_strictly_earlier_time'], result['time_seconds']
    assert 0 < earlier < endpoint
    for stream in (sweep, shifted(sweep, dx=F(1, 50))):
        s, age, margin = support_margin(stream, result['witness_xy'], F(2, 5))
        assert min(s, age, margin-(endpoint-earlier)) > 0


def test_pair_window_uses_both_original_limits_not_the_later_or_observation_time():
    sweep, _ = fixture()
    def record(limit):
        return dict(original_inlet_xyz=sweep.edge, constant_inlet_velocity_mps=sweep.velocity,
                    primary_height_scale=sweep.height_scale, time_root=sweep.time_root,
                    original_isolated_geometry_time_root_limit=limit)
    result = simultaneous_pairs([record(F(3, 10)), record(F(2, 5))], window_closure=True)
    assert result['pairs'][0]['time_seconds'] == F(3, 10)**3
    assert result['pairs'][0]['closure_bound_only']
    with pytest.raises(ValueError, match='precede'):
        simultaneous_pairs([record(F(1, 10)), record(F(2, 5))], window_closure=True)


@pytest.mark.parametrize('segments', [0, True, 4097])
def test_unbounded_or_noninteger_segment_budget_rejects(segments):
    sweep, _ = fixture()
    with pytest.raises(ValueError, match='segment count'):
        footprint_bounds(sweep, segments)


@pytest.mark.parametrize('domain', [(), ((0,), (1,), (2,)), ((0,0,0), (1,0,0), (1,1,0))])
def test_invalid_domain_shape_rejects_before_clipping(domain):
    sweep, _ = fixture()
    with pytest.raises(ValueError, match='convex exact domain'):
        overlap(sweep, sweep, domain=domain)


def test_missing_stream_provenance_and_implicit_closure_modes_cannot_pass():
    with pytest.raises(ValueError, match='cannot omit'):
        simultaneous_pairs([{'status': 'source-clipped-conditional-geometry'}])
    with pytest.raises(ValueError, match='boolean'):
        simultaneous_pairs([], window_closure='yes')
