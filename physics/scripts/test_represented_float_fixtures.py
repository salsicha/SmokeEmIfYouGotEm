from fractions import Fraction
import struct
import numpy as np
import pytest
from export_represented_float_fixtures import rounded_bits, cases, rk2_cases, valid_state, divided_bits, division_cases, sqrt_bits, sqrt_cases, product_bits, product_cases


def bits(value): return struct.unpack('<I', struct.pack('<f', value))[0]


@pytest.mark.parametrize('value,expected', [(Fraction(1,2**150),0),
    (Fraction(3,2**150),2), (Fraction(5,2**150),2), (Fraction(-3,2**150),0x80000002),
    (Fraction(1,2**126)-Fraction(1,2**150),0x800000),
    (Fraction(1,2**126)-Fraction(1,2**149),0x7fffff),
    (Fraction(2**128),0x7f800000)])
def test_exact_binary32_rounding_ties_and_range(value, expected):
    assert rounded_bits(value) == expected


def test_random_finite_binary32_values_roundtrip():
    rng = np.random.default_rng(9813)
    raw = rng.integers(1, 0x7f800000, 10000, dtype=np.uint32)
    for b, value in zip(raw, raw.view(np.float32)):
        assert rounded_bits(Fraction(float(value))) == b
        assert rounded_bits(-Fraction(float(value))) == b | 0x80000000


def test_actual_euler_depth_is_representable_subnormal_not_zero():
    name, values = next(cases()); assert name == 'captured_depth'
    s, dt, rate = map(Fraction, values)
    assert rounded_bits(s+dt*rate) == 0x7fffff


def test_fixtures_detect_double_rounding_not_just_underflow():
    count = 0
    for name, values in cases():
        if not name.startswith('double_rounding'): continue
        s, dt, r = values
        exact = rounded_bits(Fraction(s)+Fraction(dt)*Fraction(r))
        ordinary_double = bits(s+dt*r)
        assert exact != ordinary_double
        count += 1
    assert count == 4


def test_rk2_cancellation_retains_third_term_at_full_represented_range():
    count = 0
    for name, values in rk2_cases():
        if not name.startswith('deep_cancellation'): continue
        s, t, dt, r = map(Fraction, values)
        exact = rounded_bits((s+t+dt*r)/2)
        assert exact & 0x7fffffff != 0
        assert bits(.5*(float(s)+float(t)+float(dt)*float(r))) == 0
        count += 1
    assert count == 24


def test_state_admissibility_uses_represented_water_and_finite_velocity():
    tiny = 2.**-149
    assert valid_state([tiny,4*tiny,-tiny,tiny])
    assert not valid_state([0,tiny,0,0])
    assert not valid_state([tiny,1,0,0])
    assert not valid_state([tiny,0,0,-tiny])
    assert not valid_state([-tiny,0,0,0])
    assert valid_state([1,float(np.finfo(np.float32).max),0,0])


@pytest.mark.parametrize('n,d,expected',[(2.**-149,2.,0),(3*2.**-149,2.,2),
    (5*2.**-149,2.,2),(2.**-126-2.**-149,1.,0x7fffff),
    (-0.,2.,0x80000000),(1.,-0.,0xff800000),(0.,0.,0x7fc00000),
    (np.inf,np.inf,0x7fc00000),(1.,-np.inf,0x80000000)])
def test_division_reference_rounds_ties_and_preserves_signed_special_values(n,d,expected):
    assert divided_bits(n,d)==expected


def test_actual_captured_velocity_divides_positive_subnormal_depth():
    name,(n,d,_,_)=next(division_cases())
    assert name=='captured_velocity'
    assert divided_bits(n,d)==bits(n/d)
    assert 4 < n/d < 5


def test_sqrt_reference_preserves_range_and_ieee_special_values():
    assert sqrt_bits(-0.)==0x80000000
    assert sqrt_bits(-1.)==sqrt_bits(-np.inf)==sqrt_bits(np.nan)==0x7fc00000
    assert sqrt_bits(np.inf)==0x7f800000
    assert sqrt_bits(4.)==bits(2.)
    for name,(value,_,_,_) in sqrt_cases():
        if value>0 and np.isfinite(value):
            assert sqrt_bits(value)==bits(np.sqrt(float(value)))


@pytest.mark.parametrize('a,b,expected',[(2.**-149,.5,0),(3*2.**-149,.5,2),
    (5*2.**-149,.5,2),(-3*2.**-149,.5,0x80000002),
    (2.**-126-2.**-149,1.,0x7fffff),(-0.,1.,0x80000000),(-0.,-1.,0),
    (np.inf,1.,0x7fc00000),(0.,np.inf,0x7fc00000),(np.nan,0.,0x7fc00000)])
def test_product_reference_preserves_ties_signed_zero_and_invalid_inputs(a,b,expected):
    assert product_bits(a,b)==expected


def test_product_rational_oracle_agrees_with_exact_double_product_then_single_round():
    # Two binary32 significands need at most48 bits, so their finite product is
    # exact in binary64. This independent storage-rounding control covers all
    # supplied finite fixture products, including underflow and overflow.
    count=0
    with np.errstate(over='ignore',under='ignore',invalid='ignore'):
        for _,(a,b,_,_) in product_cases():
            if np.isfinite(a) and np.isfinite(b):
                assert product_bits(a,b)==bits(np.float32(np.float64(a)*np.float64(b)))
            count+=1
    assert count==34875
