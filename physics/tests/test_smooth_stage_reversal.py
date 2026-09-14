"""Retained flow-reversal and reflection failures; do not xfail or waive."""
import numpy as np
import pytest
from audit_smooth_stage_reversal import gravity_oracle, run


@pytest.fixture(scope='module', params=(1,0))
def record(request):
    return run(request.param)


def test_independent_zero_flow_gravity_oracle(record):
    np.testing.assert_allclose(gravity_oracle(1)['velocity_rate'],
                               [40.548,-24.525,29.103],rtol=0,atol=1e-12)
    np.testing.assert_allclose(gravity_oracle(-1)['velocity_rate'],
                               [3.597,-34.335,-14.388],rtol=0,atol=1e-12)
    assert gravity_oracle(1)['momentum_rate']==26.9775
    assert gravity_oracle(-1)['momentum_rate']==-30.65625
    for probe in record['probes']:
        for side in probe['sides']:
            assert side['exact_gravity_limit_error']<1e-10
            assert side['physical_velocity_recovery_error']<1e-12
    assert record['mass_gap_shrink']>65000


def test_pressure_force_is_continuous_across_zero_flow(record):
    # 65536x smaller velocity perturbation must reduce the force gap; this
    # deliberately loose necessary condition is not a full C1/order gate.
    assert record['flow_reversal_continuity_passed']


def test_resting_flat_bed_pressure_respects_reflection(record):
    assert record['resting_reflection_error']<1e-10
