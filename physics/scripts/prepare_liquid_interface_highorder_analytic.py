"""Small repeated-step and failure GPU fixtures; no river data is changed."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_interface_highorder import advect_limited


def prepare(output):
    output=output.resolve()
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True);cases=[]
    z,y,x=np.indices((10,10,48));base=100*(z+.5)-400-70*np.exp(-((x+.5-14)/2)**2)
    for k,name in enumerate(('stationary','crest-24-steps','unsupported-forward','all-solid','affine-metric')):
        phi=base.astype('<f4').astype(float);h=np.array([100,100,100.]);dt=1.;steps=24 if k==1 else 1
        velocity=np.zeros((*phi.shape,4),dtype='<f2');velocity[...,0]=0 if k==0 else 30
        solid=np.full(phi.shape,k==3,bool)
        if k==2:velocity[...,0]=30000
        if k==4:
            h=np.array([70,120,60.]);dt=float(np.float32(.2));phi=(60*(z+.5)+.2*70*(x+.5)).astype('<f4').astype(float)
            velocity[...,1]=-10;velocity[...,2]=15
        actual=phi.copy()
        for _ in range(steps):
            actual,status=advect_limited(actual,velocity[...,:3].astype(float),h,dt,[2,2,2],[46,8,8],True,solid=solid)
            # A persistent native R32F texture is written at every step.
            actual=actual.astype('<f4').astype(float)
        row=dict(region_id=100+k,name=name,cells=[48,10,10],spacing_cm=h.tolist(),dt=dt,steps=steps,
            limited_transport=status,scalar_arithmetic_gpu_tolerance_cm=.02)
        for field,array in (('phi',phi.astype('<f4')),('velocity',velocity),('solid',solid.astype('<u4')),('expected',actual.astype('<f4'))):
            path=output/f'{name}-{field}.bin';array.tofile(path)
            row[field+'_file']=str(path) if field in ('phi','velocity') else path.name
            row[field+'_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        cases.append(row)
    source=Path(__file__)
    result=dict(schema='raftsim.interface_highorder_analytic.v1',cases=cases,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        transport_source_sha256=hashlib.sha256((source.parent/'liquid_interface_highorder.py').read_bytes()).hexdigest())
    (output/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps([dict(name=r['name'],steps=r['steps'],status=r['limited_transport']) for r in cases],indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    prepare(p.parse_args().output)
