import numpy as np
import pytest
from breaking_front_reference import dispersion_fraction, plateau_signs, surface_jumps
from total_depth_pressure import wet_pairs
from total_depth_nonlinear_pressure import AccelerationSystem, nonlinear_pressure_force
from total_depth_bank_replay import advance, rate


def test_surface_jump_retains_thin_film_after_large_neighbor_eta_cancellation():
    tiny=2.**-149
    h=np.array([[tiny,1.,1.,tiny]]);bed=np.array([[0.,-1.,-1.,0.]])
    np.testing.assert_array_equal(surface_jumps(h,bed,1),[[-tiny,0,tiny,0]])
    np.testing.assert_array_equal(surface_jumps(h.T,bed.T,0),surface_jumps(h,bed,1).T)


def test_subnormal_connected_front_requires_a_real_rate_or_slope_trigger():
    h=np.full((1,64),2.**-149);h[:,20:40]=3*2.**-149
    pairs=[np.ones_like(h,dtype=bool),np.zeros_like(h,dtype=bool)]
    _,quiet=dispersion_fraction(h,h*0,h*0,pairs,1.)
    _,forced=dispersion_fraction(h,h*0,h*0+1,pairs,1.)
    assert quiet['detected_fronts']==0
    assert forced['detected_fronts']==forced['subcell_fronts']==2


def test_internal_flat_faces_join_only_equal_connected_directions():
    graph = np.ones(8,dtype=bool)
    jumps = np.array([-1.,0.,0.,-2.,1.,0.,-1.,1.])
    np.testing.assert_array_equal(plateau_signs(jumps,graph),[-1,-1,-1,-1,1,0,-1,1])
    graph[1] = False
    np.testing.assert_array_equal(plateau_signs(jumps,graph),[-1,0,0,-1,1,0,-1,1])
    np.testing.assert_array_equal(plateau_signs(np.zeros(8),np.ones(8,dtype=bool)),0)
    tiny = jumps.copy(); tiny[1] = 1e-30
    assert plateau_signs(tiny,np.ones(8,dtype=bool))[1] == 1


def test_plateau_front_and_observer_preserve_full_physical_band():
    # Variable bed: an internal flat eta face must not move the depth sampled
    # at the crest, which otherwise changes the breaking-band width abruptly.
    h = np.array([[1.,3.,2.5,2.,1.,1.]])
    eta = np.array([[0.,2.,1.5,1.5,0.,0.]])
    bed = eta-h; pairs = [np.ones_like(h,dtype=bool),np.zeros_like(h,dtype=bool)]
    fronts = []
    expected,stats = dispersion_fraction(h,bed,h*0,pairs,.5)
    actual,observed = dispersion_fraction(h,bed,h*0,pairs,.5,on_front=fronts.append)
    np.testing.assert_array_equal(actual,expected); assert stats == observed
    falling = [f for f in fronts if f['first']==1 and f['after']==4]
    assert len(falling)==1 and falling[0]['hp']==3 and falling[0]['ht']==1


def test_lake_and_uniform_downhill_sheet_are_not_breaking_fronts():
    h = np.ones((3,32)); bed = np.broadcast_to(np.arange(32)*.25,h.shape).copy()
    mu, stats = dispersion_fraction(h, bed, h*0, wet_pairs(h,bed), 1.)
    np.testing.assert_array_equal(mu,1)
    assert stats['detected_fronts'] == 0 and stats['boundary_truncated_runs'] > 0
    h = 10-bed
    mu, stats = dispersion_fraction(h,bed,h*0,wet_pairs(h,bed),1.)
    np.testing.assert_array_equal(mu,1)
    assert stats['detected_fronts'] == 0


def test_contained_steady_bore_bands_are_local_and_periodic_translation_invariant():
    h = np.ones((1,64)); h[:,20:40] = 2
    bed = np.zeros_like(h); pairs = wet_pairs(h,bed,True)
    mu, stats = dispersion_fraction(h,bed,h*0,pairs,1.)
    assert stats['detected_fronts'] == 2
    assert stats['maximum_band_width_m'] == 7.5
    np.testing.assert_allclose(stats['maximum_log10_bore_froude'],np.log10(np.sqrt(3)),atol=1e-15)
    assert np.all(mu[:,5:10] == 1) and np.all(mu[:,26:34] == 1)
    assert np.sum(1-mu) == 15
    for shift in (3,25,43):
        rotated = np.roll(h,shift,1)
        actual, _ = dispersion_fraction(rotated,bed,h*0,pairs,1.)
        np.testing.assert_allclose(actual,np.roll(mu,shift,1),atol=1e-14)


def test_subcell_front_preserves_physical_band_width_and_axis_transpose():
    h = np.ones((1,64))*.01; h[:,20:40] = .03
    bed = h*0; pairs = wet_pairs(h,bed,True)
    mu, stats = dispersion_fraction(h,bed,h*0+1,pairs,1.)
    assert stats['subcell_fronts'] == 2
    np.testing.assert_allclose(np.sum(1-mu),.3,atol=1e-14)
    assert mu.min() > 0  # No forced full-cell hydrostatic band.
    other, _ = dispersion_fraction(h.T,bed.T,h.T*0+1,[pairs[1].T,pairs[0].T],1.)
    np.testing.assert_array_equal(other,mu.T)


def test_weak_front_retains_dispersion_even_with_large_uniform_flow_rate():
    h = np.ones((1,64)); h[:,20:40] = 1.1
    mu, stats = dispersion_fraction(h,h*0,h*0+100,wet_pairs(h,h*0,True),1.)
    np.testing.assert_array_equal(mu,1)
    assert stats['detected_fronts'] == 0


@pytest.mark.parametrize('interpolation',['centered','depth_weighted'])
def test_mixed_fraction_operator_is_symmetric_positive_and_diagonal_is_exact(interpolation):
    rng = np.random.default_rng(9518)
    h = rng.uniform(.2,2,(3,5)); bed = rng.uniform(-.2,.2,h.shape)
    mu = rng.uniform(0,1,h.shape); mu[1,:2] = 0
    system = AccelerationSystem(h,bed,wet_pairs(h,bed,True),.5,1/3,
        interpolation=interpolation,dispersion_fraction=mu)
    n = h.size*2
    matrix = np.stack([system.apply(v.reshape(*h.shape,2)).ravel() for v in np.eye(n)],axis=1)
    np.testing.assert_allclose(matrix,matrix.T,atol=2e-14)
    assert np.linalg.eigvalsh(matrix).min() >= 1-1e-13
    np.testing.assert_allclose(np.diag(matrix),system.diagonal.ravel(),atol=2e-14)


def test_uniform_nonbreaking_is_identical_and_all_breaking_has_zero_pressure():
    rng = np.random.default_rng(9813)
    h = rng.uniform(.3,1,(4,8)); bed = np.zeros_like(h); u = rng.normal(size=(*h.shape,2))
    pairs = wet_pairs(h,bed,True); hydro = rng.normal(size=u.shape)
    expected, stats = nonlinear_pressure_force(h,bed,u,hydro,pairs,.5,interpolation='depth_weighted')
    actual, other = nonlinear_pressure_force(h,bed,u,hydro,pairs,.5,interpolation='depth_weighted',dispersion_fraction=h*0+1)
    np.testing.assert_array_equal(actual,expected); assert stats == other
    actual, stats = nonlinear_pressure_force(h,bed,u,hydro,pairs,.5,interpolation='depth_weighted',dispersion_fraction=h*0)
    np.testing.assert_array_equal(actual,0)
    assert all(s['iterations'] == 0 for s in stats)
    mu = rng.uniform(0,1,h.shape)
    actual, _ = nonlinear_pressure_force(h,bed,u,hydro,pairs,.5,interpolation='depth_weighted',dispersion_fraction=mu)
    np.testing.assert_allclose(actual.sum(axis=(0,1)),0,atol=2e-14)


def test_hybrid_bank_path_preserves_lake_and_validates_explicit_configuration():
    bed = np.broadcast_to(np.arange(12)*.25,(3,12)).copy()
    state = np.zeros((*bed.shape,3)); state[...,0] = np.maximum(0,2-bed)
    with pytest.raises(ValueError): rate(state,bed,.5,breaking_model='hybrid_front')
    final, stats = advance(state,bed,.5,.05,second_order=True,dispersive=True,
        pressure_model='rational_sgn',pressure_interpolation='depth_weighted',
        pressure_formulation='kinematic',pressure_bed_slope='geometry',breaking_model='hybrid_front')
    np.testing.assert_allclose(final,state,atol=2e-14)
    assert stats['pressure_solver']['maximum_breaking_cells'] == 0


def test_invalid_fraction_and_graph_rejected():
    h = np.ones((3,5)); pairs = wet_pairs(h,h*0,True)
    for mu in (h*0-1,h*0+2,h*np.nan,h[:1]):
        with pytest.raises(ValueError): AccelerationSystem(h,h*0,pairs,.5,1/3,dispersion_fraction=mu)
    for gamma in (.1,np.nan,.9):
        with pytest.raises(ValueError): dispersion_fraction(h,h*0,h*0,pairs,.5,gamma=gamma)


def test_breaking_band_cannot_cross_disconnected_wet_components():
    h = np.ones((1,64)); h[:,20:25] = 10
    pairs = wet_pairs(h,h*0,False)
    pairs[0][:,30] = False
    mu, stats = dispersion_fraction(h,h*0,h*0,pairs,1.)
    assert stats['detected_fronts'] == 2
    assert np.any(mu[:,:31] < 1)
    np.testing.assert_array_equal(mu[:,31:],1)


def test_true_tiny_trough_is_not_floored_or_overflowed():
    h = np.ones((1,64))*1e-310; h[:,20:40] = 2
    with np.errstate(over='raise',invalid='raise',divide='raise'):
        mu, stats = dispersion_fraction(h,h*0,h*0,wet_pairs(h,h*0,True),1.)
    assert stats['maximum_log10_bore_froude'] > 310
    assert np.all(np.isfinite(mu))


def test_small_nonbreaking_wave_keeps_identical_evolution():
    x = np.arange(64)*.25
    h = 1+.01*np.cos(2*np.pi*x/8)
    state = np.stack((h,.01*np.sqrt(9.81)*np.cos(2*np.pi*x/8),h*0),axis=-1)[None]
    options = dict(second_order=True,periodic=True,dispersive=True,pressure_model='rational_sgn',
        pressure_interpolation='depth_weighted',pressure_formulation='kinematic',pressure_bed_slope='geometry')
    expected, _ = advance(state,np.zeros_like(state[...,0]),.25,.05,**options)
    actual, stats = advance(state,np.zeros_like(state[...,0]),.25,.05,**options,breaking_model='hybrid_front')
    np.testing.assert_array_equal(actual,expected)
    assert stats['pressure_solver']['maximum_breaking_cells'] == 0


def test_flat_periodic_bore_loses_hydrostatic_energy_without_losing_mass_or_momentum():
    h = np.ones((1,256)); h[:,64:192] = 2
    state = np.stack((h,h*0,h*0),axis=-1)
    final, stats = advance(state,h*0,.1,.25,second_order=True,periodic=True,dispersive=True,
        pressure_model='rational_sgn',pressure_interpolation='depth_weighted',
        pressure_formulation='kinematic',pressure_bed_slope='geometry',breaking_model='hybrid_front')
    assert stats['pressure_solver']['maximum_breaking_cells'] > 0
    assert stats['final_energy_per_density_m5s2'] < stats['initial_energy_per_density_m5s2']
    assert np.all(np.isfinite(final)) and final[...,0].min() > 0
    np.testing.assert_allclose(np.sum(final-state,axis=(0,1)),0,atol=1e-12)
