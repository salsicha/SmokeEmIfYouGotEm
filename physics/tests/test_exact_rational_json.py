from fractions import Fraction as F
import json
import sys

import pytest
from exact_rational_json import encode_fraction, decode_fraction, json_default


@pytest.mark.parametrize('value', [F(0), F(1,3), F(-71,19), F(10**6000+1, 10**7000+3),
                                  F(-10**6000-1, 10**7000+3), F(1,10**10000)])
def test_json_round_trip_preserves_every_bit_without_guard_change(value):
    limit = sys.get_int_max_str_digits()
    encoded = json.loads(json.dumps(value, default=json_default, allow_nan=False))
    assert decode_fraction(encoded) == value
    assert sys.get_int_max_str_digits() == limit
    if abs(value.numerator).bit_length() < 100 and value.denominator.bit_length() < 100:
        assert encoded == str(value)
    elif limit and max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > 4*limit:
        assert set(encoded) == {'fraction_hex'}


@pytest.mark.parametrize('value', [1., {}, {'fraction_hex': ['0x1','0x0']},
    {'fraction_hex': ['0x1','-0x1']}, {'fraction_hex': ['1','0x2']},
    {'fraction_hex': [1,'0x2']}, {'fraction_hex': ['0x1']},
    {'fraction_hex': ['0x1','0x2'], 'ignored': True}])
def test_invalid_exact_encodings_rejected(value):
    with pytest.raises(ValueError):
        decode_fraction(value)


def test_unrecognized_values_are_not_silently_stringified():
    with pytest.raises(TypeError):
        encode_fraction(1.)
    with pytest.raises(TypeError):
        json.dumps(object(), default=json_default)
