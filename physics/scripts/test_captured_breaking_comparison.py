import numpy as np
import pytest
from audit_captured_owner_trial import breaking_comparison
from breaking_front_reference import dispersion_fraction, surface_jumps


def captured():
    h=np.ones((1,64));h[:,20:40]=2;bed=h*0
    pairs=[np.ones_like(h,dtype=bool),np.zeros_like(h,dtype=bool)]
    fraction,stats=dispersion_fraction(h,bed,bed,pairs,1.)
    return dict(geometry0=np.stack((h,bed),-1),pairs0=np.ones_like(h,dtype=np.uint32),
        rate0=np.zeros((*h.shape,4)),fraction0=fraction,
        surface_jumps0=np.stack([surface_jumps(h,bed,axis) for axis in (1,0)],-1),
        breaking_diagnostics0=np.array([0,stats['detected_fronts'],stats['boundary_truncated_runs'],stats['subcell_fronts']],dtype=np.uint32))


def test_actual_graph_comparison():
    result=breaking_comparison(captured(),0,(1,64),1.)
    assert result['comparison_passed'] and result['maximum_fraction_error']==0
    assert result['maximum_surface_jump_error']==0


def test_missing_old_capture_is_unavailable():
    assert breaking_comparison({},0,(1,64),1.)==dict(available=False)


@pytest.mark.parametrize('defect', ['flags','count','fraction','nan'])
def test_failure_is_not_promoted(defect):
    gpu=captured()
    if defect=='flags':gpu['breaking_diagnostics0'][0]=1
    if defect=='count':gpu['breaking_diagnostics0'][1]+=1
    if defect=='fraction':gpu['fraction0'][:]=1
    if defect=='nan':gpu['fraction0'][0,0]=np.nan
    assert not breaking_comparison(gpu,0,(1,64),1.)['comparison_passed']


def test_unknown_graph_bits_rejected():
    gpu=captured();gpu['pairs0'][0,0]|=4
    with pytest.raises(ValueError,match='graph bits'):
        breaking_comparison(gpu,0,(1,64),1.)
