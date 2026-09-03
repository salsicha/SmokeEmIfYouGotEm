"""Cross-river cooked free-surface reconstruction limiter tests."""

import numpy as np

from raftsim.cooked_flow_fields import apply_monotone_surface_shock_limiter


def _fields(eta: np.ndarray) -> dict[str, np.ndarray]:
    bed = np.zeros_like(eta, dtype=np.float32)
    return {
        "h": eta.astype(np.float32),
        "u": np.full_like(eta, 2.0, dtype=np.float32),
        "v": np.full_like(eta, 0.25, dtype=np.float32),
        "bed": bed,
        "wet_mask": np.ones_like(eta, dtype=np.uint8),
    }


def test_limiter_removes_isolated_pit_and_preserves_cell_discharge():
    eta = np.ones((7, 7), dtype=np.float32)
    eta[3, 3] = 0.2
    limited, diagnostics = apply_monotone_surface_shock_limiter(_fields(eta))

    assert limited["h"][3, 3] == np.float32(0.82)
    assert diagnostics["limited_cell_count"] == 1
    assert np.isclose(limited["h"][3, 3] * limited["u"][3, 3], 0.4)
    assert np.isclose(limited["h"][3, 3] * limited["v"][3, 3], 0.05)


def test_limiter_preserves_resolved_hydraulic_jump_and_dry_bank():
    eta = np.ones((7, 7), dtype=np.float32)
    eta[:, 4:] = 0.25
    fields = _fields(eta)
    fields["wet_mask"][0, :] = 0
    fields["h"][0, :] = 0.0
    limited, diagnostics = apply_monotone_surface_shock_limiter(fields)

    np.testing.assert_array_equal(limited["h"], fields["h"])
    np.testing.assert_array_equal(limited["wet_mask"], fields["wet_mask"])
    assert diagnostics["limited_cell_count"] == 0
