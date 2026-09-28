from dataclasses import replace
from fractions import Fraction as F

import pytest

from subcell_affine_dry_fan import AffineDryFan
from subcell_prescribed_physical_transport import PrescribedPhysicalTransport
from test_subcell_affine_dry_fan import rectangle
from test_subcell_affine_front_pressure import fixture
from test_subcell_front_auxiliary_transport import U, V
from test_subcell_prescribed_auxiliary_advection import quadrature


def make(fan=None, fragments=None, time=None):
    if fan is None:
        fan, fragments, time = fixture()
    return PrescribedPhysicalTransport(fan, fragments, time, boundary='prescribed-fan-velocity')


def dot(a, b, zero):
    assert len(a) == len(b)
    return sum((x*y for x, y in zip(a, b)), zero)


def test_original_physical_energy_and_poles_match_independent_affine_metric():
    op = make(); c, m = op.connections, op.metric
    actual = op.apply(U)
    reference = m.evaluate(m.physical_momentum(U), ((0, 0),)*len(c.geometry.active))
    assert actual['kinetic_energy'] == reference['kinetic_energy']
    assert len(actual['poles']) == 2
    for got, expected in zip(actual['poles'], reference['poles']):
        assert c.profile.pairs(got['auxiliary_state'][:c.velocity_size]) == expected['auxiliary_velocity']
        assert got['length'] == expected['length'] and got['weight'] == expected['weight']
    assert not actual['full_momentum_or_total_energy_or_inflow_or_gameplay_accepted']
    assert actual['spatial_operator_rhs_sign'] == -1
    assert dot(c.profile.vector(U), c.profile.vector(actual['physical_momentum_rhs_contribution']), c.zero) == -actual['interior_work']


def test_auxiliary_map_transpose_preserves_arbitrary_velocity_and_flux_work():
    op = make(); c = op.connections
    state = c.state(U, tuple(F(i+1, 19) for i in range(len(c.fluxes))))
    force = c.state(V, tuple(F(2-i, 13) for i in range(len(c.fluxes))))
    for pole in op.metric.poles:
        mapped = op.auxiliary_state(state, pole)
        pulled = op.pullback(force, pole)
        assert dot(mapped, force, c.zero) == dot(state, pulled, c.zero)
        assert pulled[c.velocity_size:] != force[c.velocity_size:]  # Nonzero exterior adjoint matters.
        dv = c.state(V, (0,)*len(c.fluxes))
        dq = c.state(((0, 0),)*len(c.geometry.active), state[c.velocity_size:])
        assert op.auxiliary_state(tuple(a+b for a,b in zip(dv,dq)), pole) == tuple(
            a+b for a,b in zip(op.auxiliary_state(dv,pole),op.auxiliary_state(dq,pole)))


def test_full_weighted_boundary_work_and_cross_state_identity_match_pointwise_quadrature():
    fan, fragments, time = fixture(); op = make(fan, fragments, time); c = op.connections
    qu, qv = c.fluxes, tuple(F(i+1, 23) for i in range(len(c.fluxes)))
    ru, rv = op.apply(U, qu), op.apply(V, qv)
    yu, yv = c.state(U, qu), c.state(V, qv)
    mass_u = op.transport.exterior(U, qu, channel='difference')
    mass_v = op.transport.exterior(V, qv, channel='difference')
    expected_cross = 0.
    for face_index, (fu, fv) in enumerate(zip(mass_u['faces'], mass_v['faces'])):
        own = float(op.metric.constant)*quadrature(fan,time,fu,fu['jet'],fu['jet'],'difference')/2
        cross = float(op.metric.constant)*quadrature(fan,time,fu,fu['jet'],fv['jet'],'difference')
        for pu, pv in zip(ru['poles'], rv['poles']):
            a, b = pu['auxiliary_state'], pv['auxiliary_state']
            au = op.transport.exterior(c.profile.pairs(a[:c.velocity_size]),a[c.velocity_size:],channel='factor')['faces'][face_index]
            av = op.transport.exterior(c.profile.pairs(b[:c.velocity_size]),b[c.velocity_size:],channel='factor')['faces'][face_index]
            for channel, coefficient in (('difference',pu['weight']),('factor',pu['weight']*pu['length'])):
                own += float(coefficient)*quadrature(fan,time,au,au['jet'],au['jet'],channel)/2
                cross += float(coefficient)*quadrature(fan,time,au,au['jet'],av['jet'],channel)
        assert float(ru['faces'][face_index]['outward_kinetic_flux']) == pytest.approx(own,abs=3e-11)
        expected_cross += cross
    actual_cross = dot(yv,ru['augmented_action'],c.zero)+dot(yu,rv['augmented_action'],c.zero)
    assert float(actual_cross) == pytest.approx(expected_cross,abs=3e-10)
    assert ru['interior_work']+ru['flux_coordinate_work'] == ru['outward_kinetic_flux']
    assert ru['flux_coordinate_work'] != 0
    assert any(f['outward_kinetic_flux']<0 for f in ru['faces'])
    assert any(f['outward_kinetic_flux']>0 for f in ru['faces'])


def test_winding_and_exterior_subdivision_preserve_owner_force_and_work():
    fan, fragments, time = fixture()
    reference = make(fan,fragments,time).apply(U)
    reverse = tuple(replace(f,polygon=tuple(reversed(f.polygon))) for f in fragments)
    assert make(fan,reverse,time).apply(U) == reference
    a,b,*rest = fragments[0].polygon
    middle = tuple((x+y)/2 for x,y in zip(a,b))
    split = (replace(fragments[0],polygon=(a,middle,b,*rest)),*fragments[1:])
    changed = make(fan,split,time).apply(U)
    for key in ('physical_momentum_rhs_contribution','interior_work','flux_coordinate_work','outward_kinetic_flux','kinetic_energy'):
        assert changed[key] == reference[key]


def test_stationary_flat_plateau_reduces_to_original_zero_mode():
    fan = AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0),gravity=1)
    op = make(fan,(rectangle(x0=-3,x1=-2),),F(1,10)); c,m = op.connections,op.metric
    result = op.apply((U[0],))
    assert all(a==0 for a in result['augmented_action'])
    zero_mode = m.constant+sum((p['weight'] for p in m.poles),c.zero)
    assert result['kinetic_energy'] == zero_mode*sum((mass*v*v/2 for mass,v in zip(m.mass,U[0])),c.zero)


def test_dry_removal_and_positive_subfloat_water_are_preserved():
    fan = AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0),gravity=1)
    t,eps = F(1,10),F(1,10**400)
    wet = rectangle(x0=2*t-eps,x1=2*t,y0=0,y1=1); dry = rectangle(x0=4,x1=5)
    op = make(fan,(wet,dry),t); result = op.apply((U[0],))
    assert op.connections.geometry.active == (0,)
    assert result['kinetic_energy'] > 0 and float(result['kinetic_energy']) == 0
    empty = make(fan,(dry,),t).apply(())
    assert empty['kinetic_energy'] == 0 and empty['augmented_action'] == ()


def test_invalid_coordinates_and_boundary_fail_closed():
    fan,fragments,time = fixture()
    with pytest.raises(ValueError):
        PrescribedPhysicalTransport(fan,fragments,time,boundary='radiation')
    op = make(); c = op.connections
    for bad in ((),(U[0],),((float('nan'),0),U[1])):
        with pytest.raises(ValueError):op.apply(bad)
    for bad in ((),(float('inf'),)*len(c.fluxes)):
        with pytest.raises(ValueError):op.apply(U,bad)
    for pole in op.metric.poles:
        with pytest.raises(ValueError):op.pullback((),pole)
        with pytest.raises(ValueError):op.auxiliary_state((),pole)


def test_prescribed_time_ledger_exposes_uncanceled_power_and_matches_fresh_time_derivative():
    fan,fragments,time = fixture(); op = make(fan,fragments,time)
    ledger = op.prescribed_kinetic_ledger(U); result = ledger['transport']
    assert ledger['remaining_geometry_and_port_power'] != 0
    assert ledger['kinetic_energy_rate']+result['outward_kinetic_flux'] == ledger['remaining_geometry_and_port_power']
    assert not ledger['full_momentum_or_total_energy_or_inflow_or_gameplay_accepted']
    p = op.metric.vector(ledger['physical_momentum'])
    rhs = op.metric.vector(result['physical_momentum_rhs_contribution'])
    expected = float(ledger['kinetic_energy_rate'])
    errors = []
    for step in (F(1,10000),F(1,20000)):
        energies = []
        for sign in (-1,1):
            fresh = make(fan,fragments,time+sign*step)
            advanced = tuple(a+sign*step*b for a,b in zip(p,rhs))
            state = fresh.metric.evaluate(fresh.metric.pairs(advanced),((0,0),)*len(fresh.connections.geometry.active))
            energies.append(state['kinetic_energy'])
        derivative = float((energies[1]-energies[0])/(2*step))
        errors.append(abs(derivative-expected))
    assert errors[1] < 1e-5
    assert errors[1] <= .3*errors[0]+1e-10
