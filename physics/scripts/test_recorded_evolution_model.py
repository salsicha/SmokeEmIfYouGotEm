import copy
import numpy as np
import pytest
import audit_recorded_evolution_steps as audit
from test_live_temporal_evolution import record


@pytest.mark.parametrize('limiter,summary,trace', [('continuous',None,'continuous'),
    ('continuous',[1,1,1,1],'continuous'),('binary',[1,1,1,3],'binary'),
    ('continuous',[1,1,1,3],'binary'),('unknown',[1,1,1,1],'unknown'),('unscaled',None,'unscaled'),
    ('unscaled',[1,1,1,3],'unscaled'),('unscaled',[1,1,1,7],'unscaled')])
def test_captured_model_mismatch_rejected(limiter,summary,trace):
    source=dict(shoreline_limiter=limiter)
    if summary is not None:source['summary']=summary
    with pytest.raises(ValueError,match='model|mode'):
        audit.shoreline_model(dict(shoreline_limiter=trace),source)


@pytest.mark.parametrize('limiter',['binary','continuous','unscaled'])
def test_both_recorded_stages_use_the_captured_model(monkeypatch,limiter):
    pair=record();source=dict(observations=[pair['first'],pair['second']],shoreline_limiter=limiter,
        summary=[1,1,1,{'binary':1,'continuous':3,'unscaled':5}[limiter]])
    before=copy.deepcopy(source);state=np.array(pair['first']['state']).reshape(2,3,4)
    stage=dict(state=state,rate=np.zeros_like(state),force=np.zeros((2,3,2)),
        fraction=np.ones((2,3)),pairs=np.zeros((2,3),dtype=np.uint32))
    trial=dict(interval=0,trial=0,begin=.125,end=.1328125,attempted_dt=.0078125,accepted_dt=.0078125,accepted=1)
    monkeypatch.setattr(audit,'read_records',lambda *_:iter([(trial,[stage,stage],state)]))
    calls=[];original=audit.temporal.bank.rate
    def rate(*args,**kwargs):
        calls.append(kwargs['shoreline_limiter']);return original(*args,**kwargs)
    monkeypatch.setattr(audit.temporal.bank,'rate',rate)
    rows=audit.compare(dict(shoreline_limiter=limiter),b'',source,0)
    assert calls==[limiter,limiter] and source==before
    assert rows[0]['final_state_max_error']==0
