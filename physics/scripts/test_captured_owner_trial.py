import copy
import struct
import numpy as np
import pytest
from export_captured_owner_trial import pack, pack_interval


def record():
    state=np.zeros((128,128,4),dtype=np.float32);state[...,0]=1;state[...,1]=2
    a=dict(nx=128,ny=128,cell_meters=.5,origin_x=2.,origin_y=3.,native_seconds=0.,revision=1,
        state=state.ravel().tolist(),bed=[0.]*16384,exterior_state=state[:4].ravel().tolist(),
        exterior_bed=[0.]*512,face_normal_velocity=[0.]*512)
    b=copy.deepcopy(a);b['native_seconds']=.125;b['revision']=2
    return dict(schema='raftsim.live_nonlinear_owner_audit.v1',progress=[.0625,0.,.0625,.0078125],
                state_origin_meters=[2.,3.],observations=[a,b],state=state.ravel().tolist())


def test_exact_current_state_and_clock_export_without_reset():
    r=record();r['state'][0]=.25;before=copy.deepcopy(r)
    data,meta=pack(r)
    assert r==before and meta['interval']==0
    assert struct.unpack('<IIIIfdd',data[:36])==(0x52535452,1,128,128,.5,0.,.125)
    np.testing.assert_array_equal(np.frombuffer(data,'<f4',4,36),r['progress'])
    np.testing.assert_array_equal(np.frombuffer(data,'<f4',65536,52),r['state'])


@pytest.mark.parametrize('bad',['origin','clock','inactive','state','grid'])
def test_invalid_captured_trial_rejected(bad):
    r=record()
    if bad=='origin':r['state_origin_meters']=[100,100]
    if bad=='clock':r['progress'][0]=.25
    if bad=='inactive':r['progress'][2]=0
    if bad=='state':r['state'][0]=-1
    if bad=='grid':r['observations'][0]['cell_meters']=1
    with pytest.raises(ValueError):pack(r)


def interval_record():
    r=record()
    r.update(summary=[432,37,0,1],diagnostics=[0,5,8,0],
             cumulative_boundary_volume=np.arange(2048,dtype=np.float32).tolist())
    return r


def test_interval_preserves_all_actual_records_and_original_payload():
    r=interval_record();before=copy.deepcopy(r)
    original,_=pack(r);data,meta=pack_interval(r)
    assert r==before and struct.unpack_from('<I',data,4)[0]==2
    assert data[:4]==original[:4] and data[8:len(original)]==original[8:]
    assert struct.unpack_from('<8I',data,len(original))==(432,37,0,1,0,5,8,0)
    np.testing.assert_array_equal(np.frombuffer(data,'<f4',2048,len(original)+32),r['cumulative_boundary_volume'])
    assert meta['retained_summary']==r['summary'] and meta['retained_diagnostics']==r['diagnostics']


@pytest.mark.parametrize('key,value',[
    ('summary',[0,37,0,1]),('summary',[4097,37,0,1]),('summary',[432,37,1,1]),
    ('summary',[432,37,0,0]),('summary',[432.5,37,0,1]),('summary',[432,37,0]),
    ('diagnostics',[-1,0,0,0]),('diagnostics',[2**32,0,0,0]),
    ('diagnostics',[float('nan'),0,0,0]),('cumulative_boundary_volume',[0.]*2047),
    ('cumulative_boundary_volume',[float('inf')]*2048)])
def test_interval_invalid_retained_records_rejected(key,value):
    r=interval_record();r[key]=value
    with pytest.raises(ValueError):pack_interval(r)
