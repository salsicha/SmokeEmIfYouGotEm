import numpy as np
from audit_captured_owner_trial import state_statistics, fields, bit_exact_state
import pytest


def test_stage_statistics_distinguish_represented_thin_state_from_dry_momentum():
    value=np.zeros((128,128,4),dtype=np.float32)
    tiny=np.nextafter(np.float32(0),np.float32(1))
    value[79,88]=[tiny,4*tiny,-tiny,tiny]
    assert state_statistics(value)['invalid_cells']==0
    value[79,88,0]=0
    assert state_statistics(value)['invalid_cells']==1
    value[79,88]=[tiny,0,0,-tiny]
    assert state_statistics(value)['invalid_cells']==1
    value[79,88]=[tiny,1,0,0]
    assert state_statistics(value)['invalid_cells']==1


def test_state_preservation_is_bit_exact_including_signed_zero():
    a=np.zeros((1,4),dtype=np.float32);b=a.copy()
    assert bit_exact_state(a,b)
    b[0,1]=-0.0
    assert np.array_equal(a,b)
    assert not bit_exact_state(a,b)


def test_capture_fields_reject_incomplete_or_ambiguous_storage():
    data=np.array([1,0,0,0],dtype='<u4').tobytes()
    field=dict(name='transport_diagnostics0',bytes=16,components=4,byte_offset=0,dtype='uint32')
    metadata=dict(schema='raftsim.captured_owner_trial_diagnostic.v1',capture_completed=True,fields=[field])
    assert fields(metadata,data)['transport_diagnostics0'][0,0]==1
    for bad in (dict(metadata,capture_completed=False),dict(metadata,fields=[field,field])):
        with pytest.raises(ValueError):fields(bad,data)
    with pytest.raises(ValueError):fields(metadata,data+b'\x00')
