import numpy as np
import pytest
import audit_continuous_polynomial_response as probe


def lake():
    bed=np.zeros((7,9));state=np.zeros((*bed.shape,3));state[...,0]=1
    return state,bed


def test_observer_records_actual_raw_and_scaled_faces_without_mutation():
    state,bed=lake();before=state.copy();original=probe.temporal.bank.hydrostatic_faces
    expected,cfl=probe.temporal.bank.rate(state,bed,.5,second_order=True,shoreline_limiter='continuous')
    actual,row=probe.observe(state,bed,.5,None,(3,4))
    np.testing.assert_array_equal(actual,expected)
    assert row['cfl_bound_s']==cfl
    assert [(p['axis'],p['phase']) for p in row['polynomials']]==[(1,'raw'),(1,'scaled'),(0,'raw'),(0,'scaled')]
    assert all(len(p['points'])==5 for p in row['polynomials'])
    assert all(v['factor']==1 for p in row['polynomials'] for v in p['points'])
    np.testing.assert_array_equal(state,before);np.testing.assert_array_equal(bed,0)
    assert probe.temporal.bank.hydrostatic_faces is original


def test_depth_probe_varies_only_selected_depth_and_has_unit_owning_derivatives(monkeypatch):
    state,bed=lake();before=state.copy();observed=[];original=probe.observe
    def capture(value,*args,**kwargs):
        observed.append(value.copy());return original(value,*args,**kwargs)
    monkeypatch.setattr(probe,'observe',capture)
    result=probe.depth_response(state,bed,.5,None,(3,3),(3,4),1e-5)
    assert len(observed)==7 and len(result['derivatives'])==3
    for value in observed:
        value[3,4,0]=state[3,4,0]
        np.testing.assert_array_equal(value,state)
    for row in result['derivatives']:
        for face in row['polynomials']:
            assert face['owning_minus']==1 and face['owning_plus']==1
    np.testing.assert_array_equal(state,before)


@pytest.mark.parametrize('step',[0.,-1.,float('nan'),float('inf'),1.,2.])
def test_invalid_depth_probe_rejected(step):
    state,bed=lake()
    with pytest.raises(ValueError):probe.depth_response(state,bed,.5,None,(3,3),(3,4),step)


def test_observer_restores_operator_on_failure(monkeypatch):
    state,bed=lake();original=probe.temporal.bank.hydrostatic_faces
    def fail(*args,**kwargs):raise RuntimeError('deliberate test failure')
    monkeypatch.setattr(probe.temporal.bank,'rate',fail)
    with pytest.raises(RuntimeError):probe.observe(state,bed,.5,None,(3,4))
    assert probe.temporal.bank.hydrostatic_faces is original


def test_local_jacobian_records_actual_centered_operator_without_mutation():
    state,bed=lake();before=state.copy()
    result=probe.local_hydro_jacobian(state,bed,.5,None,(3,4),0,1e-5,.001)
    assert result['indices_yxc']==[[3,4,0],[3,4,1],[3,4,2]]
    matrix=np.array(result['matrix'])
    assert matrix.shape==(3,3) and np.isfinite(matrix).all()
    assert all(real<0 for real,imag in result['eigenvalues_real_imag'])
    assert all(row['unstable_decaying_modes']==0 for row in result['rk2_frozen_linearization'])
    np.testing.assert_array_equal(state,before);np.testing.assert_array_equal(bed,0)


@pytest.mark.parametrize('radius,step,dt',[(-1,1e-5,.01),(1,0,.01),(1,1,.01),(1,1e-5,0)])
def test_invalid_jacobian_rejected(radius,step,dt):
    state,bed=lake()
    with pytest.raises(ValueError):probe.local_hydro_jacobian(state,bed,.5,None,(3,4),radius,step,dt)


def test_unscaled_control_captures_only_original_polynomials():
    state,bed=lake()
    _,row=probe.observe(state,bed,.5,None,(3,4),limiter='unscaled')
    assert [(p['axis'],p['phase']) for p in row['polynomials']]==[(1,'raw'),(0,'raw')]
    assert all(v['factor']==1 for p in row['polynomials'] for v in p['points'])
