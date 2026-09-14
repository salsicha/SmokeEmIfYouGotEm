import struct
import numpy as np
from export_reconstructed_polynomial_fixture import encode_case, range_record
from test_reconstructed_polynomial_sweep_reference import system
from reconstructed_damped_polynomial_reference import DampedPolynomialSystem
from diagnose_reconstructed_pressure_convergence import assembled_matrix


def test_fixture_preserves_binary_doubles_and_original_action():
    original = system()
    rhs = np.random.default_rng(718).normal(size=(*original.h.shape, 2))
    payload, info = encode_case(original, rhs, 4)
    n, nnz, degree, tag, omega = struct.unpack_from('<IIIId', payload)
    assert (n, nnz, degree, tag) == (rhs.size, assembled_matrix(original).nnz, 1, 4)
    offset = 24
    def read(count, dtype):
        nonlocal offset
        values = np.frombuffer(payload, dtype=dtype, count=count, offset=offset)
        offset += values.nbytes
        return values
    rows, columns = read(n+1, '<u4'), read(nnz, '<u4')
    matrix, scaled = read(nnz, '<f8'), read(nnz, '<f8')
    inverse, vector, action, precondition, action_scale, precondition_scale = [read(n, '<f8') for _ in range(6)]
    assert offset == len(payload)
    np.testing.assert_array_equal(vector, rhs.ravel())
    np.testing.assert_array_equal(action, original.apply(rhs).ravel())
    np.testing.assert_array_equal(precondition, DampedPolynomialSystem(original, 1).precondition(rhs).ravel())
    for i in range(n):
        begin, end = rows[i:i+2]; col = columns[begin:end]
        expected_action = np.sum(matrix[begin:end]*vector[col])
        expected_precondition = omega*inverse[i]*(2*inverse[i]*vector[i]
            -omega*np.sum(scaled[begin:end]*inverse[col]*vector[col]))
        assert abs(action[i]-expected_action) <= 128*np.finfo(float).eps*action_scale[i]
        assert abs(precondition[i]-expected_precondition) <= 128*np.finfo(float).eps*precondition_scale[i]
    assert info['original_action_assembly_relative_error'] < 1e-12


def test_range_diagnostic_reports_loss_without_changing_input():
    values = np.array([0., 1e-150, -1e-80, 1., 1e40]); before = values.copy()
    result = range_record(values)
    assert result['fp32_lost_nonzero'] == 2 and result['fp32_nonfinite'] == 1
    assert result['minimum_nonzero'] == 1e-150
    np.testing.assert_array_equal(values, before)
