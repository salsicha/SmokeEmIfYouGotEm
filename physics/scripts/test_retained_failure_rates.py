import numpy as np
import pytest
import audit_retained_failure_rates as audit


def test_acceleration_separates_mass_transport_and_pressure_without_floor():
    stage = dict(state=np.array([[[.02, .06, -.04, 0]]]),
        rate=np.array([[[.01, .04, .06, 0]]]), force=np.array([[[.1, -.2]]]),
        fraction=np.ones((1, 1)), pairs=np.zeros((1, 1), dtype=np.uint32))
    row = audit.cell_rates(stage, (0, 0))
    np.testing.assert_allclose(row['velocity_mps'], [3, -2])
    np.testing.assert_allclose(row['hydro_acceleration_mps2'], [.5, 4])
    np.testing.assert_allclose(row['pressure_acceleration_mps2'], [5, -10])
    stage['state'] *= 1e-30; stage['rate'] *= 1e-30; stage['force'] *= 1e-30
    tiny = audit.cell_rates(stage, (0, 0))
    np.testing.assert_allclose(tiny['hydro_acceleration_mps2'], [.5, 4])
    np.testing.assert_allclose(tiny['pressure_acceleration_mps2'], [5, -10])


def test_dry_acceleration_is_undefined_not_repaired():
    stage = dict(state=np.zeros((1, 1, 4)), rate=np.zeros((1, 1, 4)),
        force=np.zeros((1, 1, 2)), fraction=np.zeros((1, 1)), pairs=np.zeros((1, 1), dtype=np.uint32))
    row = audit.cell_rates(stage, (0, 0))
    assert row['hydro_acceleration_mps2'] is None and row['pressure_acceleration_mps2'] is None


@pytest.mark.parametrize('state', [[-1, 0, 0, 0], [0, 1, 0, 0], [1, np.inf, 0, 0]])
def test_invalid_state_rejected(state):
    with pytest.raises(ValueError, match='wet/dry'):
        audit.velocity(state)


@pytest.mark.parametrize('missing', ['completed', 'final_state_exact_to_live', 'source_evolution_failed', 'retained_failure_exact'])
def test_unqualified_capture_rejected_before_reading(missing):
    metadata = dict(completed=True, final_state_exact_to_live=True,
        source_evolution_failed=True, retained_failure_exact=True)
    metadata[missing] = False
    with pytest.raises(ValueError, match='retained-failure'):
        audit.analyze(metadata, b'', dict(summary=[1, 0, 2, 5], failure='failed'), [(22, 102)])
