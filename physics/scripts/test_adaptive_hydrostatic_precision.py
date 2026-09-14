from fractions import Fraction
import numpy as np
import pytest
from total_depth_bank_replay import mc, hydrostatic_faces, rate
from diagnose_recorded_polynomials import exact_face


def reconstruct(h, bed, axis, *, periodic=False, exterior=None, final=False):
    wet = (h > 0) & (np.roll(h, 1, axis) > 0) & (np.roll(h, -1, axis) > 0)
    dh = mc(h, axis, periodic)*wet
    de = mc(h, axis, periodic, other=bed)*wet
    result = hydrostatic_faces(h, bed, dh, de, axis, periodic, exterior, reconstruction=True)
    if final:
        left, right = result[-2:]
        partial = (h > 0) & ((np.take(left, range(1, left.shape[axis]), axis) == 0)
            | (np.take(right, range(right.shape[axis]-1), axis) == 0))
        dh[partial] = 0; de[partial] = 0
        result = hydrostatic_faces(h, bed, dh, de, axis, periodic, exterior,
                                  reconstruction=True, flattened=partial)
    return result


@pytest.mark.parametrize('axis', [0, 1])
def test_actual_stalled_neighbor_face_is_minimum_normal_not_spurious_inflow(axis):
    # Full x stencil from recorded owner y79/x84:93. The asserted face is
    # interior, so crop boundaries cannot affect its raw or flattening stencil.
    h = np.array([[1.0842406277813098e-14, 1.004714737242677e-14,
        2.0239537946008736e-18, 5.070144828202847e-15,
        1.1754943508222875e-38, 1.7662518669858684e-10,
        2.0119331201051693e-10, .000185041906661354, .012292633764445782]])
    bed = np.array([[9.480026245117188, 9.602409362792969, 9.72479248046875,
        9.709053039550781, 9.693313598632812, 9.532882690429688,
        9.372451782226562, 9.209548950195312, 9.046646118164062]])
    if axis == 0: h, bed = h.T.copy(), bed.T.copy()
    point = (3, 0) if axis == 0 else (0, 3)
    index = (4, 0) if axis == 0 else (0, 4)
    expected = Fraction(1, 2**126)
    assert exact_face(h, bed, *point, axis, 1, final=True) == expected
    original_h, original_bed = h.copy(), bed.copy()
    result = reconstruct(h, bed, axis, final=True)
    assert result[-2][index] == float(expected)
    np.testing.assert_array_equal(h, original_h)
    np.testing.assert_array_equal(bed, original_bed)


@pytest.mark.parametrize('tiny', [2.**-40, 2.**-126, 2.**-300])
@pytest.mark.parametrize('periodic', [False, True])
def test_one_sided_mc_preserves_represented_neighbor_without_floor(tiny, periodic):
    h = np.array([[1., 0., tiny, 1., 4., 5., 2.]])
    bed = np.zeros_like(h)
    result = reconstruct(h, bed, 1, periodic=periodic)
    assert result[0][0, 3] == tiny
    assert result[3][0, 3] == tiny
    assert result[5][0, 3] == tiny
    assert result[4][0, 3] == tiny


@pytest.mark.parametrize('axis', [0, 1])
@pytest.mark.parametrize('final', [False, True])
def test_random_interior_faces_agree_with_independent_exact_oracle(axis, final):
    rng = np.random.default_rng(37613)
    h = np.exp2(rng.integers(-300, 4, (9, 13))).astype(float)
    bed = rng.integers(-10, 10, h.shape)/8
    h[rng.random(h.shape) < .08] = 0
    result = reconstruct(h, bed, axis, final=final)
    for y in range(2, h.shape[0]-2):
        for x in range(2, h.shape[1]-2):
            for direction in (-1, 1):
                index = [y, x]; index[axis] += int(direction > 0)
                actual = result[-2 if direction > 0 else -1][tuple(index)]
                expected = float(exact_face(h, bed, y, x, axis, direction, final=final))
                assert actual == pytest.approx(expected, rel=1e-13, abs=0)


def test_periodic_translation_and_axis_transpose_preserve_corrected_rate():
    h = np.array([[2.**-126, 1., 4., 5., 2., 2.**-80, .5]])
    state = np.stack((h, 2*h, -.5*h), -1); bed = np.zeros_like(h)
    before = state.copy()
    value, dt = rate(state, bed, .5, second_order=True, periodic=True)
    shifted, shifted_dt = rate(np.roll(state, 3, axis=1), bed, .5, second_order=True, periodic=True)
    np.testing.assert_array_equal(shifted, np.roll(value, 3, axis=1)); assert shifted_dt == dt
    other, other_dt = rate(state.transpose(1, 0, 2)[..., [0, 2, 1]], bed.T, .5, second_order=True, periodic=True)
    np.testing.assert_allclose(other, value.transpose(1, 0, 2)[..., [0, 2, 1]], rtol=1e-14, atol=0)
    assert other_dt == dt
    np.testing.assert_array_equal(state, before)


@pytest.mark.parametrize('axis', [0, 1])
@pytest.mark.parametrize('second_order', [False, True])
def test_constant_explicit_ghosts_preserve_tiny_faces_and_datum(axis, second_order):
    h = np.full((3, 5), 2.**-126); bed = np.full_like(h, 16.)
    es = np.zeros((16, 4)); es[:, 0] = h[0, 0]; eb = np.full(16, 16.)
    result = hydrostatic_faces(h, bed, h*0, h*0, axis, False, (es, eb), reconstruction=second_order)
    translated = hydrostatic_faces(h, bed+1024, h*0, h*0, axis, False,
        (es, eb+1024), reconstruction=second_order)
    for value, shifted in zip(result, translated):
        np.testing.assert_array_equal(value, shifted)
        np.testing.assert_array_equal(value, np.full_like(value, h[0, 0]))


def test_precision_fallback_preserves_closed_box_mass_without_state_repair():
    h = np.array([[2.**-126, 1., 4., 5., 2., 2.**-80, .5]])
    state = np.stack((h, 2*h, -.5*h), -1)
    result, _ = rate(state, np.zeros_like(h), .5, second_order=True)
    assert abs(result[..., 0].sum()) < 1e-12
