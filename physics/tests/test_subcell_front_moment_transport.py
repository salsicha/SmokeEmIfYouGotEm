from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from audit_south_fork_affine_total_energy import branch_potential
from subcell_affine_dry_fan import AffineDryFan
from subcell_front_moment_transport import FrontMomentTransport, face_spatial_advection, volume_compression
from test_subcell_affine_dry_fan import rectangle
from test_subcell_affine_front_pressure import fixture
from test_subcell_front_auxiliary_transport import independent_profile, volume_quad
from test_subcell_front_profile_transport import numerical_velocity


@pytest.mark.parametrize('normal', ((1, 0), (0, 1), (3, 4), (-2, 1)))
def test_weighted_face_flux_against_independent_quadrature_reversal_and_split(normal):
    fan = AffineDryFan((0, 0), normal, F(3, 4), (F(2, 5), -F(1, 7)), 3, (F(1, 5), -F(1, 8)))
    xyz = lambda x, y: (x, y, fan.bed+fan.gradient[0]*x+fan.gradient[1]*y)
    a, b, t = xyz(-F(3, 2), -F(2, 5)), xyz(F(3, 2), F(1, 3)), F(1, 5)
    result = face_spatial_advection(fan, a, b, t)
    state, cuts, n, origin = independent_profile(fan, t)
    start, end = np.array(a[:2], float), np.array(b[:2], float)
    normal_measure = np.array((end[1]-start[1], start[0]-end[0]))
    q0, dq = n@(start-origin), n@(end-start)
    knots = [(q-q0)/dq for q in cuts if dq and 0 < (q-q0)/dq < 1]
    for axis in range(2):
        def integrand(s):
            p = start+s*(end-start)
            return (p[axis]-origin[axis])*state(p)[0]*(numerical_velocity(fan, t, p)@normal_measure)
        expected = quad(integrand, 0, 1, points=knots, epsabs=1e-12)[0]
        assert float(result[axis]) == pytest.approx(expected, rel=2e-13, abs=2e-13)
    assert result == tuple(-x for x in face_spatial_advection(fan, b, a, t))
    middle = tuple(x+F(2, 7)*(y-x) for x, y in zip(a, b))
    assert result == tuple(x+y for x, y in zip(face_spatial_advection(fan, a, middle, t),
                                              face_spatial_advection(fan, middle, b, t)))


@pytest.mark.parametrize('normal', ((1, 0), (0, 1), (3, 4), (-2, 1)))
def test_all_moments_match_time_rates_and_compression_is_independent_volume_integral(normal):
    fan = AffineDryFan((0, 0), normal, F(7, 10), (F(1, 3), -F(1, 4)), 2, (F(1, 5), -F(1, 7)))
    fragments = tuple(rectangle(x0=a, x1=b, slope=fan.gradient, bed=fan.bed) for a, b in ((-1, 0), (0, 1)))
    t = F(1, 5)
    op = FrontMomentTransport(fan, fragments, t)
    result = op.rates()
    profile = independent_profile(fan, t)
    for i, fragment in enumerate(fragments):
        assert result['moments'][i] == op.geometry.forms[i]['depth_moment_rates']
        assert result['spatial'][i] == op.geometry.forms[i]['depth_spatial_moment_rates']
        for k, actual in enumerate(op.compression[i], 1):
            expected = volume_quad(fragment, profile, lambda x, y, h, ht, grad:
                                   h**k*(2/(3*float(t)) if np.any(grad) else 0))
            assert float(actual) == pytest.approx(expected, rel=2e-12, abs=2e-12)
    assert all(row[0] == 0 for row in result['moment_compression_sources'])
    assert any(row[1] != 0 and row[2] != 0 for row in result['moment_compression_sources'])
    for k in range(3):
        total = sum(row[k] for row in result['moments'])
        incoming = -sum(face['moments'][k] for face in result['exterior_faces'])
        compression = sum(row[k] for row in result['moment_compression_sources'])
        assert total == incoming+compression
        if k: assert total != incoming  # Pure face advection is the wrong higher-moment law.
    for axis in range(2):
        assert sum(row[axis] for row in result['spatial']) == (
            -sum(face['spatial'][axis] for face in result['exterior_faces'])
            +sum(row[axis] for row in result['spatial_sources']))
    assert not result['dispersive_force_or_interacting_fronts_or_gameplay_accepted']


def test_gravity_work_matches_direct_branch_time_rate_with_explicit_exterior_pressure_and_bed():
    fan, fragments, t = fixture()
    op = FrontMomentTransport(fan, fragments, t)
    result = op.potential_balance(F(17, 3))
    for i, fragment in enumerate(fragments):
        _, rate = branch_potential(fan, [fragment], t, F(17, 3))
        assert result['potential_rate'][i] == rate
    assert sum(result['potential_rate']) == (-result['exterior_potential_flux']
                                              +sum(result['compression_work'])+sum(result['bed_work']))
    assert any(x != 0 for x in result['compression_work'])
    assert any(x != 0 for x in result['bed_work'])
    assert result['exterior_potential_flux'] != 0
    assert not result['total_energy_flux_or_dispersive_force_or_gameplay_accepted']
    before = op.potential_balance()
    mass = tuple(row[0] for row in op.rates()['moments'])
    assert tuple(b-a for a, b in zip(before['potential_rate'], result['potential_rate'])) == tuple(
        -fan.gravity*F(17, 3)*x for x in mass)
    assert before['compression_work'] == result['compression_work']
    assert before['bed_work'] == result['bed_work']


def test_partition_hanging_edges_reversal_and_exact_dry_owner():
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 2, (F(1, 5), -F(1, 7)))
    make = lambda **kw: rectangle(slope=fan.gradient, bed=fan.bed, **kw)
    fragments = (make(x0=-1, x1=0, y0=-1, y1=1), make(x0=0, x1=1, y0=-1, y1=0),
                 make(x0=0, x1=1, y0=0, y1=1), make(x0=4, x1=5, y0=-1, y1=1))
    op = FrontMomentTransport(fan, fragments, F(1, 5))
    reversed_op = FrontMomentTransport(fan, tuple(replace(f, polygon=tuple(reversed(f.polygon))) for f in fragments), F(1, 5))
    whole = FrontMomentTransport(fan, [make(x0=-1, x1=1, y0=-1, y1=1)], F(1, 5))
    assert op.rates() == reversed_op.rates()
    assert op.potential_balance() == reversed_op.potential_balance()
    assert op.rates()['moments'][-1] == (0, 0, 0)
    assert op.rates()['spatial'][-1] == (0, 0)
    for key, count in (('moments', 3), ('spatial', 2)):
        assert tuple(sum(row[j] for row in op.rates()[key]) for j in range(count)) == whole.rates()[key][0]
    assert sum(op.potential_balance()['potential_rate']) == whole.potential_balance()['potential_rate'][0]


def test_positive_sub_float_front_is_not_dropped():
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 0, (0, 0), gravity=1)
    op = FrontMomentTransport(fan, [rectangle(x0=0, x1=1)], F(1, 10**400))
    assert op.geometry.active == (0,)
    assert op.geometry.volumes[0] > 0 and float(op.geometry.volumes[0]) == 0
    assert op.compression[0][1] > 0
    assert op.rates()['moments'][0][1] > 0
    assert op.potential_balance()['potential_rate'][0] > 0


def test_translated_world_keeps_original_depth_weighted_spatial_frame():
    fan, fragments, t = fixture()
    delta = (F(10000001, 3), -F(30000002, 7))
    moved = AffineDryFan(delta, fan.normal, fan.depth, fan.velocity, fan.bed, fan.gradient, fan.gravity)
    shifted = tuple(replace(f, polygon=tuple((p[0]+delta[0], p[1]+delta[1], p[2]) for p in f.polygon)) for f in fragments)
    first, second = FrontMomentTransport(fan, fragments, t), FrontMomentTransport(moved, shifted, t)
    for key in ('moments', 'spatial', 'moment_compression_sources', 'spatial_sources'):
        assert first.rates()[key] == second.rates()[key]
    assert first.potential_balance()['potential_rate'] == second.potential_balance()['potential_rate']


@pytest.mark.parametrize('bad', ('time', 'slope', 'bed'))
def test_invalid_original_geometry_or_time_is_rejected(bad):
    fan, fragments, t = fixture()
    if bad == 'time': t = 0
    elif bad == 'slope': fragments = (replace(fragments[0], gradient=(0, 0)),)
    else:
        points = list(fragments[0].polygon)
        points[0] = (*points[0][:2], points[0][2]+F(1, 10**400))
        fragments = (replace(fragments[0], polygon=tuple(points)),)
    with pytest.raises(ValueError):
        FrontMomentTransport(fan, fragments, t)
