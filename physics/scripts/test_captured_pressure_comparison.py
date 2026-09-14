import numpy as np
import pytest
from audit_captured_owner_trial import pressure_comparison
from export_prescribed_pressure_fixtures import fixture


def captured():
    y,x=np.indices((5,7));h=1+.1*np.sin(x)
    state=np.stack((h,h*.4,h*.1),-1);rate=np.stack((h*.02,h*.03,-h*.01),-1)
    fields,_=fixture(state,.03*np.cos(x+y),rate,np.zeros((24,2)))
    names=('geometry0','input_state','rate0','bed_slope0','fraction0','pairs0',
           'pressure_rhs0','pressure_correction0','pressure0','force0','boundary_trace0')
    gpu=dict(zip(names,fields))
    gpu.update(pressure_diagnostics0=np.zeros(4,dtype=np.uint32),
        solver_diagnostics0=np.array([0,0,40,40],dtype=np.uint32),pressure_residual0=np.zeros((5,7,4)))
    return gpu


def test_same_inputs_pressure_matches():
    result=pressure_comparison(captured(),0,(5,7),.5)
    assert result['comparison_passed']
    assert result['fields']['force']['maximum_error']==0


def test_missing_capture_not_qualified():
    assert pressure_comparison({},0,(5,7),.5)==dict(available=False)


@pytest.mark.parametrize('defect',['input','solver','force','rhs','residual','nan'])
def test_pressure_defects_fail(defect):
    gpu=captured()
    if defect=='input':gpu['pressure_diagnostics0'][0]=1
    if defect=='solver':gpu['solver_diagnostics0'][1]=1
    if defect=='force':gpu['force0']+=1
    if defect=='rhs':gpu['pressure_rhs0']+=1
    if defect=='residual':gpu['pressure_residual0']+=1
    if defect=='nan':gpu['force0'][0,0,0]=np.nan
    assert not pressure_comparison(gpu,0,(5,7),.5)['comparison_passed']
