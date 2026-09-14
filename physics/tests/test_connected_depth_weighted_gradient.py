import numpy as np
import pytest
from connected_depth_weighted_scalar_gradient import ConnectedDepthWeightedScalarGradient as Gradient
from depth_weighted_scalar_gradient import DepthWeightedScalarGradient
from audit_depth_weighted_source_support import inspect


@pytest.mark.parametrize('axis', (0, 1))
def test_no_scalar_link_jumps_an_exact_dry_gap(axis):
    h = np.ones((9,9)); index = [slice(None), slice(None)]; index[axis] = 4
    h[tuple(index)] = 0
    f = np.zeros_like(h); index[axis] = slice(5, None); f[tuple(index)] = 10
    g = Gradient(h, 1.)
    index[axis] = slice(None, 4)
    assert np.all(g.gradient(f)[tuple(index)] == 0)
    assert np.any(DepthWeightedScalarGradient(h, 1.).gradient(f)[tuple(index)] != 0)


def test_bridge_loss_is_continuous_not_a_depth_cutoff():
    h = np.ones((9,9)); h[:,4] = 0
    f = np.zeros_like(h); f[:,5:] = 10
    limit = Gradient(h, 1.).gradient(f)[4,3,0]
    errors = []
    for eps in (2.**-8, 2.**-16, 2.**-24):
        later = h.copy(); later[:,4] = eps
        errors.append(abs(Gradient(later, 1.).gradient(f)[4,3,0]-limit))
    assert errors[-1] < 1e-6 and errors[-1] < errors[0]/10000


def test_quadratic_reproduction_and_independent_connected_wls():
    y,x = np.indices((11,11), dtype=float); dx = .25; x *= dx; y *= dx
    rng = np.random.default_rng(836); h = np.exp(rng.normal(size=x.shape))
    g = Gradient(h, dx)
    actual = g.gradient(2*x*x-3*x*y+4*y*y+2*x-y)
    np.testing.assert_allclose(actual, np.stack((4*x-3*y+2,-3*x+8*y-1),axis=-1), atol=2e-12, rtol=0)
    f = rng.normal(size=h.shape); actual = g.gradient(f)
    for point in ((0,0), (4,4), (10,10)):
        for component,axis in enumerate((1,0)):
            rows=[]; values=[]; weights=[]
            for r in g.offsets:
                nb=list(point);nb[axis]+=r
                if not 0 <= nb[axis] < h.shape[axis]:continue
                nb=tuple(nb); w=h[nb]/(h[point]+h[nb])
                if abs(r)==2:
                    mid=list(point);mid[axis]+=r//2;m=h[tuple(mid)]
                    w *= 4*m/(m+h[point])*m/(m+h[nb])
                rows.append((r,r*r));values.append(f[nb]-f[point]);weights.append(w)
            expected=np.linalg.lstsq(np.array(rows)*np.sqrt(weights)[:,None],
                np.array(values)*np.sqrt(weights),rcond=None)[0][0]/dx
            assert abs(actual[point][component]-expected)<2e-12


def test_entering_bridge_uses_actual_direction_and_keeps_source_unchanged():
    h = np.zeros((9,9)); rate=np.full_like(h,.125)
    f=np.random.default_rng(731).normal(size=h.shape)
    original=h.copy()
    np.testing.assert_allclose(Gradient(h,1.,mass_rate=rate).gradient(f),
        Gradient(rate*2.**-24,1.).gradient(f),atol=1e-13,rtol=0)
    np.testing.assert_array_equal(h,original)


def test_capture_support_auditor_detects_the_original_gap(monkeypatch):
    import audit_depth_weighted_source_support as audit
    full=np.ones((15,15,4)); full[:,7,0]=0
    original=inspect(full,1.)
    assert original['components'][0]['wet_links_crossing_exactly_dry_cells']>0
    monkeypatch.setattr(audit,'DepthWeightedScalarGradient',Gradient)
    connected=inspect(full,1.)
    assert all(c['wet_links_crossing_exactly_dry_cells']==0 for c in connected['components'])
