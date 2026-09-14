import numpy as np
import pytest
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate
from source_supported_scalar_boundary import SourceSupportedScalarBoundary


def fixture(n=8, dx=None, h=None):
    dx = 1/n if dx is None else dx
    y, x = np.meshgrid((np.arange(n+6)-2.5)*dx, (np.arange(n+6)-2.5)*dx, indexing='ij')
    depth = np.ones_like(x) if h is None else h(x, y)
    full = np.stack((depth, depth*(.2+x), depth*(.3+y)), axis=-1)
    bed = np.zeros_like(x)
    core = (slice(3, -3), slice(3, -3))
    g = ReconstructedPressureGeometry(depth[core], bed[core], dx, periodic=False,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')
    return SourceSupportedScalarBoundary(g, full[core], full, bed), x, y


@pytest.mark.parametrize('n', [8, 16, 32])
def test_affine_derivatives_exact_including_all_edges_and_corners(n):
    b, x, y = fixture(n)
    f = 2*x-3*y+.75
    actual = b.gradient(f[b.core], f)
    np.testing.assert_allclose(actual, np.broadcast_to([2., -3.], actual.shape), atol=2e-13, rtol=0)
    assert np.all(b.gradient(np.ones((n,n)), np.ones_like(x)) == 0)


def test_smooth_boundary_error_refines_second_order():
    errors = []
    for n in (8,16,32):
        b, x, y = fixture(n)
        f = np.sin(x)+np.cos(y)
        exact = np.stack((np.cos(x), -np.sin(y)), axis=-1)[b.core]
        errors.append(float(abs(b.gradient(f[b.core], f)-exact).max()))
    assert errors[0]/errors[1] > 3.9 and errors[1]/errors[2] > 3.9


def test_current_interior_wins_and_source_inputs_are_untouched():
    b, x, y = fixture()
    original_source = b.state.copy()
    evolved = b.state[b.core].copy(); evolved[..., 1] += .125
    changed = SourceSupportedScalarBoundary(b.original, evolved, original_source, b.extended.bed)
    np.testing.assert_array_equal(changed.state[changed.core], evolved)
    np.testing.assert_array_equal(original_source, b.state)
    mask = np.ones(x.shape, bool); mask[b.core] = False
    np.testing.assert_array_equal(changed.state[mask], original_source[mask])


def test_affine_velocity_ghost_divergence_uses_independent_face_trace():
    b, x, y = fixture()
    n = b.original.h.shape[0]
    trace = np.zeros((4*n,2))
    trace[:n,0]=.2; trace[n:2*n,0]=1.2
    trace[2*n:3*n,0]=.3; trace[3*n:,0]=1.3
    d,e=b.exterior_kinematics(trace)
    np.testing.assert_allclose(d[2:-2,2:-2],2.,atol=1e-13,rtol=0)
    np.testing.assert_array_equal(e,0.)
    changed=trace.copy(); changed[0,0]+=.125
    dd,_=b.exterior_kinematics(changed)
    assert dd[3,2]-d[3,2] == pytest.approx(.125/b.original.dx)
    tangent=PressureGeometryRate(b.original,b.original.bed,np.zeros((n,n)))
    q,c,adv=b.forcing(tangent,trace)
    np.testing.assert_allclose(adv,b.velocity[b.core],atol=1e-13,rtol=0)
    # Independently q-D(Adv)=d^2-u.grad(d)=4, c+E(Adv)=0.
    da,ea=b.original.kinematic_components(adv)
    np.testing.assert_allclose(q-da,4.,atol=1e-12,rtol=0)
    np.testing.assert_allclose(c+ea,0.,atol=1e-12,rtol=0)


def test_pressure_force_and_work_unchanged_and_dry_columns_not_repaired():
    b,x,y=fixture(h=lambda x,y:np.where(x<.25,0.,1.+x/8))
    g=b.original; rng=np.random.default_rng(335)
    p=rng.normal(size=g.h.shape); p[g.h==0]=0
    u=b.velocity[b.core]
    before=g.gradient_traction(p,np.zeros_like(p)).copy()
    b.gradient(x[b.core],x)
    np.testing.assert_array_equal(g.gradient_traction(p,np.zeros_like(p)),before)
    d,_=g.kinematic_components(u)
    assert abs(np.sum(u*before)+np.sum(p*d))<1e-12
    np.testing.assert_array_equal(b.state[...,1:][b.state[...,0]==0],0.)
    assert np.isfinite(b.gradient(x[b.core],x)).all()
    # Finite dry-support scalar action is NOT a wetting-front consistency pass.


def test_missing_halo_and_unregistered_current_depth_are_rejected():
    b,x,y=fixture()
    with pytest.raises(ValueError):
        SourceSupportedScalarBoundary(b.original,b.state[b.core],b.state[1:],b.extended.bed[1:])
    state=b.state[b.core].copy();state[0,0,0]+=.1
    with pytest.raises(ValueError):
        SourceSupportedScalarBoundary(b.original,state,b.state,b.extended.bed)


def test_scalar_action_matches_independent_explicit_face_matrix():
    from audit_difference_scalar_identities import face_matrices
    b,x,y=fixture(n=5,h=lambda x,y:1.+x/8+y/16)
    _,_,_,scalar,_=face_matrices(b.extended)
    rng=np.random.default_rng(983)
    outer=rng.normal(size=x.shape); interior=rng.normal(size=(5,5))
    full=outer.copy(); full[b.core]=interior
    expected=(scalar@full.ravel()).reshape((*x.shape,2))[b.core]
    np.testing.assert_allclose(b.gradient(interior,outer),expected,atol=2e-14,rtol=0)


def test_partial_time_face_trace_is_not_lost_in_material_identity():
    b,x,y=fixture()
    n=b.original.h.shape[0]
    trace=np.zeros((4*n,2))
    trace[:n,0]=.2; trace[n:2*n,0]=1.2
    trace[2*n:3*n,0]=.3; trace[3*n:,0]=1.3
    trace[:,1]=.1*trace[:,0]
    tangent=PressureGeometryRate(b.original,b.original.bed,np.zeros((n,n)))
    q,c,adv=b.forcing(tangent,trace)
    partial_u_t=.1*b.velocity[b.core]
    da,ea=b.original.kinematic_components(partial_u_t+adv)
    # u(t)=(1+.1t)*(x+.2,y+.3): divergence=2+.2t everywhere.
    np.testing.assert_allclose(q-da,3.8,atol=1e-12,rtol=0)
    np.testing.assert_allclose(c+ea,0.,atol=1e-12,rtol=0)


@pytest.mark.parametrize('flat', [True,False])
def test_actual_entering_ray_keeps_zero_state_and_nonzero_velocity_limit(flat):
    from directional_pressure_geometry import DirectionalPressureGeometry
    base,x,y=fixture(n=5,h=lambda x,y:np.where(x<.25,0.,1.))
    state=base.state.copy(); rate=np.zeros_like(state)
    rate[...,0]=.125; rate[...,1]=.0625; rate[...,2]=-.03125
    bed=np.zeros_like(x) if flat else .125*np.maximum(x,0)+.0625*y
    interior=ReconstructedPressureGeometry(state[base.core][...,0],bed[base.core],base.original.dx,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')
    g=DirectionalPressureGeometry(interior,rate[base.core][...,0])
    b=SourceSupportedScalarBoundary(g,state[base.core],state,bed,full_rate=rate)
    dry=state[...,0]==0
    np.testing.assert_array_equal(b.state[dry],0.)
    np.testing.assert_array_equal(b.velocity[dry],np.broadcast_to([.5,-.25],b.velocity[dry].shape))
    np.testing.assert_array_equal(b.full_rate,rate)
    errors=[]
    trace=np.zeros((20,2))
    expected=b.forcing(g.tangent,trace)
    for eps in (2.**-8,2.**-16,2.**-24):
        later=state+eps*rate
        gg=ReconstructedPressureGeometry(later[base.core][...,0],bed[base.core],base.original.dx,
            pressure_trace='integrated_column',bed_quadrature='shared_bottom')
        bb=SourceSupportedScalarBoundary(gg,later[base.core],later,bed)
        tangent=PressureGeometryRate(gg,gg.bed,rate[base.core][...,0])
        actual=bb.forcing(tangent,trace)
        errors.append(max(float(abs(a-e).max()) for a,e in zip(actual,expected)))
    assert errors[-1]<1e-6 and errors[-1]<errors[0]/10000
    with pytest.raises(ValueError,match='actual full conserved rates'):
        SourceSupportedScalarBoundary(g,state[base.core],state,bed)
    invalid=rate.copy(); invalid[dry,0]=-.125
    with pytest.raises(ValueError,match='dry conserved direction'):
        SourceSupportedScalarBoundary(g,state[base.core],state,bed,full_rate=invalid)
