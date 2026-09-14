import numpy as np
import pytest
from periodic_connected_scalar_reference import gradient, periodic_connected_gradients
from reconstructed_pressure_geometry import ReconstructedPressureGeometry


def geometry(h,dx,periodic=True):
    return ReconstructedPressureGeometry(h,np.zeros_like(h),dx,periodic=periodic,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')


def test_actual_periodic_boundary_values_and_refinement():
    errors=[]
    for n in (16,32,64):
        dx=2*np.pi/n;x=(np.arange(n)+.5)*dx
        h=(1+.2*np.sin(x))[None];f=np.sin(x)[None]
        g=geometry(h,dx)
        actual=gradient(g,f)
        errors.append(float(abs(actual[...,0]-np.cos(x)[None]).max()))
        assert np.all(actual[...,1]==0)
        assert np.all(gradient(g,np.ones_like(h))==0)
        shifted=gradient(geometry(np.roll(h,5,1),dx),np.roll(f,5,1))
        np.testing.assert_array_equal(shifted,np.roll(actual,5,1))
    assert errors[0]/errors[1]>3.5 and errors[1]/errors[2]>3.5


def test_rejects_open_or_dry_domain_and_restores_on_failure():
    g=geometry(np.ones((3,5)),1.,False)
    with pytest.raises(ValueError,match='open-boundary'):gradient(g,np.ones_like(g.h))
    h=np.ones((3,5));h[1,2]=0
    with pytest.raises(ValueError,match='fully positive'):gradient(geometry(h,1.),h)
    original=ReconstructedPressureGeometry.scalar_gradient
    with pytest.raises(RuntimeError):
        with periodic_connected_gradients():
            assert ReconstructedPressureGeometry.scalar_gradient is gradient
            raise RuntimeError('intentional')
    assert ReconstructedPressureGeometry.scalar_gradient is original
