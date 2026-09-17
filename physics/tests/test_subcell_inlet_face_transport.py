from dataclasses import replace
from fractions import Fraction as F
from math import comb

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_exact_geometry import SourceFragment, clip
from subcell_inlet_face_transport import face_transport, source_transport_balance
from subcell_inlet_sweep_geometry import InletSweep
from test_subcell_inlet_sweep_geometry import fixture


def split(receiver, cut):
    return [SourceFragment(i, clip(receiver.polygon, 0, cut, side), receiver.gradient)
            for i, side in enumerate((False, True))]


def cut_face(fragment, cut):
    return next(i for i, (a, b) in enumerate(zip(fragment.polygon, fragment.polygon[1:]+fragment.polygon[:1]))
                if a[0] == b[0] == cut and a != b)


def test_full_receiver_birth_flux_equals_independent_exact_moments():
    sweep, receiver = fixture()
    result = source_transport_balance(sweep, receiver)
    incoming = result['faces'][2]
    assert incoming['original_edge_xyz'] == (receiver.polygon[2], receiver.polygon[0])
    assert incoming['lower'] == incoming['upper'] == tuple(-sweep.full_moment(p) for p in range(4))
    assert result['balance_lower'] == result['balance_upper'] == (F(0),)*4
    assert not result['pressure_or_bed_force_or_coupled_step_accepted']


@pytest.mark.parametrize('cut', [F(7, 256), F(3, 200)])
def test_crossed_source_face_conserves_storage_and_shared_flux(cut):
    sweep, receiver = fixture()
    pieces = split(receiver, cut)
    balances = [source_transport_balance(sweep, piece) for piece in pieces]
    faces = [balance['faces'][cut_face(piece, cut)] for piece, balance in zip(pieces, balances)]
    assert faces[0]['lower'] == tuple(-x for x in faces[1]['upper'])
    assert faces[0]['upper'] == tuple(-x for x in faces[1]['lower'])
    assert faces[0]['lower'][1] > 0
    r = float(sweep.time_root**3-cut/sweep.velocity[0])**(1/3)
    for p in range(4):
        expected = float(sweep.full_moment(p))*(r/float(sweep.time_root))**(p+4)
        observed = float((faces[0]['lower'][p]+faces[0]['upper'][p])/2)
        np.testing.assert_allclose(observed, expected, rtol=1e-12)
        for balance in balances:
            assert balance['balance_lower'][p] <= 0 <= balance['balance_upper'][p]
            assert balance['maximum_relative_balance_width'] < F(1, 10**10)


def test_oblique_face_matches_independent_eulerian_time_integral():
    sweep, _ = fixture()
    # Downstream region above x+y=1/8; its first edge has inward flux.
    polygon = tuple(tuple(map(F, p)) for p in
                    ((F(1,8),0,F(75,8)), (0,F(1,8),F(81,8)), (0,1,11), (1,1,6), (1,0,5)))
    fragment = SourceFragment(80, polygon, (F(-5), F(1)))
    result = face_transport(sweep, fragment, 0)
    assert result['outward_direction'] == -1
    # Independently integrate h(t,x,y)=(t-x/2)^(1/3)-y at fixed XY on
    # the face. Time integration has a closed primitive; only lambda is quad.
    for p in range(4):
        def along_face(lam):
            x, y = (1-lam)/8, lam/8
            high, low = 1/64-x/2, y**3
            if high <= low:
                return 0.
            return .25*sum(comb(p,j)*(-y)**(p-j)*3/(j+3)*
                            (high**((j+3)/3)-low**((j+3)/3)) for j in range(p+1))
        expected = quad(along_face, 0, 1, epsabs=1e-19, epsrel=1e-11, limit=200)[0]
        observed = -float((result['lower'][p]+result['upper'][p])/2)
        np.testing.assert_allclose(observed, expected, rtol=1e-9, atol=1e-17)
    assert source_transport_balance(sweep, fragment)['conditional_advective_balance_bounded']


def test_original_orientation_translation_and_velocity_sign_do_not_change_outward_flux():
    sweep, receiver = fixture()
    piece = split(receiver, F(3,200))[0]
    before = source_transport_balance(sweep, piece)
    move = lambda p: (p[0]+F(10**12), -p[1]-F(10**12), p[2])
    reflected = replace(sweep, edge=tuple(move(p) for p in sweep.edge),
                        velocity=(sweep.velocity[0], -sweep.velocity[1]))
    moved = SourceFragment(piece.source_id, tuple(move(p) for p in reversed(piece.polygon)),
                           (piece.gradient[0], -piece.gradient[1]))
    after = source_transport_balance(reflected, moved)
    assert after['balance_lower'] == before['balance_lower']
    assert after['balance_upper'] == before['balance_upper']
    assert sorted(f['lower'] for f in after['faces']) == sorted(f['lower'] for f in before['faces'])


def test_segment_subdivision_preserves_crossing_flux_without_double_counting():
    sweep, receiver = fixture()
    piece = split(receiver, F(3,200))[0]
    index = cut_face(piece, F(3,200))
    a, b = piece.polygon[index], piece.polygon[(index+1) % len(piece.polygon)]
    midpoint = tuple((x+y)/2 for x, y in zip(a,b))
    divided = replace(piece, polygon=piece.polygon[:index+1]+(midpoint,)+piece.polygon[index+1:])
    whole = face_transport(sweep, piece, index)
    halves = [face_transport(sweep, divided, i) for i in (index, index+1)]
    for p in range(4):
        lo, hi = (sum(h[key][p] for h in halves) for key in ('lower', 'upper'))
        assert lo <= whole['upper'][p] and hi >= whole['lower'][p]
        assert hi-lo < F(1,10**10)*sweep.full_moment(p)


def test_zero_transverse_flux_and_face_not_reached_stay_exactly_zero():
    sweep, receiver = fixture()
    assert face_transport(sweep, receiver, 0)['lower'] == (F(0),)*4  # parallel velocity
    piece = split(receiver, F(1,2))[0]
    result = face_transport(sweep, piece, cut_face(piece,F(1,2)))
    assert result['lower'] == result['upper'] == (F(0),)*4


def test_positive_sub_float_inlet_flux_is_retained():
    sweep, receiver = fixture()
    tiny = InletSweep(sweep.edge, (F(1,10**126),0), 1, F(1,10**255))
    result = face_transport(tiny, receiver, 2)
    assert result['upper'][1] < 0 and float(result['upper'][1]) == 0.
    assert result['lower'] == result['upper'] == tuple(-tiny.full_moment(p) for p in range(4))


def test_upstream_donor_is_not_misclassified_as_empty_receiver():
    sweep, _ = fixture()
    donor = SourceFragment(81, tuple(tuple(map(F,p)) for p in ((0,0,10),(0,2,12),(-2,0,10))), (F(0),F(1)))
    with pytest.raises(ValueError, match='does not close'):
        source_transport_balance(sweep, donor)
    debit = source_transport_balance(sweep, donor, birth_donor=True)
    assert debit['original_inlet_withdrawal'] == tuple(sweep.full_moment(p) for p in range(4))
    assert debit['advected_moment_change_lower'] == tuple(-sweep.full_moment(p) for p in range(4))
    assert debit['balance_lower'] == debit['balance_upper'] == (F(0),)*4
    _, receiver = fixture()
    with pytest.raises(ValueError, match='does not enter'):
        source_transport_balance(sweep, receiver, birth_donor=True)
    with pytest.raises(ValueError, match='boolean'):
        source_transport_balance(sweep, donor, birth_donor='yes')


def test_unresolved_integration_and_invalid_face_are_not_accepted():
    sweep, receiver = fixture()
    piece = split(receiver,F(3,200))[0]
    with pytest.raises(ValueError, match='bound unresolved'):
        face_transport(sweep,piece,cut_face(piece,F(3,200)),max_depth=1)
    for index in (-1, len(piece.polygon), True):
        with pytest.raises(ValueError, match='edge index'):
            face_transport(sweep,piece,index)
    with pytest.raises(ValueError, match='relative integration bound'):
        face_transport(sweep,receiver,0,relative_bound=1)


def test_zero_measure_polynomial_contact_differs_from_identically_zero_constraint():
    sweep, _ = fixture()
    lower, upper = [(F(0),)], [(F(0), sweep.height_scale/sweep.bed_span)]
    # -(r-R/2)^2 touches zero at one exact interior point only.
    middle = sweep.time_root/2
    result = sweep._constraint_moments(lower, upper, [(-middle**2, 2*middle, F(-1))])
    assert result['lower'] == result['upper'] == (F(0),)*4
    free = sweep._constraint_moments(lower, upper, [(F(0),)])
    assert free['lower'] == free['upper'] == tuple(sweep.full_moment(p) for p in range(4))
