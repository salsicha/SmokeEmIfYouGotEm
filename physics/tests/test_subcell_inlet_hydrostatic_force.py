from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_exact_geometry import SourceFragment
from subcell_inlet_hydrostatic_force import source_hydrostatic_force, lateral_front_moment
from subcell_inlet_sweep_geometry import InletSweep
from test_subcell_inlet_sweep_geometry import fixture
from test_subcell_inlet_face_transport import split


def midpoint(bounds):
    return np.array([float((a+b)/2) for a,b in bounds])


def boundary_pressure(sweep, fragment):
    # Independent Eulerian boundary traction: -g/2 integral h^2 n dl.
    # No volume force formula or radial integration helper is used here.
    a0=np.array([float(x) for x in sweep.edge[0][:2]])
    transform=np.array([[float(sweep.delta[j]),float(sweep.velocity[j])] for j in range(2)])
    time=float(sweep.time_root**3)
    polygon=np.array([[float(x) for x in p[:2]] for p in fragment.polygon])
    orientation=np.sign(sum(np.linalg.det(np.array([a,b])) for a,b in zip(polygon,np.roll(polygon,-1,axis=0))))
    result=np.zeros(2)
    for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
        edge=b-a
        def value(lam):
            s,age=np.linalg.solve(transform,a+lam*edge-a0)
            if s<0 or age<0 or age>time:
                return 0.
            h=max(0.,float(sweep.height_scale)*np.cbrt(time-age)-float(sweep.bed_span)*s)
            return h*h
        integral=quad(value,0,1,epsabs=1e-15,epsrel=1e-10,
                      points=[1/128,1/64,1/32,1/16,1/8,1/4,1/2],limit=300)[0]
        result-=float(sweep.gravity)/2*orientation*np.array([edge[1],-edge[0]])*integral
    return result


def test_full_source_force_matches_closed_form_and_exact_cross_slope_balance():
    sweep,receiver=fixture()
    force=source_hydrostatic_force(sweep,receiver)
    volume=sweep.full_moment(1)
    weighted=sweep.jacobian*sweep.height_scale**2*sweep.time_root**3/(2*sweep.bed_span)
    assert force['pressure_weighted_volume_bounds']==(weighted,weighted)
    expected=(sweep.gravity*weighted/6,sweep.gravity*volume)
    assert force['pressure_force_per_density_bounds']==tuple((x,x) for x in expected)
    combined=expected[0]+5*sweep.gravity*volume
    assert force['combined_force_per_density_bounds']==((combined,combined),(F(0),F(0)))
    assert force['velocity_dot_force_per_density_bounds']==(2*combined,2*combined)
    assert not force['nonhydrostatic_or_curvature_or_coupled_time_or_gameplay_accepted']
    assert force['positive_depth_lateral_front_on_source_boundary_proven']
    assert not force['wet_dry_riemann_flux_or_lateral_fan_accepted']


@pytest.mark.parametrize('cut',[None,F(7,256),F(3,200)])
def test_pressure_matches_independent_boundary_traction_on_crossed_sources(cut):
    sweep,receiver=fixture()
    pieces=[receiver] if cut is None else split(receiver,cut)
    for piece in pieces:
        force=source_hydrostatic_force(sweep,piece)
        np.testing.assert_allclose(midpoint(force['pressure_force_per_density_bounds']),
                                   boundary_pressure(sweep,piece),rtol=2e-8,atol=2e-12)
        assert force['combined_force_per_density_bounds'][1]==(F(0),F(0))
        assert force['pressure_weighted_moment_relative_width']<F(1,10**12)


def test_partition_preserves_force_including_cancellation_of_shared_pressure_faces():
    sweep,receiver=fixture()
    whole=source_hydrostatic_force(sweep,receiver)
    pieces=[source_hydrostatic_force(sweep,p) for p in split(receiver,F(3,200))]
    for name in ('pressure_force_per_density_bounds','bed_force_per_density_bounds','combined_force_per_density_bounds'):
        for j in range(2):
            lo=sum(p[name][j][0] for p in pieces)
            hi=sum(p[name][j][1] for p in pieces)
            assert lo<=whole[name][j][1] and hi>=whole[name][j][0]
            assert hi-lo<F(1,10**10)*sum(abs(x[0]) for x in whole['pressure_force_per_density_bounds'])


def test_original_bed_slope_changes_force_without_relocating_water_or_changing_pressure():
    sweep,receiver=fixture()
    before=source_hydrostatic_force(sweep,receiver)
    tilted=replace(receiver,polygon=tuple((x,y,z+8*x) for x,y,z in receiver.polygon),
                   gradient=(receiver.gradient[0]+8,receiver.gradient[1]))
    after=source_hydrostatic_force(sweep,tilted)
    assert after['pressure_force_per_density_bounds']==before['pressure_force_per_density_bounds']
    assert after['volume_bounds']==before['volume_bounds']
    delta=-8*sweep.gravity*sweep.full_moment(1)
    assert after['combined_force_per_density_bounds'][0]==tuple(x+delta for x in before['combined_force_per_density_bounds'][0])


def test_transverse_velocity_and_coordinate_rotation_preserve_force_covariance():
    sweep,receiver=fixture()
    sweep=replace(sweep,velocity=(F(2),F(1,5)))
    before=source_hydrostatic_force(sweep,receiver)
    assert before['positive_depth_lateral_front_proven']
    assert before['interior_lateral_front_radial_moment_bounds'][0]>0
    assert before['lateral_front_pressure_jump_per_density_bounds'][1][1]<0
    np.testing.assert_allclose(midpoint(before['pressure_force_per_density_bounds']),
                               boundary_pressure(sweep,receiver),rtol=2e-8,atol=2e-12)
    move=lambda p:(-p[1]+F(10**12),p[0]-F(10**12),p[2]+F(10**15))
    rotated=replace(sweep,edge=tuple(move(p) for p in sweep.edge),velocity=(-sweep.velocity[1],sweep.velocity[0]))
    fragment=replace(receiver,polygon=tuple(move(p) for p in reversed(receiver.polygon)),
                     gradient=(-receiver.gradient[1],receiver.gradient[0]))
    after=source_hydrostatic_force(rotated,fragment)
    for name in ('pressure_force_per_density_bounds','bed_force_per_density_bounds','combined_force_per_density_bounds'):
        x,y=before[name]
        assert after[name]==((-y[1],-y[0]),x)


def test_birth_limit_is_integrable_without_depth_or_time_floor():
    sweep,receiver=fixture()
    values=[]
    for divisor in (1,2,4):
        current=replace(sweep,time_root=sweep.time_root/divisor)
        force=source_hydrostatic_force(current,receiver)
        values.append(force['pressure_force_per_density_bounds'][0][0])
    assert values[0]==8*values[1]==64*values[2]  # pressure momentum rate scales as R^3
    tiny=InletSweep(sweep.edge,(F(1,10**126),0),1,F(1,10**255))
    force=source_hydrostatic_force(tiny,receiver)
    assert force['pressure_force_per_density_bounds'][0][0]>0
    assert float(force['pressure_force_per_density_bounds'][0][0])==0.


def test_wrong_original_gradient_donor_role_and_resolution_reject():
    sweep,receiver=fixture()
    with pytest.raises(ValueError,match='gradient and vertices disagree'):
        source_hydrostatic_force(sweep,replace(receiver,gradient=(F(0),F(0))))
    donor=SourceFragment(81,tuple(tuple(map(F,p)) for p in ((0,0,10),(0,2,12),(-2,0,10))),(F(0),F(1)))
    with pytest.raises(ValueError,match='does not close'):
        source_hydrostatic_force(sweep,donor)
    with pytest.raises(ValueError,match='bound unresolved'):
        source_hydrostatic_force(sweep,split(receiver,F(3,200))[0],max_depth=1)
    with pytest.raises(ValueError,match='affine bed gradient'):
        source_hydrostatic_force(sweep,replace(receiver,polygon=()))
    with pytest.raises(ValueError,match='radial Jacobian'):
        sweep.full_moment(1,radial_power=True)
    with pytest.raises(ValueError,match='lateral-front integration bound'):
        lateral_front_moment(sweep,receiver,max_depth=True)
    with pytest.raises(ValueError,match='boolean'):
        lateral_front_moment(sweep,receiver,include_boundary='yes')


def test_discontinuous_shared_front_trace_is_not_a_conservative_riemann_flux():
    sweep,receiver=fixture()
    sweep=replace(sweep,velocity=(F(2),F(1,5)))
    whole=source_hydrostatic_force(sweep,receiver)
    # The ray y=x/10 now lies exactly on an artificial partition edge.
    # Wet and dry one-sided traces cannot be used as a common numerical flux.
    corner=(F(20,11),F(2,11),F(12,11))
    wet=replace(receiver,polygon=(receiver.polygon[0],corner,receiver.polygon[2]))
    dry=replace(receiver,polygon=(receiver.polygon[0],receiver.polygon[1],corner))
    parts=[source_hydrostatic_force(sweep,p) for p in (wet,dry)]
    assert parts[0]['positive_depth_lateral_front_on_source_boundary_proven']
    assert parts[1]['positive_depth_lateral_front_on_source_boundary_proven']
    trace_sum=sum(p['pressure_force_per_density_bounds'][1][0] for p in parts)
    assert trace_sum>whole['pressure_force_per_density_bounds'][1][1]
    assert all(not p['wet_dry_riemann_flux_or_lateral_fan_accepted'] for p in parts)
