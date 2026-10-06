import json

import numpy as np
import pytest

from audit_froth_characteristics import FrozenCurrent
from audit_froth_flow_history import FlowHistory, load, analyze


def field(u, v, origin=(-16, -16)):
    y, x = np.indices((65, 65)); x = x*.5+origin[0]; y = y*.5+origin[1]
    a = np.zeros((65,65,4));a[...,0]=2;a[...,1]=u(x,y);a[...,2]=v(x,y)
    return FrozenCurrent(a,origin,.5)


def test_changing_uniform_flow_is_integrated_over_original_intervals():
    first=field(lambda x,y:x*0+2,lambda x,y:y*0)
    last=field(lambda x,y:x*0,lambda x,y:y*0+4)
    h=FlowHistory([(0,.3,first),(.3,1,last)])
    p=np.array([[1.,2.],[-3.,5.]])
    for order in (1,2,4):
        actual,ok=h.depart(p,1,.017,order)
        assert ok.all();np.testing.assert_allclose(actual,p-[.6,2.8],atol=2e-13)
    frozen,_=last.depart(p,1,128,4)
    assert np.linalg.norm(frozen-actual,axis=1).min()>1


def test_noncommuting_shears_require_reverse_chronological_composition():
    first=field(lambda x,y:.8*y,lambda x,y:y*0)
    last=field(lambda x,y:x*0,lambda x,y:.7*x)
    p=np.array([[2.,3.],[-1.,4.]])
    expected=p.copy();expected[:,1]-=.7*.5*p[:,0];expected[:,0]-=.8*.5*expected[:,1]
    actual,ok=FlowHistory([(0,.5,first),(.5,1,last)]).depart(p,1,.1)
    assert ok.all();np.testing.assert_allclose(actual,expected,atol=1e-13)
    wrong,_=FlowHistory([(0,.5,last),(.5,1,first)]).depart(p,1,.1)
    assert np.linalg.norm(wrong-expected,axis=1).min()>.1


def test_original_registration_survives_window_move_and_partial_interval():
    a=field(lambda x,y:x*0+1,lambda x,y:y*0,(-16,-16))
    b=field(lambda x,y:x*0+2,lambda x,y:y*0,(-15,-16))
    p=np.array([[0.,0.]])
    actual,ok=FlowHistory([(3,3.5,a),(3.5,4,b)]).depart(p,.75,.03)
    assert ok.all();np.testing.assert_allclose(actual,[[-1.25,0]],atol=1e-13)
    assert a.origin.tolist()==[-16,-16] and b.origin.tolist()==[-15,-16]


def test_missing_time_and_dry_path_remain_unavailable():
    f=field(lambda x,y:x*0+2,lambda x,y:y*0)
    h=FlowHistory([(1,2,f)])
    out,ok=h.depart(np.array([[0.,0.]]),1.1,.01)
    assert not ok.any() and np.isnan(out).all()
    f.flow[30:35,30:35,0]=0
    out,ok=h.depart(np.array([[0.,0.],[20.,0.]]),.2,.01)
    assert not ok.any() and np.isnan(out).all()


@pytest.mark.parametrize('times', [[(0,.4),(.5,1)],[(0,.5),(.4,1)],[(0,0)],[(False,1)],[(0,float('nan'))]])
def test_no_gap_overlap_hold_or_nonfinite_history(times):
    f=field(lambda x,y:x*0,lambda x,y:y*0)
    with pytest.raises(ValueError):FlowHistory([(a,b,f) for a,b in times])


def fixture(tmp_path):
    prefix=tmp_path/'actual'
    flow=np.zeros((25,25,4),dtype='<f4');flow[...,0]=2;flow[...,1]=1
    surface=flow.copy();surface[...,3]=.5
    flow.tofile(str(prefix)+'.flow.f32');surface.tofile(str(prefix)+'.surface.f32')
    flow.tofile(str(prefix)+'.history-000.f32')
    snapshot=dict(schema='raftsim.detail.snapshot.v2',dtype='little-endian float32',arrays_complete=True,
                  shape=[25,25,4],origin_m=[-6,-6],cell_m=.5,simulation_s=2.)
    record=dict(file='actual.history-000.f32',shape=[25,25,4],origin_m=[-6,-6],cell_m=.5,
                start_s=.5,end_s=2.,mean_sample_elapsed_s=.5)
    index=dict(schema='raftsim.froth_flow_history.v1',dtype='little-endian float32',arrays_complete=True,intervals=[record])
    Path=type(prefix)
    Path(str(prefix)+'.json').write_text(json.dumps(snapshot))
    Path(str(prefix)+'.history.json').write_text(json.dumps(index))
    return prefix,index,snapshot


def test_complete_original_audit_and_common_cohort(tmp_path):
    prefix,_,_=fixture(tmp_path);report=analyze(prefix)
    assert len(report['input_sha256'])==5 and report['original_wet_interior_cells']==81
    assert report['visual_accepted'] is False and report['physical_accepted'] is False
    for record in report['records']:
        assert len(record['rows'])==81 and record['common_supported_rows']==81
        for result in record['methods'].values():assert result['common_foamy']['maximum_m']<1e-12


@pytest.mark.parametrize('change',[{'file':'../actual.history-000.f32'},{'end_s':3},{'shape':[25,25,3]},
                                  {'origin_m':[0,0]},{'cell_m':0},{'mean_sample_elapsed_s':True}])
def test_original_metadata_mismatch_rejected(tmp_path,change):
    prefix,index,_=fixture(tmp_path);index['intervals'][0].update(change)
    type(prefix)(str(prefix)+'.history.json').write_text(json.dumps(index))
    with pytest.raises(ValueError):load(prefix)


def test_changed_last_input_is_not_paired_history(tmp_path):
    prefix,_,_=fixture(tmp_path)
    path=type(prefix)(str(prefix)+'.history-000.f32');a=np.fromfile(path,dtype='<f4');a[1]=3;a.tofile(path)
    with pytest.raises(ValueError,match='differs'):load(prefix)
