from fractions import Fraction as F
import numpy as np
from audit_positive_rational_branch_crossings import branch,signature
from reverse_rational_depth_gradient import Tape,limited


def test_branch_values_agree_with_original_reverse_limiter():
    rng=np.random.default_rng(9911)
    for scale in (1.,2.**-500):
        h=rng.integers(-40,40,(3,17)).astype(float)*scale
        b=rng.integers(-40,40,h.shape).astype(float)*scale
        for key,label in signature(h,b).items():
            axis,point,kind=key;p=list(point);q=list(point)
            p[axis]=(p[axis]-1)%h.shape[axis];q[axis]=(q[axis]+1)%h.shape[axis]
            p,q=tuple(p),tuple(q)
            back=F(float(h[point]))-F(float(h[p]));front=F(float(h[q]))-F(float(h[point]))
            if kind=='surface':
                back+=F(float(b[point]))-F(float(b[p]))
                front+=F(float(b[q]))-F(float(b[point]))
            candidates=(2*back,(back+front)/2,2*front)
            expected=F(0) if label==-1 else candidates[label]
            tape=Tape();actual=limited(tape.node(back),tape.node(front))
            assert actual.value==expected


def test_singleton_axis_not_reported_and_no_input_changes():
    h=np.array([[1.,1.5,2.,1.5]]);b=np.zeros_like(h)
    original=h.copy();sig=signature(h,b)
    assert all(key[0]==1 for key in sig)
    assert len(sig)==8
    np.testing.assert_array_equal(h,original)
