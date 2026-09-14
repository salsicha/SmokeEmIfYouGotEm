import numpy as np
import pytest
import reconstructed_nonlinear_pressure as pressure
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from source_supported_pressure_reference import solve


def test_two_pole_lake_is_unchanged_and_forcing_binding_restored():
    state=np.zeros((10,11,3));state[...,0]=1.;bed=np.zeros((10,11));rate=np.zeros_like(state)
    core=(slice(3,-3),slice(3,-3))
    g=ReconstructedPressureGeometry(state[core][...,0],bed[core],.5,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')
    original=pressure.kinematic_forcing
    force,detail=solve(g,state[core],state,bed,rate,np.zeros((18,2)))
    np.testing.assert_array_equal(force,0.)
    assert len(detail['poles'])==2 and all(p['iterations']==0 for p in detail['poles'])
    assert pressure.kinematic_forcing is original
    with pytest.raises(ValueError):solve(g,state[core],state,bed,rate,np.zeros((17,2)))
    assert pressure.kinematic_forcing is original


def test_no_fabricated_rates_or_different_current_depth():
    state=np.zeros((10,11,3));state[...,0]=1.;bed=np.zeros((10,11));core=(slice(3,-3),slice(3,-3))
    g=ReconstructedPressureGeometry(state[core][...,0],bed[core],.5,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')
    with pytest.raises(ValueError):solve(g,state[core],state,bed,np.zeros((4,5,3)),np.zeros((18,2)))
    changed=state[core].copy();changed[0,0,0]=.5
    with pytest.raises(ValueError):solve(g,changed,state,bed,np.zeros_like(state),np.zeros((18,2)))
