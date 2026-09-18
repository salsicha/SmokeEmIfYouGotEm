from fractions import Fraction as F

import numpy as np
import pytest

from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from subcell_affine_dry_fan import AffineDryFan
from subcell_affine_front_pressure import FrontPressureGeometry
from subcell_front_pressure_variation import FrontPressureVariation
from test_subcell_affine_dry_fan import rectangle
from test_subcell_moving_pressure_metric import geometry, metric


P=((F(1,30),-F(1,20)),(F(1,70),F(2,90)))
PD=((F(1,50),F(1,30)),(-F(1,40),F(3,70)))


def floats(values):return np.array([[float(x) for x in row] for row in values])


def primitives(g):
    return dict(p=floats(P),moments=floats([g.forms[i]['depth_moments'][1:] for i in g.active]),
                slopes=floats([g.fragments[i].gradient for i in g.active]),
                columns=floats([f['column_normal'] for f in g.faces]))


def independent_energy(g,p,moments,slopes,columns,coordinate='physical'):
    """Independent normalized two-pole map, rebuilt from primitive values.

    No implementation pullback or stored divergence/Gram/kinetic/rate is read.
    Complex inputs provide a cancellation-free independent derivative probe.
    """
    n=len(g.active);dtype=np.result_type(p,moments,slopes,columns)
    divergence=np.zeros((n,2*n),dtype=dtype);kinetic=np.zeros((2*n,2*n),dtype=dtype)
    positions={owner:i for i,owner in enumerate(g.active)}
    for face,column in zip(g.faces,columns):
        owners=face['owners']
        if any(i not in positions for i in owners):continue
        incidence=np.zeros((n,2),dtype=dtype)
        incidence[positions[owners[0]]]=-column
        if len(owners)==2:incidence[positions[owners[1]]]=column
        for owner in owners:
            row=positions[owner]
            divergence[row]+=incidence.ravel()/(len(owners)*moments[row,0])
    for row in range(n):
        m1,m2,m3=moments[row];bx,by=slopes[row]
        gram=np.array([[m3,-1.5*bx*m2,-1.5*by*m2],
                       [-1.5*bx*m2,3*bx*bx*m1,3*bx*by*m1],
                       [-1.5*by*m2,3*bx*by*m1,3*by*by*m1]],dtype=dtype)
        j=np.zeros((3,2*n),dtype=dtype);j[0]=divergence[row]
        j[1,2*row]=j[2,2*row+1]=1
        kinetic+=j.T@gram@j
    root=np.sqrt(np.repeat(moments[:,0],2));q=kinetic/root[:,None]/root[None,:]
    response=(1-float(np.sum(WEIGHTS)))*np.eye(2*n,dtype=dtype)
    for lam,w in zip(LENGTHS,WEIGHTS):response+=w*np.linalg.inv(np.eye(2*n)+lam*q)
    momentum=p.ravel()/root
    return momentum@(np.linalg.solve(response,momentum) if coordinate=='physical' else response@momentum)/2


@pytest.mark.parametrize('kind',('p','moments','slopes','columns'))
def test_every_primitive_partial_matches_independent_complex_step(kind):
    g=geometry();m=metric(g);r=FrontPressureVariation(g,m,P);state=primitives(g)
    derivatives=dict(p=r.momentum_gradient,moments=r.depth_moment_gradients,
                     slopes=r.bed_gradient_gradients,columns=r.face_column_gradients)
    expected=floats(derivatives[kind]);measured=np.zeros_like(expected)
    np.testing.assert_allclose(independent_energy(g,**state),float(m.evaluate(P,PD)['kinetic_energy']),rtol=2e-13,atol=1e-14)
    for index in np.ndindex(expected.shape):
        probe={k:v.astype(complex) for k,v in state.items()}
        probe[kind][index]+=1.e-25j
        measured[index]=independent_energy(g,**probe).imag/1.e-25
    np.testing.assert_allclose(measured,expected,rtol=1e-10,atol=1e-10)


def test_source_time_pullback_equals_complete_physical_energy_rate_exactly():
    g=geometry();m=metric(g);r=FrontPressureVariation(g,m,P)
    direct=m.evaluate(P,PD);reverse=r.time_work(PD)
    assert reverse['energy_direction']==direct['kinetic_energy_rate']
    assert reverse['momentum_work']==direct['momentum_work']
    assert reverse['depth_moment_work']+reverse['face_column_work']==direct['geometry_time_work']
    assert reverse['bed_gradient_work']==0
    assert reverse['depth_moment_work']!=0 and reverse['face_column_work']!=0
    assert not reverse['nonlinear_force_or_topology_change_or_gameplay_accepted']


@pytest.mark.parametrize('kind',('p','moments','slopes','columns'))
def test_fixed_canonical_momentum_uses_the_other_conjugate_velocity(kind):
    g=geometry();m=metric(g);r=FrontPressureVariation(g,m,P);state=primitives(g)
    direct=m.evaluate(P,PD);state['p']=floats(direct['canonical_momentum'])
    derivatives=dict(p=r.canonical_momentum_gradient,moments=r.canonical_depth_moment_gradients,
                     slopes=r.canonical_bed_gradient_gradients,columns=r.canonical_face_column_gradients)
    expected=floats(derivatives[kind]);measured=np.zeros_like(expected)
    np.testing.assert_allclose(independent_energy(g,**state,coordinate='canonical'),float(direct['kinetic_energy']),rtol=2e-13,atol=1e-14)
    for index in np.ndindex(expected.shape):
        probe={k:v.astype(complex) for k,v in state.items()}
        probe[kind][index]+=1.e-25j
        measured[index]=independent_energy(g,**probe,coordinate='canonical').imag/1.e-25
    np.testing.assert_allclose(measured,expected,rtol=1e-10,atol=1e-10)
    assert r.canonical_momentum_gradient==direct['layer_velocity']
    assert r.momentum_gradient==direct['canonical_velocity']
    assert r.canonical_momentum_gradient!=r.momentum_gradient


def test_both_momentum_coordinates_give_the_same_exact_physical_time_work():
    g=geometry();m=metric(g);r=FrontPressureVariation(g,m,P);direct=m.evaluate(P,PD)
    canonical=r.time_work(direct['canonical_momentum_rate'],momentum_coordinate='canonical')
    assert canonical['energy_direction']==r.time_work(PD)['energy_direction']==direct['kinetic_energy_rate']
    assert canonical['momentum_work']!=r.time_work(PD)['momentum_work']
    wrong=r.time_work(direct['canonical_momentum_rate'])
    assert wrong['energy_direction']!=direct['kinetic_energy_rate']
    with pytest.raises(ValueError,match='momentum coordinate'):
        r.time_work(PD,momentum_coordinate='layer')


def test_simultaneous_real_primitive_direction_converges_without_fitting_a_force():
    g=geometry();r=FrontPressureVariation(g,metric(g),P);state=primitives(g)
    direction={k:np.arange(v.size).reshape(v.shape)*.001+.003 for k,v in state.items()}
    exact=r.work(direction['p'],direction['moments'],direction['columns'],direction['slopes'])
    expected=float(exact['energy_direction']);errors=[]
    for epsilon in (.004,.002,.001):
        energies=[independent_energy(g,**{k:v+sign*epsilon*direction[k] for k,v in state.items()}) for sign in (-1,1)]
        errors.append(abs((energies[1]-energies[0])/(2*epsilon)-expected))
    assert all(a/b>3.8 for a,b in zip(errors,errors[1:]))
    assert errors[-1]<1.e-5*abs(expected)


def test_local_gram_divergence_and_mass_reverse_chain_matches_exact_matrix_direction():
    g=geometry();m=metric(g);r=FrontPressureVariation(g,m,P);zero=m.zero
    direct=sum((x*y for x,y in zip(r.mass_gradient,m.mass_rate)),zero)
    direct+=sum((r.kinetic_gradient[i][j]*g.kinetic_rate[i][j] for i in range(4) for j in range(4)),zero)
    local=sum((r.mass_gradient[i]*m.mass_rate[i] for i in range(4)),zero)
    for row,owner in enumerate(g.active):
        local+=sum((r.gram_gradients[row][i][j]*g.forms[owner]['gram_rate'][i][j] for i in range(3) for j in range(3)),zero)
        local+=sum((x*y for x,y in zip(r.divergence_gradients[row],g.divergence_rate[row])),zero)
    assert local==direct==m.evaluate(P,PD)['geometry_time_work']
    # A metric-only derivative is not the full geometry force.
    incomplete=sum((r.kinetic_gradient[i][j]*g.metric_rate[i][j] for i in range(4) for j in range(4)),zero)
    assert incomplete!=direct


def test_inactive_dry_owner_has_no_invented_velocity_or_wetting_force():
    fan=AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0),gravity=1)
    fragments=(rectangle(x0=-1,x1=0,y0=0,y1=1,slope=(0,0),bed=0),
               rectangle(x0=1,x1=2,y0=0,y1=1,slope=(0,0),bed=0))
    g=FrontPressureGeometry(fan,fragments,F(1,10),outer_boundary='reflecting')
    assert g.active==(0,)
    r=FrontPressureVariation(g,metric(g),((F(1,3),F(1,4)),))
    assert any(x is None for x in r.face_column_gradients)
    result=r.time_work(((0,0),))
    assert result['energy_direction']==metric(g).evaluate(((F(1,3),F(1,4)),),((0,0),))['kinetic_energy_rate']
    direction=[(0,0) for _ in g.faces]
    direction[next(i for i,x in enumerate(r.face_column_gradients) if x is None)]=(F(1,10**400),0)
    with pytest.raises(ValueError,match='Dry pressure topology'):
        r.work(((0,0),),((0,0,0),),direction,((0,0),))


def test_primitive_shapes_wrong_metric_and_corrupt_pole_are_rejected():
    g=geometry();m=metric(g);r=FrontPressureVariation(g,m,P)
    with pytest.raises(ValueError,match='primitive direction'):r.work((),(),(),())
    with pytest.raises(ValueError,match='directed column'):
        r.work(P,((0,0,0),(0,0,0)),(),P)
    m.mass=tuple(x*2 for x in m.mass)
    with pytest.raises(ValueError,match='Matching original'):FrontPressureVariation(g,m,P)
    m=metric(g);m.poles[0]['matrix'][0][0]+=1
    with pytest.raises(ValueError,match='pole residual'):FrontPressureVariation(g,m,P)


def test_positive_subfloat_pressure_work_and_empty_dry_state_are_retained():
    depth=F(1,10**400)
    fan=AffineDryFan((0,0),(1,0),depth,(0,0),0,(0,0),gravity=1)
    wet=rectangle(x0=-2,x1=-1,y0=0,y1=1,slope=(0,0),bed=0)
    g=FrontPressureGeometry(fan,(wet,),1,outer_boundary='reflecting')
    p=((g.volumes[0],2*g.volumes[0]),);r=FrontPressureVariation(g,metric(g),p)
    result=r.work(((0,0),),((depth,2*depth**2,3*depth**3),),
                  [f['column_normal'] for f in g.faces],((0,0),))
    assert result['energy_direction']<0 and float(result['energy_direction'])==0
    # The uniform single-cell closed contour has zero divergence: its
    # first pressure-column derivative is exactly zero, not underflow.
    assert all(x==0 for row in r.face_column_gradients for x in row)
    front=rectangle(x0=-1,x1=1,y0=0,y1=1,slope=(0,0),bed=0)
    fg=FrontPressureGeometry(fan,(front,),1,outer_boundary='reflecting')
    r=FrontPressureVariation(fg,metric(fg),((fg.volumes[0],2*fg.volumes[0]),))
    assert any(x!=0 and float(x)==0 for row in r.face_column_gradients for x in row)
    direction=(tuple(k*x for k,x in enumerate(fg.forms[0]['depth_moments'][1:],1)),)
    result=r.work(((0,0),),direction,[f['column_normal'] for f in fg.faces],((0,0),))
    assert result['energy_direction']<0 and float(result['energy_direction'])==0
    dry=rectangle(x0=2,x1=3,y0=0,y1=1,slope=(0,0),bed=0)
    empty=FrontPressureGeometry(fan,(dry,),1,outer_boundary='reflecting')
    er=FrontPressureVariation(empty,metric(empty),())
    assert er.depth_moment_gradients==() and all(x is None for x in er.face_column_gradients)
    assert er.time_work(())['energy_direction']==0


def test_original_owner_order_does_not_change_the_pressure_derivative():
    g=geometry()
    fan=AffineDryFan((0,0),(3,4),1,(F(1,3),-F(1,4)),2,(F(1,5),-F(1,7)),gravity=1)
    other=FrontPressureGeometry(fan,tuple(reversed(g.fragments)),F(1,5),outer_boundary='reflecting')
    original=FrontPressureVariation(g,metric(g),P)
    reordered=FrontPressureVariation(other,metric(other),tuple(reversed(P)))
    assert reordered.depth_moment_gradients==tuple(reversed(original.depth_moment_gradients))
    assert reordered.bed_gradient_gradients==tuple(reversed(original.bed_gradient_gradients))
    assert reordered.momentum_gradient==tuple(reversed(original.momentum_gradient))
    for face,value in zip(g.faces,original.face_column_gradients):
        candidates=[(f,v) for f,v in zip(other.faces,reordered.face_column_gradients)
                    if set((f['first'],f['last']))==set((face['first'],face['last']))]
        assert len(candidates)==1
        other_face,other_value=candidates[0]
        assert other_value==(value if other_face['first']==face['first'] else tuple(-x for x in value))
    assert reordered.time_work(tuple(reversed(PD)))['energy_direction']==original.time_work(PD)['energy_direction']
