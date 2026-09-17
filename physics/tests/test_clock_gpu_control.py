"""Actual SM5 production commit-phase clock tests, not an HLSL emulator.

Configure RAFTSIM_CLOCK_GPU_EXE and RAFTSIM_CLOCK_GPU_SHADER. Skips are not
native acceptance. Exact-rational clock sums supply the expected two words.
"""
from fractions import Fraction as F
import os
from pathlib import Path
import struct
import subprocess

import numpy as np
import pytest


def f32(x):
    return float(np.float32(float(x)))


def expected(progress, dt, diagnostics=(0,0,0,0), end=None):
    # All ordinary cases use an exactly representable clock sum or residual.
    # Independent exact rational arithmetic, not the shader's TwoSum sequence.
    hi,lo,remaining,proposal=map(f32,progress)
    dt=f32(dt);d=list(diagnostics);info=[0.,dt,0.,0.]
    accept=dt>0 and not any(d[:3])
    next_state=[hi,lo,remaining,proposal]
    if accept:
        total=F(hi)+F(lo)+F(dt)
        with np.errstate(over='ignore'):
            h=f32(total)
        if not np.isfinite(h):
            accept=False;d[2]|=16
        else:
            l=f32(total-F(h))
            residual=(F(end[0])+F(end[1])-F(h)-F(l) if end is not None
                      else F(0) if dt==remaining else F(remaining)-F(dt))
            r=f32(residual)
            if end is not None and F(r)>residual:
                r=float(np.nextafter(np.float32(r),np.float32(-np.inf)))
            if r<0 or r==remaining or (h==hi and l==lo):
                accept=False;d[2]|=16
            else:
                next_state=[h,l,r,min(f32(1/120),r)]
    if not accept:
        next_state=[hi,lo,remaining,0. if d[0] or d[2]&16 or remaining==0 else f32(.5*dt)]
        if 0<next_state[3]<f32(1e-9) and next_state[3]!=remaining:
            next_state[3]=0.;d[2]|=16
    info[0]=dt if accept else 0.;d[3]=int(accept)
    return next_state,info,d


def records():
    result=[]
    for hi,lo in [(1048576.,0.),(1048576.,.03125),(1048575.9375,.0625),
                  (3.125,0.),(0.,0.),(-1048576.,-.03125)]:
        for dt in [.001,1/128,2**-40]:
            result.append(((hi,lo,dt,dt),dt,(0,0,0,0),None))
    for bits in [(1,0,0,0),(0,1,0,0),(0,0,8,0)]:
        result.append(((1048576.,.03125,.004,.001),.001,bits,None))
    result.extend([((1048576.,0.,0.,0.),0.,(0,0,0,0),None),
                   ((3e38,3e38,.004,.001),.001,(0,0,0,0),None),
                   ((1048576.,0.,.1,1/120),1/120,(0,0,0,0),None),
                   ((1048576.,0.,1/128,1/128),1/128,(0,0,0,0),(1048576.,1/128)),
                   ((1048576.,.03125,1/128,1/256),1/256,(0,0,0,0),(1048576.,.0390625))])
    return result


def payload():
    data=bytearray(struct.pack('<3I',0x5253434c,1,len(records())))
    for p,dt,d,end in records():
        p=tuple(map(f32,p));dt=f32(dt)
        out,info,diag=expected(p,dt,d,end)
        data+=struct.pack('<8f7I8f4I',*p,0.,dt,0.,0.,*d,int(end is not None),
                          *struct.unpack('<2I',struct.pack('<2f',*(end or (0.,0.)))),
                          *out,*info,*diag)
    return data


@pytest.fixture
def artifacts():
    values=[os.environ.get(k) for k in ('RAFTSIM_CLOCK_GPU_EXE','RAFTSIM_CLOCK_GPU_SHADER')]
    if os.name!='nt' or not all(values):
        pytest.skip('Actual Windows clock shader and runner must be configured')
    paths=[Path(v).resolve() for v in values]
    assert all(p.is_file() for p in paths)
    return paths


def run(artifacts,tmp_path,data,backend='hardware'):
    path=tmp_path/'clock.bin';path.write_bytes(data)
    return subprocess.run([str(artifacts[0]),'run',str(artifacts[1]),str(path),backend],
                          capture_output=True,text=True,timeout=60)


@pytest.mark.parametrize('backend',['hardware','warp'])
def test_original_commit_phase_preserves_compensated_clock(artifacts,tmp_path,backend):
    result=run(artifacts,tmp_path,payload(),backend)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'clock_word_errors=0' in result.stdout


@pytest.mark.parametrize('damage',['header','truncated','extra'])
def test_bad_fixture_rejected(artifacts,tmp_path,damage):
    data=payload()
    if damage=='header': data[0]^=1
    elif damage=='truncated': data.pop()
    else: data.append(0)
    assert run(artifacts,tmp_path,data).returncode==2


def test_last_expected_word_is_checked(artifacts,tmp_path):
    data=payload();data[-4]^=1
    result=run(artifacts,tmp_path,data)
    assert result.returncode==1
    assert 'clock_word_errors=1' in result.stdout
