from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest

from subcell_affine_dry_fan import AffineDryFan
from subcell_prescribed_mass_pressure import PrescribedMassPressurePair
from test_subcell_affine_dry_fan import rectangle
from test_subcell_affine_front_pressure import fixture
from test_subcell_front_auxiliary_transport import U, V


def make(fan=None, fragments=None, time=None):
    if fan is None:
        fan, fragments, time = fixture()
    return PrescribedMassPressurePair(fan, fragments, time, boundary='prescribed-fan-velocity')


@pytest.fixture(scope='module')
def op():
    return make()


def independent_flux_quadrature(fan, time, first, last):
    # Direct analytic shallow-water profile, no face_flux/profile/column helper.
    n, u, slope = (np.array(tuple(map(float, a))) for a in (fan.normal, fan.velocity, fan.gradient))
    origin = np.array(tuple(map(float, fan.origin)))
    a, b = np.array(tuple(map(float, first[:2]))), np.array(tuple(map(float, last[:2])))
    g, h, t, n2 = float(fan.gravity), float(fan.depth), float(time), n@n
    un, c = u@n, np.sqrt(g*h*n2)
    shift = g*(n@slope)*t*t/2
    head, front = (un-c)*t-shift, (un+2*c)*t-shift
    qa, qb = n@(a-origin), n@(b-origin)
    cuts = [0., 1.]
    if qa != qb:
        cuts += [s for q in (head, front) if 0 < (s := (q-qa)/(qb-qa)) < 1]
    normal = np.array((b[1]-a[1], a[0]-b[0]))
    result = 0.
    nodes, weights = np.polynomial.legendre.leggauss(6)
    cuts.sort()
    for lo, hi in zip(cuts, cuts[1:]):
        for node, weight in zip(nodes, weights):
            s = (lo+hi)/2+(hi-lo)*node/2
            q = qa+s*(qb-qa)
            if q >= front:
                continue
            if q <= head:
                depth, velocity = h, u-g*slope*t
            else:
                xi = (q+shift)/t
                depth = (un+2*c-xi)**2/(9*g*n2)
                velocity = u-un*n/n2+n*(un+2*c+2*xi)/(3*n2)-g*slope*t
            result += weight*(hi-lo)/2*depth*(normal@velocity)
    return result


def test_original_continuous_profile_flux_and_all_owner_volume_rates(op):
    c, m = op.connections, op.metric
    p = m.vector(op.original_momentum)
    canonical = m.pairs(m.solve_physical.solve(tuple(a-b for a, b in zip(p, m.offset))))
    assert op.physical_momentum(canonical) == op.original_momentum
    assert op.physical_momentum(canonical) == m.physical_momentum(canonical)
    result = op.apply((F(4,7), -F(3,5)), canonical)
    assert result['mass']['active_volume_rate'] == c.geometry.volume_rates
    fan, fragments, time = fixture()
    direct = tuple(fan.boundary_rates(f, time)['volume_rate'] for f in fragments)
    assert result['mass']['volume_rate'] == direct
    assert any(f['profile_lift'] != 0 for f in op.shared_faces)
    for face, flux in zip(op.shared_faces, result['mass']['shared_fluxes']):
        assert flux == face['original_flux']
        expected = independent_flux_quadrature(fan, time, face['first'], face['last'])
        assert float(flux) == pytest.approx(expected, rel=3e-12, abs=3e-12)
    assert not result['full_nonlinear_or_total_energy_or_boundary_or_gameplay_accepted']


def test_local_face_coefficients_and_pressure_use_original_physical_map(op):
    c, m, z = op.connections, op.metric, op.zero
    phi = (F(4,7), -F(3,5))
    result = op.apply(phi, U)
    force = [z]*c.velocity_size
    for face in op.shared_faces:
        left, right = face['rows']
        for owner in (left, right):
            for axis in range(2):
                force[2*owner+axis] += ((phi[left]-phi[right])*face['column_normal'][axis]
                                      /(2*c.geometry.volumes[owner]))
    expected = m.action(m.physical, force)
    actual = m.vector(result['physical_momentum_rhs_contribution'])
    assert actual == expected
    assert actual != tuple(mass*a for mass, a in zip(m.mass, force))  # No unfiltered shallow-water substitution.
    assert all(a != 0 for a in actual)  # Both physical components matter.
    # Independently debit/credit the same shared face, then add each exterior.
    p = m.vector(result['physical_momentum'])
    local = [z]*len(c.geometry.active)
    for face in op.shared_faces:
        left, right = face['rows']
        velocity = tuple((p[2*left+k]/c.geometry.volumes[left]+p[2*right+k]/c.geometry.volumes[right])/2 for k in range(2))
        flux = op.dot(face['column_normal'], velocity)+face['profile_lift']
        local[left] -= flux
        local[right] += flux
    for face, flux in zip(c.trace.boundary_faces, c.fluxes):
        local[face['row']] -= flux
    assert tuple(local) == result['mass']['active_volume_rate']


def test_augmented_adjoint_matches_exact_mass_directional_derivative(op):
    c, z = op.connections, op.zero
    phi, step = (F(4,7), -F(3,5)), F(1,13)
    q = tuple(F(i-2,17) for i in range(len(c.fluxes)))
    dq = tuple(F(3-i,11) for i in range(len(c.fluxes)))
    result = op.apply(phi, U, q)
    values = []
    for sign in (-1, 1):
        velocity = tuple(tuple(a+sign*step*b for a, b in zip(u,v)) for u,v in zip(U,V))
        flux = tuple(a+sign*step*b for a,b in zip(q,dq))
        rates = op.mass_rates(op.physical_momentum(velocity,flux),flux)['active_volume_rate']
        values.append(op.dot(phi, rates))
    derivative = (values[1]-values[0])/(2*step)
    assert derivative == -op.dot(c.state(V,dq),result['augmented_action'])
    assert result['prescribed_flux_coordinate_work'] != 0
    assert result['prescribed_profile_lift_work'] != 0
    assert (result['potential_covector_rate']+result['pressure_work']
            +result['prescribed_flux_coordinate_work']+result['prescribed_profile_lift_work']) == z
    assert result['potential_covector_rate']+result['pressure_work'] != 0
    assert result['mass']['total_outward_mass_flux'] == sum(q,z)  # Signed inflow is retained.


def test_constant_head_and_potential_datum_do_not_manufacture_internal_force(op):
    c, z = op.connections, op.zero
    phi, datum = (F(4,7), -F(3,5)), F(17,3)
    constant = op.apply((datum,datum),U)
    assert all(a == 0 for a in c.profile.vector(constant['physical_momentum_rhs_contribution']))
    assert constant['boundary_flux_action'] == (z+datum,)*len(c.fluxes)
    assert constant['prescribed_profile_lift_work'] == 0
    first, shifted = op.apply(phi,U), op.apply(tuple(x+datum for x in phi),U)
    assert first['physical_momentum_rhs_contribution'] == shifted['physical_momentum_rhs_contribution']
    assert shifted['prescribed_profile_lift_work'] == first['prescribed_profile_lift_work']
    assert shifted['potential_covector_rate']-first['potential_covector_rate'] == -datum*sum(c.fluxes,z)


def test_prescribed_profile_lift_is_not_hidden_by_using_pressure_jet_divergence(op):
    c, m = op.connections, op.metric
    layer = m.pairs(tuple(p/mass for p,mass in zip(m.vector(op.original_momentum),m.mass)))
    wrong = tuple(-volume*d for volume,d in zip(c.geometry.volumes,c.apply_divergence(c.state(layer))))
    assert wrong != c.geometry.volume_rates
    mean_only = tuple(-op.dot(row,m.vector(op.original_momentum)) for row in op.mass_map)
    mean_only = list(mean_only)
    for face,q in zip(c.trace.boundary_faces,c.fluxes):
        mean_only[face['row']] -= q
    assert tuple(mean_only) != c.geometry.volume_rates


def test_winding_and_exterior_subdivision_preserve_physical_work(op):
    fan, fragments, time = fixture()
    phi = (F(4,7), -F(3,5))
    reference = op.apply(phi,U)
    reverse = tuple(replace(f,polygon=tuple(reversed(f.polygon))) for f in fragments)
    assert make(fan,reverse,time).apply(phi,U) == reference
    a,b,*rest = fragments[0].polygon
    middle = tuple((x+y)/2 for x,y in zip(a,b))
    split = (replace(fragments[0],polygon=(a,middle,b,*rest)),*fragments[1:])
    changed = make(fan,split,time).apply(phi,U)
    for key in ('physical_momentum_rhs_contribution','potential_covector_rate','pressure_work',
                'prescribed_flux_coordinate_work','prescribed_profile_lift_work'):
        assert changed[key] == reference[key]
    assert changed['mass']['volume_rate'] == reference['mass']['volume_rate']


def test_dry_owners_and_positive_subfloat_volumes_keep_original_identity():
    fan = AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0),gravity=1)
    t,eps = F(1,10),F(1,10**400)
    wet = rectangle(x0=2*t-eps,x1=2*t,y0=0,y1=1)
    dry = rectangle(x0=4,x1=5)
    tiny = make(fan,(wet,dry),t)
    assert tiny.connections.geometry.active == (0,)
    assert tiny.connections.geometry.volumes[0] > 0 and float(tiny.connections.geometry.volumes[0]) == 0
    result = tiny.apply((F(2,3),),(U[0],))
    assert len(result['mass']['volume_rate']) == 2 and result['mass']['volume_rate'][1] == 0
    empty = make(fan,(dry,),t).apply((),())
    assert empty['mass']['volume_rate'] == (fan.zero,)
    assert empty['augmented_action'] == ()


def test_invalid_coordinates_are_rejected_without_clipping(op):
    fan,fragments,time = fixture()
    with pytest.raises(ValueError):
        PrescribedMassPressurePair(fan,fragments,time,boundary='radiation')
    for bad in ((),(1,),(float('nan'),0)):
        with pytest.raises(ValueError):op.apply(bad,U)
    for bad in ((),(U[0],),((float('inf'),0),U[1])):
        with pytest.raises(ValueError):op.apply((1,2),bad)
    for bad in ((),(float('inf'),)*len(op.connections.fluxes)):
        with pytest.raises(ValueError):op.apply((1,2),U,bad)


@pytest.mark.parametrize('normal',[(1,0),(3,4),(-2,1)])
@pytest.mark.parametrize('velocity',[(F(2,5),-F(1,7)),(-F(3,5),F(2,7))])
def test_varied_original_oriented_fans_reproduce_continuous_fluxes(normal,velocity):
    from subcell_exact_geometry import clip
    fan = AffineDryFan((0,0),normal,F(3,4),velocity,3,(F(1,5),-F(1,8)))
    source = rectangle(x0=-F(2,5),x1=F(2,5),slope=fan.gradient,bed=3)
    fragments = tuple(replace(source,source_id=i,polygon=clip(source.polygon,0,F(1,10),side))
                      for i,side in enumerate((False,True)))
    time = F(1,5)
    pair = make(fan,fragments,time)
    c,m = pair.connections,pair.metric
    p = m.vector(pair.original_momentum)
    v = m.pairs(m.solve_physical.solve(tuple(a-b for a,b in zip(p,m.offset))))
    actual = pair.apply((F(2,3),-F(5,11)),v)
    assert actual['mass']['active_volume_rate'] == c.geometry.volume_rates
    for face,flux in zip(pair.shared_faces,actual['mass']['shared_fluxes']):
        assert float(flux) == pytest.approx(independent_flux_quadrature(fan,time,face['first'],face['last']),rel=4e-12,abs=4e-12)
    for face,flux in zip(c.trace.boundary_faces,actual['mass']['exterior_mass_flux']):
        assert float(flux) == pytest.approx(independent_flux_quadrature(fan,time,face['first'],face['last']),rel=4e-12,abs=4e-12)


def test_stationary_flat_lake_pair_has_no_mass_or_pressure_change():
    fan = AffineDryFan((0,0),(1,0),1,(0,0),2,(0,0),gravity=1)
    fragments = (rectangle(x0=-4,x1=-3,bed=2),rectangle(x0=-3,x1=-2,bed=2))
    pair = make(fan,fragments,F(1,10))
    result = pair.apply((3,3),((0,0),(0,0)))
    assert result['mass']['volume_rate'] == (0,0)
    assert result['mass']['prescribed_profile_lift'] == (0,0)
    assert result['physical_momentum_rhs_contribution'] == ((0,0),(0,0))
    assert result['potential_covector_rate'] == result['pressure_work'] == 0
    assert result['prescribed_flux_coordinate_work'] == result['prescribed_profile_lift_work'] == 0
