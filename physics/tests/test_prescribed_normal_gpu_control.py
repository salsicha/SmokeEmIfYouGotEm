"""Exact original-plane oracle and optional actual hardware/WARP execution."""
from fractions import Fraction as F
import os
from pathlib import Path
import struct
import subprocess

import numpy as np
import pytest


def f32(value):
    return float(np.float32(value))


def cases():
    normal=tuple(map(f32,(.929999828338623,.36755993962287903,0)))
    result=[((-12066.3125,-5790.435546875,647.5684814453125),
             (-12066.3134765625,-5790.43408203125,647.5401611328125),normal,0.)]
    for n in (normal,tuple(-v for v in normal),(-normal[1],normal[0],0),(normal[1],-normal[0],0)):
        for scale in (-15000.,-1.,1.,15000.):
            for travel in map(f32,(0.,.001,.05,3.)):
                start=(scale,f32(scale*f32(.731)),650.)
                tangent=(-n[1],n[0],0.)
                norm=sum(v*v for v in n)
                candidate=tuple(f32(start[j]+tangent[j]*.037+n[j]*travel/norm+(0 if j<2 else -.028)) for j in range(3))
                result.append((start,candidate,n,travel))
    return result


def exact_position(start,candidate,normal,travel):
    axis=0 if abs(normal[0])>=abs(normal[1]) else 1
    s,c,n=([F(v) for v in row] for row in (start,candidate,normal))
    ideal=(F(travel)+sum(s[j]*n[j] for j in range(3))-sum(c[j]*n[j] for j in range(3) if j!=axis))/n[axis]
    output=list(candidate);output[axis]=f32(float(ideal))
    residual=sum((F(output[j])-s[j])*n[j] for j in range(3))-F(travel)
    if residual<0:
        output[axis]=float(np.nextafter(np.float32(output[axis]),np.float32(np.inf if n[axis]>0 else -np.inf)))
    return output


def test_exact_oracle_agrees_with_unchanged_native_double_oracle():
    for index,(s,c,n,travel) in enumerate(cases()):
        axis=0 if abs(n[0])>=abs(n[1]) else 1
        residual=sum((c[j]-s[j])*n[j] for j in range(3))-travel
        native=list(c);native[axis]=f32(c[axis]-residual/n[axis])
        if sum((native[j]-s[j])*n[j] for j in range(3))<travel:
            native[axis]=float(np.nextafter(np.float32(native[axis]),np.float32(np.inf if n[axis]>0 else -np.inf)))
        assert native==exact_position(s,c,n,travel),index


def payload(rows=None):
    rows=cases() if rows is None else rows
    inputs,outputs=bytearray(),bytearray()
    for s,c,n,t in rows:
        inputs+=struct.pack('<16f',*s,0,*c,0,*n,0,t,0,0,0)
        outputs+=struct.pack('<4f',*exact_position(s,c,n,t),0)
    return bytearray(struct.pack('<3I',0x52534e50,1,len(rows))+inputs+outputs)


@pytest.fixture
def artifacts():
    values=[os.environ.get(k) for k in ('RAFTSIM_NORMAL_GPU_EXE','RAFTSIM_NORMAL_GPU_SHADER')]
    if os.name!='nt' or not all(values):pytest.skip('Explicit hardware runner and shader required')
    result=[Path(v).resolve() for v in values]
    assert all(p.is_file() for p in result)
    return result


def run(artifacts,tmp_path,data,backend='hardware'):
    fixture=tmp_path/'normal.bin';fixture.write_bytes(data)
    return subprocess.run([str(artifacts[0]),'run',str(artifacts[1]),str(fixture),backend],capture_output=True,text=True,timeout=60)


@pytest.mark.parametrize('backend',['hardware','warp'])
def test_original_normal_positions(artifacts,tmp_path,backend):
    result=run(artifacts,tmp_path,payload(),backend)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'cases=65 normal_word_errors=0' in result.stdout


@pytest.mark.parametrize('backend',['hardware','warp'])
def test_seeded_projected_positions_against_exact_plane(artifacts,tmp_path,backend):
    rng=np.random.default_rng(20260917)
    rows=[]
    for i in range(512):
        angle=float(rng.uniform(-np.pi,np.pi))
        n=tuple(map(f32,(np.cos(angle),np.sin(angle),0)))
        scale=2.**int(rng.integers(-10,20))
        s=tuple(map(f32,(rng.uniform(-1,1)*scale,rng.uniform(-1,1)*scale,650)))
        travel=f32(rng.choice([0.,.001,.05,3.]))
        tangent=(-n[1],n[0],0.)
        norm=sum(v*v for v in n)
        c=tuple(f32(s[j]+tangent[j]*.037+n[j]*travel/norm+(0 if j<2 else -.028)) for j in range(3))
        rows.append((s,c,n,travel))
    result=run(artifacts,tmp_path,payload(rows),backend)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'cases=512 normal_word_errors=0' in result.stdout


@pytest.mark.parametrize('damage',['header','truncated','extra'])
def test_malformed_fixture_rejected(artifacts,tmp_path,damage):
    data=payload()
    if damage=='header':data[0]^=1
    elif damage=='truncated':data.pop()
    else:data.append(0)
    assert run(artifacts,tmp_path,data).returncode==2


def test_last_expected_word_checked(artifacts,tmp_path):
    data=payload();data[-4]^=1
    result=run(artifacts,tmp_path,data)
    assert result.returncode==1
    assert 'normal_word_errors=1' in result.stdout
