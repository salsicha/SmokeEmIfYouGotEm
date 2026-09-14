import numpy as np
from export_scaled_hydrostatic_fixtures import expected, cases
from export_exact_hydrostatic_fixtures import expected as unscaled_expected


def test_zero_and_one_factors_retain_original_exact_reference():
    for _, values in list(cases())[:40]:
        for left, right in ((0, 0), (0, 1), (1, 0), (1, 1)):
            rows = values.copy(); rows[0, 3] = left; rows[2, 3] = right
            assert expected(rows) == unscaled_expected(rows)


def test_scaled_offset_below_minimum_subnormal_keeps_exact_wet_sign():
    tiny = 2.**-149
    # One exact half-slope times the smallest factor remains nonzero even
    # though the hydrostatic reduced depth cannot be stored as a nonzero FP32.
    rows = np.asarray([(tiny, 2*tiny, 3*tiny, tiny), (0, 0, 0, 1),
        (tiny, tiny, tiny, 0), (2*tiny, 2*tiny, 2*tiny, -1)], dtype=np.float32)
    result = expected(rows)
    assert result[2] == 0 and result[4] == 1


def test_fixture_factors_and_inputs_are_representable_finite_values():
    records = list(cases())
    assert len(records) == 4317
    for name, rows in records:
        assert rows.shape == (4, 4) and rows.dtype == np.float32
        assert np.isfinite(rows).all()
        assert 0 <= rows[0, 3] <= 1 and 0 <= rows[2, 3] <= 1
        assert np.min(rows[[0, 2], :3]) >= 0
