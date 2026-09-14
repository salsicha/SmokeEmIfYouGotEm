import numpy as np
import pytest
import test_positive_rational_velocity_stage as positive_controls
import test_rational_velocity_bracket_reference as original
from smooth_rational_velocity_stage import stage,rk2_step,make


@pytest.fixture
def smooth_controls(monkeypatch):
    monkeypatch.setattr(original,'make',lambda h,b:make(h,b,.5))
    monkeypatch.setattr(original,'stage',stage)
    monkeypatch.setattr(positive_controls,'stage',stage)
    monkeypatch.setattr(positive_controls,'rk2_step',rk2_step)


@pytest.mark.parametrize('seed',(6301,6302,6303))
def test_original_closed_energy_direction_controls(smooth_controls,seed):
    original.test_nonlinear_closed_stage_energy_and_independent_state_direction(seed)


@pytest.mark.parametrize('name',[
    'test_stationary_lake_inputs_unchanged_and_mass_step_positive',
    'test_dry_pressure_not_silently_accepted',
    'test_rk2_matches_two_original_stages_without_changing_inputs'])
def test_previous_stage_controls_unchanged(smooth_controls,name):
    getattr(positive_controls,name)()


@pytest.mark.parametrize('seed',(7325,7326))
def test_original_rough_bed_states(smooth_controls,seed):
    positive_controls.test_original_rough_bed_positive_cut_states(seed)


def test_high_bed_barrier_retains_blocked_pressure_face():
    h=np.ones((3,9));b=np.zeros_like(h);b[:,4]=10.;g=make(h,b,.5)
    assert np.all(g.polynomials[0]['fa'][:,3]==0)
    assert np.all(g.edges[0]['aa'][:,3]==0)
    assert np.all(g.polynomials[0]['fb'][:,4]==0)
    assert np.all(g.edges[0]['ab'][:,4]==0)
