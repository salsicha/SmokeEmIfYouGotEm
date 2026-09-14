import numpy as np
from audit_total_depth_dispersion import solitary
from audit_reconstructed_solitary_residual import exact_time_rate, measure


def test_profile_time_derivative_matches_independent_centered_time_difference():
    x = np.linspace(0, 96, 193); time, dt = .5, 1e-5
    before, _ = solitary(x, time-dt); after, _ = solitary(x, time+dt)
    np.testing.assert_allclose(exact_time_rate(x, time), (after-before)/(2*dt), atol=8e-10, rtol=1e-6)


def test_actual_sgn_rate_refines_without_periodic_momentum_leak():
    coarse, fine = measure(.5, 'sgn'), measure(.25, 'sgn')
    assert fine['relative_mass_rate_l1_difference'] < coarse['relative_mass_rate_l1_difference']
    assert fine['relative_momentum_rate_l1_difference'] < coarse['relative_momentum_rate_l1_difference']
    for value in (coarse, fine):
        assert value['exact_for_governing_equations']
        assert abs(value['net_mass_rate_per_width_m2ps']) < 1e-12
        np.testing.assert_allclose(value['net_momentum_rate_per_width_m3ps2'], 0, atol=1e-12)
        assert value['transverse_rate_max'] == 0
        assert max(p['relative_residual'] for stage in value['pressure_stages']
                   for p in stage['pressure_stats']) < 2e-5


def test_fine_rational_pressure_failure_is_not_hidden_by_small_physical_error():
    result = measure(.125, 'rational_sgn')
    assert not result['pressure_residual_check_passed']
    assert max(p['relative_residual'] for stage in result['pressure_stages']
               for p in stage['pressure_stats']) > 2e-5
