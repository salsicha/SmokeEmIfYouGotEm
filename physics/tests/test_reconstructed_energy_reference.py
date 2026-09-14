import numpy as np
import pytest
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate
from reconstructed_energy_reference import metric,energy,energy_rate,tangent_matrices
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from finite_depth_pressure_reference import LENGTHS,WEIGHTS


def make(h,bed):
    return ReconstructedPressureGeometry(h,bed,.5,periodic=True,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')


def test_single_pole_equals_independently_integrated_vertical_kinetic_energy():
    rng=np.random.default_rng(1151);h=rng.uniform(.5,2.,(3,4));bed=rng.uniform(0,.2,h.shape)
    u=rng.normal(size=(*h.shape,2))*.2;g=make(h,bed);d,e=g.kinematic_components(u)
    expected=np.sum(.5*h*np.sum(u*u,axis=-1)+h**3*d*d/6-h*h*d*e/2+h*e*e/2
                    +9.81*h*(.5*h+bed))*g.dx**2
    assert energy(g,u)==pytest.approx(expected,rel=2e-14,abs=1e-13)


@pytest.mark.parametrize('rational',[False,True])
def test_energy_direction_matches_independent_finite_differences(rational):
    rng=np.random.default_rng(1152);h=rng.uniform(.8,2.,(3,4));bed=rng.uniform(0,.2,h.shape)
    u=rng.normal(size=(*h.shape,2))*.2;ht=rng.normal(size=h.shape)*.02;mt=rng.normal(size=u.shape)*.02
    g=make(h,bed);tangent=PressureGeometryRate(g,bed,ht)
    predicted=energy_rate(g,tangent,u,mt,rational=rational)['total']
    errors=[]
    for epsilon in (1e-2,1e-3):
        values=[]
        for sign in (-1,1):
            hh=h+sign*epsilon*ht;mm=h[...,None]*u+sign*epsilon*mt
            values.append(energy(make(hh,bed),mm/hh[...,None],rational=rational))
        errors.append(abs((values[1]-values[0])/(2*epsilon)-predicted))
    assert errors[-1]<2e-8 and errors[-1]<errors[0]/50


def test_tangent_face_matrices_match_original_rate_actions():
    rng=np.random.default_rng(1153);h=rng.uniform(.5,2.,(3,4));bed=rng.uniform(0,1,h.shape)
    g=make(h,bed);t=PressureGeometryRate(g,bed,rng.normal(size=h.shape)*.1)
    u=rng.normal(size=(*h.shape,2));d,e=tangent_matrices(t);actual=t.kinematic_rate(u)
    np.testing.assert_allclose(d@u.ravel(),actual[0].ravel(),atol=2e-15,rtol=0)
    np.testing.assert_allclose(e@u.ravel(),actual[1].ravel(),atol=2e-15,rtol=0)


def test_rational_metric_is_inverse_of_actual_pole_acceleration_response():
    rng=np.random.default_rng(1154);h=rng.uniform(.5,2.,(3,4));bed=rng.uniform(0,.2,h.shape);g=make(h,bed)
    basis=np.eye(2*h.size).reshape(-1,*h.shape,2)
    response=(1-float(np.sum(WEIGHTS)))*np.eye(2*h.size)
    for length,weight in zip(LENGTHS,WEIGHTS):
        s=ReconstructedAccelerationSystem(g,length)
        matrix=np.stack([s.apply(x).ravel() for x in basis],axis=1)
        response+=weight*np.linalg.solve(matrix,np.eye(2*h.size))
    k,_=metric(g,rational=True)
    np.testing.assert_allclose(k@response,np.eye(2*h.size),atol=2e-14,rtol=0)
    assert np.linalg.eigvalsh(k).min()>0


def test_no_silent_dry_normalization_or_missing_boundary_energy():
    h=np.ones((3,4));h[0,0]=0
    with pytest.raises(ValueError):metric(make(h,h*0))
    g=ReconstructedPressureGeometry(np.ones((3,4)),np.zeros((3,4)),.5,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')
    with pytest.raises(ValueError):metric(g)
