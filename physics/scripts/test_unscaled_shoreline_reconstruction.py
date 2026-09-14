"""Properties of the opt-in original-MC control, not native/history acceptance."""
import numpy as np
import total_depth_bank_replay as bank


def test_actual_unscaled_operator_retains_original_positive_polynomials(monkeypatch):
    rng=np.random.default_rng(140914)
    bed=rng.uniform(-2,2,(19,23));h=10**rng.uniform(-12,1,bed.shape)
    state=np.concatenate((h[...,None],h[...,None]*rng.uniform(-3,3,(*h.shape,2))),axis=-1)
    before=state.copy();old_bed=bed.copy();captures=[];original=bank.hydrostatic_faces
    def capture(*args,**kwargs):
        result=original(*args,**kwargs);captures.append((args,kwargs,result));return result
    monkeypatch.setattr(bank,'hydrostatic_faces',capture)
    bank.rate(state,bed,.5,second_order=True,shoreline_limiter='unscaled')
    assert len(captures)==2
    for args,kwargs,result in captures:
        axis=args[4]
        np.testing.assert_array_equal(args[2],bank.mc(h,axis,False))
        np.testing.assert_array_equal(args[3],bank.mc(h,axis,False,other=bed))
        assert kwargs.get('slope_factors') is None and kwargs.get('flattened') is None
        assert np.all(result[0]>=0) and np.all(result[1]>=0)
        np.testing.assert_allclose(.5*(result[0]+result[1]),h,rtol=3e-16,atol=0)
    np.testing.assert_array_equal(state,before);np.testing.assert_array_equal(bed,old_bed)


def test_owning_depth_is_self_monotone_over_wet_stencils():
    rng=np.random.default_rng(2414);h=10**rng.uniform(-12,2,(1024,5));bed=rng.uniform(-10,10,h.shape)
    a=h.copy();b=h.copy();a[:,2]*=1-1e-5;b[:,2]*=1+1e-5
    def faces(depth):
        return bank.hydrostatic_faces(depth,bed,bank.mc(depth,1,False),
            bank.mc(depth,1,False,other=bed),1,False,reconstruction=True)[:2]
    left,right=faces(a),faces(b);difference=b[:,2]-a[:,2]
    for low,high in zip(left,right):
        derivative=(high[:,2]-low[:,2])/difference
        assert np.min(derivative)>=-1e-8 and np.max(derivative)<=2+1e-8


def test_unscaled_control_never_changes_legacy_default():
    rng=np.random.default_rng(6214);bed=rng.uniform(0,1,(7,9))
    state=np.zeros((*bed.shape,3));state[...,0]=rng.uniform(.01,1,bed.shape)
    expected,_=bank.rate(state,bed,.5,second_order=True,shoreline_limiter='binary')
    bank.rate(state,bed,.5,second_order=True,shoreline_limiter='unscaled')
    actual,_=bank.rate(state,bed,.5,second_order=True)
    np.testing.assert_array_equal(actual,expected)
