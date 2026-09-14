"""Independent rational MC/hydrostatic face fixtures for actual GPU evaluation."""
import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
from export_represented_float_fixtures import rounded_bits
from audit_captured_owner_trial import fields


def polynomial(depth,bed):
    h0,h,h1=map(lambda v:Q(float(v)),depth[:3]);z0,z,z1=map(lambda v:Q(float(v)),bed[:3])
    if not depth[3] or min(h0,h,h1)<=0:return h,z
    def mc(a,b):
        if a>0 and b>0:return min(2*a,(a+b)/2,2*b)
        if a<0 and b<0:return max(2*a,(a+b)/2,2*b)
        return Q(0)
    dh=mc(h-h0,h1-h);de=mc(h-h0+z-z0,h1-h+z1-z)
    direction=Q(float(bed[3]))
    return h+direction*dh/2,z+direction*(de-dh)/2


def expected(rows):
    hl,zl=polynomial(rows[0],rows[1]);hr,zr=polynomial(rows[2],rows[3])
    a=max(Q(0),hl-max(Q(0),zr-zl));b=max(Q(0),hr-max(Q(0),zl-zr))
    return [rounded_bits(v) for v in (hl,hr,a,b)]+[int(a>0),int(b>0),0,0]


def cases():
    tiny=2.**-149
    for h in (tiny,2*tiny,2.**-126,2.**-100,2.**-40,1.,2.**100):
        for datum in (0.,.5,100.,-100.,2.**120):
            for mask in range(4):
                yield 'constant_film',[(h,h,h,mask&1),(datum,datum,datum,1),
                                       (h,h,h,mask>>1),(datum,datum,datum,-1)]
    # A strictly positive half-minimum-subnormal face rounds to zero, but must
    # retain its exact positivity for flattening and wet-graph decisions.
    yield 'positive_rounds_zero',[(tiny,2*tiny,3*tiny,1),(0,0,0,-1),
                                 (tiny,tiny,tiny,0),(tiny,tiny,tiny,1)]
    rng=np.random.default_rng(718227)
    for _ in range(4096):
        raw=rng.integers(0,0x7f800000,(2,3),dtype=np.uint32)
        depths=raw.view(np.float32)
        raw_bed=rng.integers(0,0xffffffff,(2,3),dtype=np.uint32)
        raw_bed[(raw_bed&0x7f800000)==0x7f800000]&=np.uint32(0xff7fffff)
        beds=raw_bed.view(np.float32);mask=int(rng.integers(0,4))
        yield 'random_finite',[( *depths[0],mask&1),(*beds[0],1),
                               (*depths[1],mask>>1),(*beds[1],-1)]


def captured_cases(metadata_path):
    metadata=json.loads(metadata_path.read_text());binary=Path(metadata['binary']).read_bytes()
    data=fields(metadata,binary);input_path=Path(metadata['input']);raw=input_path.read_bytes()
    manifest=json.loads(input_path.with_suffix('.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==manifest['input_sha256']
    assert struct.unpack_from('<IIII',raw)==(0x52535452,1,128,128)
    bed=np.frombuffer(raw,'<f4',128*128,36+16+128*128*16).reshape(128,128)
    for stage in ('input_state','euler_state'):
        h=data[stage].reshape(128,128,4)[...,0]
        for axis in (0,1):
            for y,x in ((79,87),(79,88),(109,112),(109,113)):
                l=np.array((y,x));r=l.copy();r[axis]+=1;d=np.zeros(2,dtype=int);d[axis]=1
                p=[tuple(l-d),tuple(l),tuple(l+d)];q=[tuple(r-d),tuple(r),tuple(r+d)]
                for mask in range(4):
                    yield f'{stage}_{axis}_{y}_{x}_{mask}',[
                        (*[h[i] for i in p],mask&1),(*[bed[i] for i in p],1),
                        (*[h[i] for i in q],mask>>1),(*[bed[i] for i in q],-1)]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--captured-trial',type=Path)
    args=parser.parse_args();manifest=args.output.with_suffix('.json')
    if args.output.exists() or manifest.exists():raise FileExistsError(args.output)
    records=list(cases())
    if args.captured_trial:records+=list(captured_cases(args.captured_trial))
    payload=bytearray(struct.pack('<III',0x52534650,5,len(records)))
    for name,rows in records:
        represented=np.asarray(rows,dtype='<f4')
        payload.extend(represented.tobytes());payload.extend(struct.pack('<8I',*expected(represented)))
    args.output.write_bytes(payload)
    report=dict(scope=__doc__,count=len(records),fixture_sha256=hashlib.sha256(payload).hexdigest(),
        generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        rounding_sha256=hashlib.sha256(Path(__file__).with_name('export_represented_float_fixtures.py').read_bytes()).hexdigest(),
        captured_trial=str(args.captured_trial) if args.captured_trial else None,
        captured_sha256=hashlib.sha256(Path(json.loads(args.captured_trial.read_text())['binary']).read_bytes()).hexdigest() if args.captured_trial else None,
        scene_accepted=False)
    manifest.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


if __name__=='__main__':main()
