import numpy as np
import pytest

from subcell_donor_face_flux import flux
from subcell_energy_flux import face_flux_normal
from subcell_source_activation import assembly, attempt
from triangle_face_section import TriangleFaceSection
from test_subcell_wet_pool_pressure import partition


def test_nearly_dry_face_cannot_have_negative_velocity_exchange():
    section = TriangleFaceSection([[[0., 0.], [1., 0.]]], [0., 1.])
    left, right = np.array([1., .3]), np.array([10., -.7])
    old, info = face_flux_normal(section, 1., left, 0., right, [1., 0.], dissipative=True)
    old_exchange = -.25*(left[0]+right[0])*info['pressure_secant_area']
    assert old[0] > 0 and old_exchange < 0
    value, record = flux(section, 1., left, 0., right, [1., 0.])
    assert record['velocity_exchange'] == 0 and record['right_donor'] == 0
    np.testing.assert_allclose(value[1:], value[0]*left+np.array([.25*9.81, 0.]), atol=1e-14)


def test_donor_flux_rotation_and_coefficient_decomposition():
    section = TriangleFaceSection([[[0., 1.], [1., 2.]]], [0., 1.])
    ul, ur = np.array([.2, -.4]), np.array([-.7, .3])
    rot = np.array([[.6, -.8], [.8, .6]])
    value, r = flux(section, 2.1, ul, 1.2, ur, [1., 0.])
    rotated, _ = flux(section, 2.1, rot@ul, 1.2, rot@ur, rot[:, 0])
    np.testing.assert_allclose(rotated, np.r_[value[0], rot@value[1:]], atol=1e-14)
    np.testing.assert_allclose(value[0], r['left_donor']-r['right_donor'], atol=1e-14)
    pressure = np.array([.5*(r['left_pressure']+r['right_pressure']), 0.])
    np.testing.assert_allclose(value[1:], r['left_donor']*ul-r['right_donor']*ur+pressure, atol=1e-14)


@pytest.mark.parametrize('seed', [1001, 1002, 1003])
def test_original_terrain_donor_rates_conserve_mass_and_dissipate_base_energy(seed):
    rng = np.random.default_rng(seed)
    pools, _, _, _ = partition(lambda x, y: .3*x+.2*y+.1*x*y,
        2.+rng.uniform(-.1, .1, (2, 3)), (2, 3), (.5, .5), (-.5, -.25))
    pools = pools.with_regions([dict(p, momentum=p['volume']*rng.normal(size=2)*.3) for p in pools.pools])
    a = assembly(pools, face_scheme='donor')
    assert not a['new_region_rates']
    assert abs(a['net_mass_rate']) < 1e-13
    assert a['momentum_boundary_bed_error'] < 1e-13
    np.testing.assert_array_equal(a['explicit_force_parts']['negative_exchange'], 0.)
    velocity = np.array([p['momentum']/p['volume'] for p in pools.pools])
    eta = np.array([p['form']['datum']+p['form']['stage_offset'] for p in pools.pools])
    gradient = 9.81*eta-.5*np.sum(velocity**2, axis=1)
    assert gradient@a['volume_rate']+np.sum(velocity*a['momentum_rate']) <= 1e-10


def test_donor_exact_terrain_lake_and_cached_scheme_identity():
    pools, _, _, _ = partition(lambda x, y: .3*x+.2*y+.1*x*y, 2., (2, 3), (.5, .5), (-.5, -.25))
    pools = pools.with_regions([dict(p, momentum=np.zeros(2)) for p in pools.pools])
    a = assembly(pools, face_scheme='donor')
    np.testing.assert_allclose(a['volume_rate'], 0., atol=1e-13)
    np.testing.assert_allclose(a['momentum_rate'], 0., atol=1e-13)
    with pytest.raises(ValueError, match='Matching'):
        attempt(pools, .02, assembled=a, scheme='coupled-frozen')
    result = attempt(pools, .02, assembled=a, scheme='coupled-donor')
    assert result['audit']['candidate_accepted'], result['audit']
