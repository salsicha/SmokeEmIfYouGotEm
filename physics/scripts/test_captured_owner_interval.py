import copy
import numpy as np
import pytest

from audit_captured_owner_interval import analyze
from test_captured_owner_trial import interval_record
import audit_live_temporal_evolution as temporal


def capture(source, *, completed=False):
    summary=source['summary'].copy();clock=source['progress'].copy()
    if completed:summary=[437,42,1,1];clock=[.125,0.,0.,0.]
    arrays=dict(output_state=np.asarray(source['state'],dtype='<f4').reshape(-1,4),
        progress=np.asarray([clock],dtype='<f4'),summary=np.asarray([summary],dtype='<u4'),
        diagnostics=np.asarray([[0,0,0,1] if completed else source['diagnostics']],dtype='<u4'),
        boundary_volume=np.asarray(source['cumulative_boundary_volume'],dtype='<f4').reshape(-1,4))
    return arrays


def encoded(arrays,completed=False):
    data=bytearray();fields=[]
    for name,value in arrays.items():
        fields.append(dict(name=name,bytes=value.nbytes,components=value.shape[1],byte_offset=len(data),dtype=value.dtype.name))
        data+=value.tobytes()
    return dict(schema='raftsim.captured_owner_interval_diagnostic.v1',capture_completed=True,
                transaction_accepted=completed,fields=fields),data


def source():
    r=interval_record();r['cumulative_boundary_volume']=[0.]*2048
    return r


def test_pending_interval_preserves_history_and_does_not_claim_completion():
    r=source();before=copy.deepcopy(r);metadata,data=encoded(capture(r))
    result=analyze(r,metadata,data)
    assert r==before and result['additional_trials']==0 and not result['interval_completed']
    assert result['cpu_completed'] and result['state_gates_passed']
    assert not result['scene_accepted'] and not result['full_history_qualified']


def test_completed_interval_uses_retained_interior_and_original_boundary(monkeypatch):
    r=source();r['state'][0]=.25;arrays=capture(r,completed=True);metadata,data=encoded(arrays,True)
    def reference(state,bed,dx,seconds,**kw):
        assert state[0,0,0]==.25 and seconds==.0625 and dx==.5
        assert kw['max_trials']==4096-432 and kw['breaking_model']=='hybrid_front'
        es,eb,trace=kw['boundary_at_time'](seconds,None)
        assert es.shape==(512,4) and eb.shape==(512,) and trace.shape==(512,2)
        return state.copy(),dict(elapsed_s=seconds)
    monkeypatch.setattr(temporal.bank,'advance',reference)
    result=analyze(r,metadata,data)
    assert result['interval_completed'] and result['additional_trials']==5 and result['additional_accepted']==5
    assert result['state_gates_passed'] and result['float_water_balance_m3']==0
    assert result['maximum_state_error']==0 and not result['full_history_qualified']


@pytest.mark.parametrize('bad',['counter_reset','too_many','accepted_exceeds_trials','mode','status',
    'time_backwards','fake_completion','changed_unaccepted_state','changed_unaccepted_ledger','nonfinite_ledger','layout'])
def test_invalid_retained_continuations_rejected(bad):
    r=source();arrays=capture(r)
    if bad=='counter_reset':arrays['summary'][0,0]=0
    if bad=='too_many':arrays['summary'][0,0]=449
    if bad=='accepted_exceeds_trials':arrays['summary'][0,1]=38
    if bad=='mode':arrays['summary'][0,3]=0
    if bad=='status':arrays['summary'][0,2]=3
    if bad=='time_backwards':arrays['progress'][0,0]=0
    if bad=='fake_completion':arrays['summary'][0,2]=1
    if bad=='changed_unaccepted_state':arrays['output_state'][0,0]=2
    if bad=='changed_unaccepted_ledger':arrays['boundary_volume'][0,0]=1
    if bad=='nonfinite_ledger':arrays['boundary_volume'][0,0]=np.nan
    if bad=='layout':arrays['output_state']=arrays['output_state'][:1]
    metadata,data=encoded(arrays)
    with pytest.raises(ValueError):analyze(r,metadata,data)
