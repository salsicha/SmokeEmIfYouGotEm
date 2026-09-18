from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_affine_dry_fan import AffineDryFan
from subcell_affine_front_pressure import face_metric
from subcell_front_auxiliary_transport import FrontAuxiliaryTransport, face_depth_moments
from test_subcell_affine_dry_fan import rectangle
from test_subcell_affine_front_pressure import fixture


ADV = ((F(2, 3), -F(1, 5)), (F(1, 4), F(2, 7)))
U = ((F(1, 3), -F(2, 5)), (F(1, 7), F(2, 9)))
V = ((F(2, 5), F(1, 3)), (-F(1, 4), F(3, 7)))


def transport():
    fan, fragments, time = fixture()
    return fan, fragments, time, FrontAuxiliaryTransport(
        fan, fragments, time, ADV, outer_boundary='reflecting')


def independent_profile(fan, time):
    n, slope, origin, velocity = (np.array(values, float) for values in
                                 (fan.normal, fan.gradient, fan.origin, fan.velocity))
    depth, g, t = float(fan.depth), float(fan.gravity), float(time)
    norm2, un = n@n, n@velocity
    c, acceleration = np.sqrt(g*depth*norm2), g*(n@slope)
    head, front = (un-c)*t-acceleration*t*t/2, (un+2*c)*t-acceleration*t*t/2
    def state(point):
        q = n@(np.array(point)-origin)
        if q <= head:
            return depth, 0., np.zeros(2)
        if q >= front:
            return 0., 0., np.zeros(2)
        linear = un+2*c-q/t-acceleration*t/2
        return (linear**2/(9*g*norm2),
                2*linear*(q/t**2-acceleration/2)/(9*g*norm2),
                -2*linear*n/(9*g*norm2*t))
    return state, (head, front), n, origin


def volume_quad(fragment, profile, function):
    state, cuts, n, origin = profile
    xy = np.array([[float(p[0]), float(p[1])] for p in fragment.polygon])
    low, high = xy.min(axis=0), xy.max(axis=0)
    def row(y):
        knots = [origin[0]+(q-n[1]*(y-origin[1]))/n[0] for q in cuts] if n[0] else []
        return quad(lambda x: function(x, y, *state((x, y))), low[0], high[0],
                    points=[x for x in knots if low[0] < x < high[0]], epsabs=2e-12)[0]
    ycuts = [origin[1]+(q-n[0]*(x-origin[0]))/n[1]
             for q in cuts for x in (low[0], high[0])] if n[1] else []
    return quad(row, low[1], high[1], points=[y for y in ycuts if low[1] < y < high[1]],
                epsabs=2e-12)[0]


@pytest.mark.parametrize('normal', ((1, 0), (3, 4), (-2, 1)))
def test_profile_face_moments_match_independent_quadrature_and_exact_edge_splits(normal):
    fan = AffineDryFan((0, 0), normal, F(3, 4), (F(2, 5), -F(1, 7)), 3, (F(1, 5), -F(1, 8)))
    a = (-F(3, 2), -F(2, 5)); b = (F(3, 2), F(1, 3)); t = F(1, 5)
    xyz = lambda p: (*p, fan.bed+sum(s*x for s, x in zip(fan.gradient, p)))
    a, b = xyz(a), xyz(b)
    moments = face_depth_moments(fan, a, b, t)
    state, cuts, n, origin = independent_profile(fan, t)
    xy0, xy1 = np.array(a[:2], float), np.array(b[:2], float)
    q0, dq = n@(xy0-origin), n@(xy1-xy0)
    knots = [(q-q0)/dq for q in cuts if dq and 0 < (q-q0)/dq < 1]
    for k, value in enumerate(moments, 1):
        expected = quad(lambda s: state(xy0+s*(xy1-xy0))[0]**k,
                        0, 1, points=knots, epsabs=1e-12)[0]
        assert float(value) == pytest.approx(expected, rel=2e-13, abs=1e-13)
    assert moments[0] == face_metric(fan, a, b, t)['parameter_depth_integral']
    assert moments == face_depth_moments(fan, b, a, t)
    fraction = F(2, 7)
    middle = tuple(x+fraction*(y-x) for x, y in zip(a, b))
    first, last = face_depth_moments(fan, a, middle, t), face_depth_moments(fan, middle, b, t)
    assert moments == tuple(fraction*x+(1-fraction)*y for x, y in zip(first, last))


def test_actual_depth_gradient_moments_and_connection_match_independent_volume_integrals():
    fan, fragments, time, operator = transport()
    profile = independent_profile(fan, time)
    du, dv = map(lambda x: np.array(list(map(float, operator.divergence(operator.vector(x))))), (U, V))
    expected_work = 0.
    for i, fragment in enumerate(fragments):
        for axis in range(2):
            expected = volume_quad(fragment, profile, lambda x, y, h, ht, grad: h*grad[axis])
            assert float(operator.depth_gradient_moments[i][axis]) == pytest.approx(expected, abs=1e-12)
        ui, vi, adv, bed = map(lambda x: np.array(x, float), (U[i], V[i], ADV[i], fan.gradient))
        def work(x, y, h, ht, grad):
            fu, fv, advh = h*du[i]-1.5*(bed@ui), h*dv[i]-1.5*(bed@vi), grad@adv
            return .5*h*(fv*advh*du[i]-advh*dv[i]*fu)
        expected_work += volume_quad(fragment, profile, work)
    actual = sum(float(a)*float(b) for a, b in zip(operator.vector(V), operator.vector(operator.volume_factor_force(U))))
    assert actual == pytest.approx(expected_work, abs=1e-12)
    assert abs(expected_work) > 1e-6


def test_physical_time_commutator_matches_direct_factor_work_not_volume_only_derivative():
    fan, fragments, time, operator = transport()
    profile = independent_profile(fan, time)
    u, v = operator.vector(U), operator.vector(V)
    du, dv, dtu, dtv = [np.array(list(map(float, values))) for values in
        (operator.divergence(u), operator.divergence(v),
         operator.divergence(u, rate=True), operator.divergence(v, rate=True))]
    expected = 0.
    for i, fragment in enumerate(fragments):
        ui, vi, bed = map(lambda x: np.array(x, float), (U[i], V[i], fan.gradient))
        def work(x, y, h, ht, grad):
            fu, fv = h*du[i]-1.5*(bed@ui), h*dv[i]-1.5*(bed@vi)
            fut, fvt = ht*du[i]+h*dtu[i], ht*dv[i]+h*dtv[i]
            return .5*h*(fv*fut-fvt*fu)
        expected += volume_quad(fragment, profile, work)
    actual = sum(float(a)*float(b) for a, b in zip(v, operator.vector(operator.time_commutator(U))))
    assert actual == pytest.approx(expected, abs=1e-11)
    assert abs(expected) > 1e-6


@pytest.mark.parametrize('method', ('volume_factor_force', 'factor_force', 'difference_force', 'time_commutator'))
def test_original_front_operators_are_exactly_skew_for_distinct_velocities(method):
    _, _, _, operator = transport()
    action = getattr(operator, method)
    u, v = operator.vector(U), operator.vector(V)
    au, av = operator.vector(action(U)), operator.vector(action(V))
    assert sum((a*b for a, b in zip(u, au)), operator.zero) == 0
    assert sum((a*b+c*d for a, b, c, d in zip(v, au, u, av)), operator.zero) == 0
    assert any(x != 0 for x in au)


def test_face_factor_exchange_matches_independent_sextic_profile_integration():
    fan, _, time, operator = transport()
    profile, _, _, _ = independent_profile(fan, time)
    du, dv = [np.array(list(map(float, operator.divergence(operator.vector(x))))) for x in (U, V)]
    u, v, adv, bed = (np.array(x, float) for x in (U, V, ADV, fan.gradient))
    expected = 0.
    for face in operator.faces:
        l, r = face['left'], face['right']
        a, b = (np.array(point[:2], float) for point in (face['first'], face['last']))
        normal = np.array((b[1]-a[1], a[0]-b[0]))
        speed = normal@((adv[l]+adv[r])/2)
        def integrand(s):
            h = profile(a+s*(b-a))[0]
            f = lambda vec, div, i: h*div[i]-1.5*(bed@vec[i])
            paired = f(v, dv, l)*f(u, du, r)-f(v, dv, r)*f(u, du, l)
            paired += .75*((bed@v[l])*(bed@u[r])-(bed@v[r])*(bed@u[l]))
            return .5*h*speed*paired
        # This fixture's shared edge is entirely within one fan branch.
        expected += quad(integrand, 0, 1, epsabs=1e-12)[0]
    force = operator.vector(operator.factor_force(U))
    connection = operator.vector(operator.volume_factor_force(U))
    measured = sum(float(a)*float(b-c) for a, b, c in zip(operator.vector(V), force, connection))
    assert measured == pytest.approx(expected, abs=1e-12)


def test_uniform_depth_on_sloping_bed_has_zero_spatial_connection_not_hydrostatic_one():
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 2, (F(1, 5), -F(1, 7)))
    fragments = (rectangle(x0=-3, x1=-2, bed=2, slope=fan.gradient),)
    operator = FrontAuxiliaryTransport(fan, fragments, F(1, 10), (ADV[0],), outer_boundary='reflecting')
    assert all(x == 0 for x in operator.depth_gradient_moments[0])
    assert all(x == 0 for x in operator.connection[0])
    gram = operator.geometry.forms[0]['gram']
    hydrostatic = tuple(sum((gram[i+1][j+1]*ADV[0][j]/4 for j in range(2)), operator.zero) for i in range(2))
    assert any(x != 0 for x in hydrostatic)


def test_winding_and_hanging_vertices_preserve_front_transport():
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 0, (0, 0))
    fragments = (rectangle(x0=-1, x1=0), rectangle(x0=0, x1=1, y0=-1, y1=0),
                 rectangle(x0=0, x1=1, y0=0, y1=1))
    adv = (ADV[0], ADV[1], ADV[0])
    first = FrontAuxiliaryTransport(fan, fragments, F(1, 5), adv, outer_boundary='reflecting')
    second = FrontAuxiliaryTransport(fan, tuple(replace(f, polygon=tuple(reversed(f.polygon))) for f in fragments),
                                     F(1, 5), adv, outer_boundary='reflecting')
    assert len(first.faces) == 3
    assert first.depth_gradient_moments == second.depth_gradient_moments
    assert first.factor_force(adv) == second.factor_force(adv)
    assert first.difference_force(adv) == second.difference_force(adv)


def test_positive_subfloat_front_support_and_dry_unknown_semantics():
    fan = AffineDryFan((0, 0), (1, 0), F(1, 10**400), (0, 0), 0, (0, 0), gravity=1)
    fragments = (rectangle(x0=-2, x1=-1), rectangle(x0=-1, x1=0), rectangle(x0=1, x1=2))
    operator = FrontAuxiliaryTransport(fan, fragments, F(1, 5), ADV, outer_boundary='reflecting')
    assert operator.geometry.active == (0, 1)
    assert len(operator.faces) == 1
    assert all(x > 0 and float(x) == 0 for x in operator.faces[0]['depth_moments'])
    assert not operator.scope()['mass_or_momentum_closure_or_interacting_fans_or_native_or_gameplay_accepted']
    with pytest.raises(ValueError, match='active original owner'):
        operator.factor_force((*U, (0, 0)))


def test_invalid_profiles_boundaries_and_state_reject():
    fan, fragments, time = fixture()
    with pytest.raises(ValueError, match='reflecting'):
        FrontAuxiliaryTransport(fan, fragments, time, ADV, outer_boundary='open')
    with pytest.raises(ValueError, match='active original owner'):
        FrontAuxiliaryTransport(fan, fragments, time, ((np.nan, 0), ADV[1]), outer_boundary='reflecting')
    with pytest.raises(ValueError, match='affine bed'):
        face_depth_moments(fan, (0, 0, 10), (1, 0, 10), time)


@pytest.mark.parametrize('method', ('factor_force', 'time_commutator'))
def test_direct_local_momentum_ledger_matches_operator_without_residual_defined_bed_force(method):
    _, _, _, operator = transport()
    ledger = getattr(operator, method+'_ledger')(U)
    assert ledger.action() == getattr(operator, method)(U)
    assert ledger.faces
    assert any(x != 0 for row in ledger.bed for x in row)
    assert any(x != 0 for row in ledger.wall for x in row)
    for axis in range(2):
        assert sum((row[axis] for row in ledger.action()), operator.zero) == sum(
            (bed[axis]+wall[axis] for bed, wall in zip(ledger.bed, ledger.wall)), operator.zero)


@pytest.mark.parametrize('method', ('factor_force', 'time_commutator'))
def test_flat_front_has_no_spurious_bed_term_in_direct_ledger(method):
    fan = AffineDryFan((0, 0), (3, 4), 1, (F(1, 3), -F(1, 7)), 0, (0, 0))
    fragments = (rectangle(x0=-1, x1=0), rectangle(x0=0, x1=1))
    operator = FrontAuxiliaryTransport(fan, fragments, F(1, 5), ADV, outer_boundary='reflecting')
    ledger = getattr(operator, method+'_ledger')(U)
    assert ledger.action() == getattr(operator, method)(U)
    assert all(x == 0 for row in ledger.bed for x in row)


def test_wholly_dry_source_has_no_force_unknown_or_fabricated_dry_velocity():
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 0, (0, 0))
    operator = FrontAuxiliaryTransport(fan, (rectangle(x0=5, x1=6),), F(1, 10), (), outer_boundary='reflecting')
    assert operator.geometry.active == () and operator.faces == []
    for method in ('factor_force', 'difference_force', 'volume_factor_force', 'time_commutator'):
        assert getattr(operator, method)(()) == ()
    for method in ('factor_force_ledger', 'time_commutator_ledger'):
        assert getattr(operator, method)(()).action() == ()
