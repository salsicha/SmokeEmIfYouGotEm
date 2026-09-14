import numpy as np
import pytest
from audit_nonlinear_detail_inputs import analyze


def test_nonlinear_inputs_are_not_silently_admitted_or_clipped():
    flow = np.zeros((5, 5, 4)); flow[..., 0] = 1.5; flow[..., 1] = .4
    state = np.zeros_like(flow); state[..., 0] = .5; state[..., 1] = .3
    result = analyze(flow, state, .5)
    assert result['nonlinear_migration_admissible'] is None
    assert result['cfl_verified_for_future_stages'] is False
    assert result['maximum_mean_strain_source_m2s2'] == 0
    assert result['interior_gradient_cells'] == 9
    state[2, 2, 0] = -2
    result = analyze(flow, state, .5)
    assert result['nonpositive_total_depth_cells'] == 1
    assert result['nonlinear_migration_admissible'] is False
    assert state[2, 2, 0] == -2


def test_empty_shore_gradient_is_unavailable_not_zero_evidence():
    flow = np.zeros((3, 3, 4)); flow[1, 1, 0] = 1
    result = analyze(flow, np.zeros_like(flow), .5)
    assert result['interior_gradient_cells'] == 0
    assert result['maximum_mean_strain_source_m2s2'] is None
    with pytest.raises(ValueError):
        analyze(np.zeros_like(flow), np.zeros_like(flow), .5)
