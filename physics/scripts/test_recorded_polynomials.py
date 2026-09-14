from fractions import Fraction
import numpy as np
import pytest
from diagnose_recorded_polynomials import exact_slopes, exact_face


@pytest.mark.parametrize('axis', [0, 1])
def test_exact_lake_has_zero_surface_slope_and_equal_face_depths(axis):
    bed = np.broadcast_to(np.arange(5, dtype=float)/8, (5, 5)).copy()
    if axis == 0: bed = bed.T.copy()
    h = 2-bed
    dh, de = exact_slopes(h, bed, 2, 2, axis)
    assert dh == Fraction(-1, 8) and de == 0
    assert exact_face(h, bed, 2, 2, axis, 1) == exact_face(h, bed, *( (3, 2) if axis == 0 else (2, 3)), axis, -1)


def test_one_sided_mc_retains_tiny_positive_neighbor_without_a_floor():
    h = np.array([[0, 2**-40, 1., 4., 5.]]*3, dtype=np.float32)
    bed = np.zeros_like(h)
    dh, de = exact_slopes(h, bed, 1, 2, 1)
    assert dh == de == 2*(1-Fraction(1, 2**40))
    assert exact_face(h, bed, 1, 2, 1, -1) == Fraction(1, 2**40)


def test_dry_stencil_zeroes_polynomial_and_step_blocks_face():
    h = np.array([[0., 1., 4.]])
    bed = np.array([[0., 0., 2.]])
    assert exact_slopes(h, bed, 0, 1, 1) == (0, 0)
    assert exact_face(h, bed, 0, 1, 1, 1) == 0
