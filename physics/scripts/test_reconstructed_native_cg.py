import struct
import numpy as np
import pytest
from audit_reconstructed_native_cg import read_native, compare
from test_reconstructed_polynomial_sweep_reference import system
from reconstructed_damped_polynomial_reference import DampedPolynomialSystem


def fixture():
    data = struct.pack('<III', 0x52534347, 1, 6)
    for tag in range(6):
        data += struct.pack('<IIIIIId', tag, 2, 0, 40, 1, 0, 2.5)
        data += np.array([1e-150, -2.5, 1e-150, -2.5], dtype='<f8').tobytes()
    return data


def test_native_parser_preserves_small_double_values():
    values = read_native(fixture())
    assert len(values) == 6 and values[5]['iterations'] == 40
    np.testing.assert_array_equal(values[4]['gpu'], [1e-150, -2.5])
    assert not values[0]['gpu'].flags.writeable


@pytest.mark.parametrize('mutation', [lambda x: x[:-1], lambda x: x+b'x', lambda x: b'x'+x[1:],
    lambda x: x[:16]+struct.pack('<I', 524289)+x[20:],
    lambda x: x[:24]+struct.pack('<I', 41)+x[28:],
    lambda x: x[:44]+struct.pack('<d', float('nan'))+x[52:]])
def test_invalid_native_data_rejected(mutation):
    with pytest.raises(ValueError): read_native(mutation(fixture()))


def test_original_operator_verification_retains_failure_and_input():
    original = system(); rhs = np.random.default_rng(889).normal(size=(*original.h.shape, 2))
    before = rhs.copy(); value, _ = DampedPolynomialSystem(original, 1).solve(rhs)
    record = dict(gpu=value.ravel(), cpu=value.ravel(), failures=0, iterations=40)
    good = compare(original, rhs, record)
    assert good['passed']
    bad = compare(original, rhs, dict(record, gpu=np.zeros(rhs.size)))
    assert not bad['passed'] and bad['backends']['gpu']['original_factored_true_relative_residual'] == pytest.approx(1.)
    assert not compare(original, rhs, dict(record, failures=1))['passed']
    np.testing.assert_array_equal(rhs, before)
