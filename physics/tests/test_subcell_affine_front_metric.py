from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_affine_dry_fan import AffineDryFan
from subcell_affine_front_metric import front_metric, metric_work
from subcell_exact_geometry import clip
from test_subcell_affine_dry_fan import rectangle


@pytest.mark.parametrize('slope',[-F(1,5),0,F(1,4)])
def test_curved_depth_moments_match_independent_branch_quadrature(slope):
    fan=AffineDryFan((0,0),(1,0),F(3,4),(F(2,5),0),3,(slope,0))
    t=F(1,5);source=rectangle(slope=(slope,0),bed=3)
    result=front_metric(fan,source,t)
    assert result['depth_moment_rates'][0]==fan.boundary_rates(source,t)['volume_rate']
    g=float(fan.gravity);dt=float(t);c=np.sqrt(g*.75);u=.4
    head=(u-c)*dt-g*float(slope)*dt*dt/2
    front=(u+2*c)*dt-g*float(slope)*dt*dt/2
    def depth(x):
        if x<=head:return .75
        if x>=front:return 0.
        return (u+2*c-x/dt-g*float(slope)*dt/2)**2/(9*g)
    points=[x for x in (head,front) if -2<x<2]
    for k in range(4):
        expected=quad(lambda x:depth(x)**k if k else float(x<front),-2,2,points=points,epsabs=1e-12)[0]
        assert float(result['depth_moments'][k])==pytest.approx(expected,rel=2e-13,abs=1e-13)
    jet=(F(1,3),-F(2,5),F(1,7))
    bdot=float(slope*jet[1]);d=float(jet[0])
    expected=quad(lambda x:.5*depth(x)*((depth(x)*d-1.5*bdot)**2+.75*bdot*bdot),
                  -2,2,points=points,epsabs=1e-12)[0]
    assert float(metric_work(result,jet)['energy'])==pytest.approx(expected,rel=2e-13,abs=1e-13)


def test_original_source_partition_and_winding_preserve_exact_metric_and_rate():
    fan=AffineDryFan((0,0),(3,4),F(7,10),(F(1,3),-F(1,4)),2,(F(1,5),-F(1,7)))
    source=rectangle(slope=fan.gradient,bed=2);t=F(1,5)
    whole=front_metric(fan,source,t)
    parts=[front_metric(fan,replace(source,polygon=clip(source.polygon,0,F(1,5),side)),t)
           for side in (False,True)]
    reversed_form=front_metric(fan,replace(source,polygon=tuple(reversed(source.polygon))),t)
    for key in ('depth_moments','depth_moment_rates','depth_moment_rate_scales'):
        assert tuple(a+b for a,b in zip(parts[0][key],parts[1][key]))==whole[key]
        assert reversed_form[key]==whole[key]
    for key in ('gram','gram_rate'):
        for i in range(3):
            for j in range(3):
                assert parts[0][key][i][j]+parts[1][key][i][j]==whole[key][i][j]
                assert whole[key][i][j]==whole[key][j][i]==reversed_form[key][i][j]


def test_oblique_bed_cross_terms_match_independent_positive_tensor_quadrature():
    fan=AffineDryFan((0,0),(3,4),F(7,10),(F(1,3),-F(1,4)),2,(F(1,5),-F(1,7)))
    source=rectangle(x0=-F(1,5),x1=F(2,5),slope=fan.gradient,bed=2);t=F(1,5)
    jet=(F(1,3),-F(2,5),F(1,7));result=metric_work(front_metric(fan,source,t),jet)
    g=9.81;dt=.2;normal=np.array([3.,4.]);slope=np.array([.2,-1/7])
    c=np.sqrt(g*.7*25);acceleration=g*float(normal@slope)
    d=float(jet[0]);bu=float(slope@np.array(list(map(float,jet[1:]))))
    nodes,weights=np.polynomial.legendre.leggauss(4);energy=rate=0.
    for a,wa in zip(nodes,weights):
        for b,wb in zip(nodes,weights):
            x,y=.1+.3*a,.5*b;q=3*x+4*y;xi=q/dt+acceleration*dt/2
            assert -c<xi<2*c  # Entire chosen rectangle is inside the curved fan.
            L=2*c-xi;h=L*L/(9*g*25);ht=2*L*(q/(dt*dt)-acceleration/2)/(9*g*25)
            weight=.15*wa*wb
            energy+=weight*.5*h*((h*d-1.5*bu)**2+.75*bu*bu)
            rate+=weight*.5*ht*(3*h*h*d*d-6*h*d*bu+3*bu*bu)
    assert float(result['energy'])==pytest.approx(energy,rel=2e-13,abs=1e-14)
    assert float(result['metric_time_work'])==pytest.approx(rate,rel=2e-13,abs=1e-14)


def test_metric_and_jet_time_work_match_independent_refined_energy_difference():
    fan=AffineDryFan((0,0),(3,4),F(7,10),(F(1,3),-F(1,4)),2,(F(1,5),-F(1,7)))
    source=rectangle(x0=-F(1,5),x1=F(2,5),slope=fan.gradient,bed=2);t=F(1,5)
    jet=(F(1,3),-F(2,5),F(1,7));rate=(F(1,2),F(1,7),-F(1,3))
    work=metric_work(front_metric(fan,source,t),jet,rate)
    assert work['metric_time_work']!=0 and work['jet_time_work']!=0
    errors=[]
    for divisor in (100,200,400,800):
        eps=t/divisor
        values=[metric_work(front_metric(fan,source,t+sign*eps),
                            tuple(a+sign*eps*b for a,b in zip(jet,rate)))['energy'] for sign in (-1,1)]
        errors.append(abs(float((values[1]-values[0])/(2*eps)-work['energy_rate'])))
    assert all(a/b>3.8 for a,b in zip(errors,errors[1:]))
    assert errors[-1]<1e-7


def test_cubic_metric_cannot_be_replaced_by_mean_depth_and_volume():
    fan=AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0))
    form=front_metric(fan,rectangle(x0=0,x1=F(1,2)),F(1,5))
    area,volume,_,third=form['depth_moments']
    assert area>0 and volume>0 and third>volume*volume*volume/(area*area)
    assert form['gram'][0][0]==third


def test_subfloat_positive_front_metric_and_zero_dry_metric_are_not_clipped():
    fan=AffineDryFan((0,0),(1,0),F(2,10**400),(0,0),0,(0,0),gravity=1)
    tiny=front_metric(fan,rectangle(),F(1,10**200))
    assert tiny['gram'][0][0]>0 and float(tiny['gram'][0][0])==0
    assert metric_work(tiny,(1,0,0))['energy']>0
    dry=front_metric(fan,rectangle(x0=10,x1=11),F(1,10**200))
    assert dry['depth_moments']==(0,0,0,0)
    assert dry['depth_moment_rates']==(0,0,0)
    assert metric_work(dry,(1,2,3),(3,2,1))['energy_rate']==0


def test_wrong_source_plane_time_and_jet_are_rejected():
    fan=AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0))
    for t in (0,-1):
        with pytest.raises(ValueError):front_metric(fan,rectangle(),t)
    with pytest.raises(ValueError):front_metric(fan,rectangle(bed=1),F(1,5))
    with pytest.raises(ValueError):metric_work(front_metric(fan,rectangle(),F(1,5)),(1,2))


def test_time_check_rejects_corrupted_metric_rate_and_subfloat_ghost():
    from audit_south_fork_affine_front_metric import temporal_metric_check
    fan=AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0));source=rectangle();t=F(1,10)
    form=front_metric(fan,source,t)
    assert temporal_metric_check(fan,source,t,form)['passed']
    bad=dict(form,depth_moment_rates=(form['depth_moment_rates'][0]+1,*form['depth_moment_rates'][1:]))
    assert not temporal_metric_check(fan,source,t,bad)['passed']
    dry_source=rectangle(x0=10,x1=11);dry=front_metric(fan,dry_source,t)
    bad=dict(dry,depth_moment_rates=(fan.zero+F(1,10**400),fan.zero,fan.zero))
    assert not temporal_metric_check(fan,dry_source,t,bad)['passed']
