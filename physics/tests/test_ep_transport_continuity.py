"""Regression for a value jump in EP's wide-extremum branch selection.

The published slope formula can pass spatial refinement yet remain unsuitable
for this coupled time-evolving model. Do not xfail or weaken this test.
"""
from fractions import Fraction as F
import numpy as np
from extremum_preserving_transport import ep_slope,exact_slope,ExtremumPreservingTransport


def fixture(t):
    return [F(1),1+t,F(9,8)+t,3+t,6+t]


def test_formula_and_rational_oracle_agree_on_both_sides():
    for exponent in (20,24,28):
        eps=F(1,2**exponent)
        for t,expected in ((eps,F(1,4)),(-eps,F(15,64)+F(15,8)*eps)):
            values=fixture(t);h=np.array([[float(v) for v in values]])
            assert exact_slope(values)==expected
            assert ep_slope(h,1)[0,2]==float(expected)


def test_ep_slope_is_continuous_at_wide_extremum_switch():
    gaps=[]
    for exponent in (20,24):
        eps=F(1,2**exponent)
        values=[exact_slope(fixture(t)) for t in (-eps,eps)]
        gaps.append(abs(values[1]-values[0]))
    # A 16x smaller perturbation must shrink the value gap, not leave a
    # nonzero 1/64 jump. This generous ratio avoids demanding asymptotic 16.
    assert gaps[0]/gaps[1]>8


def test_positive_donor_face_flux_is_continuous_on_same_states():
    gaps=[]
    for exponent in (20,24):
        eps=F(1,2**exponent);flux=[]
        for t in (-eps,eps):
            h=np.array([[float(v) for v in fixture(t)]]);b=np.zeros_like(h)
            u=np.ones((*h.shape,2));transport=ExtremumPreservingTransport(h,b,u,1.,periodic=True)
            flux.append(transport.faces[0]['flux'][0,2])
        gaps.append(abs(flux[1]-flux[0]))
    assert gaps[0]/gaps[1]>8
