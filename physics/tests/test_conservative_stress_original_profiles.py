"""Momentum improvement must not waive the independent energy failures."""
import pytest
from audit_conservative_rational_stress import run


@pytest.fixture(scope='module',params=[(seed,n) for n in (64,128) for seed in (2200,2202,2204,2206)])
def original(request):
    return run(*request.param)


def test_original_physical_momentum_and_local_stress(original):
    assert original['momentum_conservation_gate_passed']
    assert original['local_momentum_flux_error']<1e-10
    assert abs(original['net_mass_rate'])<1e-10
    assert original['energy_coordinate_error']<1e-10


def test_original_energy_conservation_not_waived(original):
    assert original['energy_conservation_gate_passed']
