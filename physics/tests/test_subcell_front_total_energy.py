"""Independent total-energy checks; none imply a conservative front force law."""
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_affine_dry_fan import AffineDryFan
from subcell_affine_front_metric import front_metric
from subcell_affine_front_pressure import FrontPressureGeometry
from subcell_exact_geometry import clip
from subcell_front_total_energy import FrontTotalEnergyVariation
from test_subcell_affine_dry_fan import rectangle
from test_subcell_front_pressure_variation import P, PD, floats, independent_energy, primitives
from test_subcell_moving_pressure_metric import geometry, metric


def primitive_state(g, coordinate):
    state=primitives(g)
    if coordinate=='canonical':
        state['p']=floats(metric(g).evaluate(P,PD)['canonical_momentum'])
    state['spatial']=floats([g.forms[i]['depth_spatial_moments'] for i in g.active])
    state['bed']=np.array([float(g.forms[i]['bed_at_origin']) for i in g.active])
    return state


def independent_total(g, state, coordinate, datum=0):
    kinetic=independent_energy(g,**{k:v for k,v in state.items() if k not in ('spatial','bed')},coordinate=coordinate)
    gravity=np.array([float(g.forms[i]['gravity']) for i in g.active])
    potential=np.sum(gravity*((state['bed']-datum)*state['moments'][:,0]
                  +state['moments'][:,1]/2+np.sum(state['slopes']*state['spatial'],axis=1)))
    return kinetic+potential


@pytest.mark.parametrize('coordinate',['physical','canonical'])
@pytest.mark.parametrize('kind',['p','moments','slopes','columns','spatial','bed'])
def test_all_total_energy_partials_match_independent_complex_step(coordinate,kind):
    g=geometry();r=FrontTotalEnergyVariation(g,metric(g),P,energy_datum=F(1,3))
    state=primitive_state(g,coordinate);prefix='canonical_' if coordinate=='canonical' else ''
    derivatives=dict(p=getattr(r,prefix+'momentum_gradient'),
                     moments=getattr(r,prefix+'depth_moment_gradients'),
                     slopes=getattr(r,prefix+'bed_gradient_gradients'),
                     columns=getattr(r,prefix+'face_column_gradients'),
                     spatial=r.spatial_moment_gradients,bed=r.bed_height_gradients)
    expected=np.asarray(derivatives[kind],dtype=float);measured=np.zeros_like(expected)
    assert independent_total(g,state,coordinate,1/3)==pytest.approx(float(r.total_energy),rel=2e-13,abs=1e-14)
    for index in np.ndindex(expected.shape):
        changed={k:v.astype(complex) for k,v in state.items()}
        changed[kind][index]+=1e-25j
        measured[index]=independent_total(g,changed,coordinate,1/3).imag/1e-25
    np.testing.assert_allclose(measured,expected,rtol=1e-10,atol=1e-10)


@pytest.mark.parametrize('slope',[-F(1,5),0,F(1,4)])
def test_potential_and_physical_time_work_match_independent_branch_quadrature(slope):
    fan=AffineDryFan((0,0),(1,0),F(3,4),(F(2,5),0),3,(slope,0))
    source=rectangle(slope=(slope,0),bed=3);t=F(1,5)
    g=FrontPressureGeometry(fan,(source,),t,outer_boundary='reflecting')
    result=FrontTotalEnergyVariation(g,metric(g),((0,0),),energy_datum=1)
    gravity=float(fan.gravity);time=float(t);s=float(slope);wave=np.sqrt(gravity*.75)
    head=(.4-wave)*time-gravity*s*time*time/2
    edge=(.4+2*wave)*time-gravity*s*time*time/2
    def values(x):
        if x<=head:return .75,0.
        if x>=edge:return 0.,0.
        L=.4+2*wave-x/time-gravity*s*time/2
        return L*L/(9*gravity),2*L*(x/time**2-gravity*s/2)/(9*gravity)
    points=[x for x in (head,edge) if -2<x<2]
    integral=lambda f:quad(f,-2,2,points=points,epsabs=1e-12)[0]
    energy=integral(lambda x:gravity*(values(x)[0]**2/2+(2+s*x)*values(x)[0]))
    rate=integral(lambda x:gravity*(values(x)[0]+2+s*x)*values(x)[1])
    assert float(result.potential_energy)==pytest.approx(energy,rel=2e-13,abs=1e-12)
    assert float(result.time_work(((0,0),))['potential_energy_direction'])==pytest.approx(rate,rel=2e-13,abs=1e-12)
    form=g.forms[0]
    assert float(form['depth_spatial_moments'][0])==pytest.approx(integral(lambda x:x*values(x)[0]),abs=1e-12)
    assert float(form['depth_spatial_moment_rates'][0])==pytest.approx(integral(lambda x:x*values(x)[1]),abs=1e-12)
    assert form['depth_spatial_moments'][1]==form['depth_spatial_moment_rates'][1]==0


def test_total_physical_time_derivative_and_both_momentum_coordinates():
    t=F(1,5);g=geometry(t);m=metric(g);solved=m.evaluate(P,PD)
    result=FrontTotalEnergyVariation(g,m,P,solved_state=solved)
    physical=result.time_work(PD)
    canonical=result.time_work(solved['canonical_momentum_rate'],momentum_coordinate='canonical')
    assert physical['energy_direction']==canonical['energy_direction']
    assert physical['potential_energy_direction']==canonical['potential_energy_direction']!=0
    assert physical['kinetic_energy_direction']==solved['kinetic_energy_rate']
    assert physical['spatial_moment_work']!=0
    terms=('momentum_work','face_column_work','depth_moment_work','bed_gradient_work','spatial_moment_work','bed_height_work')
    assert sum(physical[key] for key in terms)==physical['energy_direction']
    assert not physical['conservative_force_or_wetting_or_open_or_native_or_gameplay_accepted']
    errors=[]
    for divisor in (200,400,800,1600):
        eps=t/divisor;energies=[]
        for sign in (-1,1):
            probe=geometry(t+sign*eps)
            p=tuple(tuple(x+sign*eps*y for x,y in zip(a,b)) for a,b in zip(P,PD))
            energies.append(FrontTotalEnergyVariation(probe,metric(probe),p).total_energy)
        errors.append(abs(float((energies[1]-energies[0])/(2*eps)-physical['energy_direction'])))
    assert all(a/b>3.8 for a,b in zip(errors,errors[1:]))
    assert errors[-1]<1e-6


def test_energy_datum_shift_has_exact_mass_and_mass_rate_work_not_a_force_change():
    g=geometry();m=metric(g);delta=F(17,3)
    before=FrontTotalEnergyVariation(g,m,P)
    after=FrontTotalEnergyVariation(g,m,P,energy_datum=delta)
    expected=sum(g.forms[i]['gravity']*g.forms[i]['depth_moments'][1] for i in g.active)
    rate=sum(g.forms[i]['gravity']*g.forms[i]['depth_moment_rates'][0] for i in g.active)
    assert after.total_energy-before.total_energy==-delta*expected
    assert after.time_work(PD)['energy_direction']-before.time_work(PD)['energy_direction']==-delta*rate
    assert before.momentum_gradient==after.momentum_gradient
    assert before.face_column_gradients==after.face_column_gradients
    assert before.bed_gradient_gradients==after.bed_gradient_gradients
    assert after.potential_energy<0  # Datum-dependent potential need not be positive.


def test_spatial_moments_are_exact_under_source_split_winding_and_origin_translation():
    fan=AffineDryFan((0,0),(3,4),F(7,10),(F(1,3),-F(1,4)),2,(F(1,5),-F(1,7)))
    source=rectangle(slope=fan.gradient,bed=2);t=F(1,5)
    original=front_metric(fan,source,t)
    parts=[front_metric(fan,replace(source,polygon=clip(source.polygon,0,F(1,5),side)),t) for side in (False,True)]
    backwards=front_metric(fan,replace(source,polygon=tuple(reversed(source.polygon))),t)
    offset=(F(12345),-F(23456))
    moved=replace(source,polygon=tuple((p[0]+offset[0],p[1]+offset[1],p[2]) for p in source.polygon))
    translated=AffineDryFan(offset,fan.normal,fan.depth,fan.velocity,fan.bed,fan.gradient,fan.gravity)
    other=front_metric(translated,moved,t)
    for key in ('depth_spatial_moments','depth_spatial_moment_rates'):
        assert tuple(a+b for a,b in zip(parts[0][key],parts[1][key]))==original[key]
        assert backwards[key]==other[key]==original[key]


def test_spatial_bed_potential_cannot_use_geometric_centroid_times_volume():
    fan=AffineDryFan((0,0),(1,0),1,(0,0),2,(F(1,5),0),gravity=1)
    fragment=rectangle(x0=0,x1=F(1,2),slope=fan.gradient,bed=2)
    form=front_metric(fan,fragment,F(1,5))
    assert form['depth_spatial_moments'][0]!=F(1,4)*form['depth_moments'][1]


def test_positive_subfloat_potential_and_empty_dry_state_are_not_deleted():
    tiny=F(1,10**400)
    fan=AffineDryFan((0,0),(1,0),tiny,(0,0),0,(0,0),gravity=1)
    wet=rectangle(x0=-2,x1=-1,y0=0,y1=1)
    g=FrontPressureGeometry(fan,(wet,),1,outer_boundary='reflecting')
    result=FrontTotalEnergyVariation(g,metric(g),((0,0),))
    assert result.potential_energy==tiny*tiny/2>0 and float(result.potential_energy)==0
    change=result.work(((0,0),),((tiny,2*tiny*tiny,3*tiny**3),),[(0,0) for _ in g.faces],
                       ((0,0),),((0,0),),(0,))
    assert change['energy_direction']==tiny*tiny>0
    dry=rectangle(x0=2,x1=3,y0=0,y1=1)
    empty=FrontPressureGeometry(fan,(dry,),1,outer_boundary='reflecting')
    zero=FrontTotalEnergyVariation(empty,metric(empty),())
    assert zero.total_energy==zero.time_work(())['energy_direction']==0
    direction=[(F(1,10**400),0) for _ in empty.faces]
    with pytest.raises(ValueError,match='Dry pressure topology'):
        zero.work((),(),direction,(),(),())


@pytest.mark.parametrize('field',['gravity','bed_at_origin','spatial_origin'])
def test_altered_source_bed_or_invalid_gravity_is_not_accepted(field):
    g=geometry();g.forms[0][field]={'gravity':-1,'bed_at_origin':3,'spatial_origin':(1,2)}[field]
    with pytest.raises(ValueError,match='matching original affine bed'):
        FrontTotalEnergyVariation(g,metric(g),P)


def test_missing_directions_and_unknown_momentum_coordinate_reject():
    g=geometry();r=FrontTotalEnergyVariation(g,metric(g),P)
    with pytest.raises(ValueError,match='per active original source'):
        r.work(P,((0,0,0),)*2,[(0,0) for _ in g.faces],P,(),())
    with pytest.raises(ValueError,match='momentum coordinate'):
        r.time_work(PD,momentum_coordinate='layer')
