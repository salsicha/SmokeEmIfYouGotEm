"""Exact rational power-of-two scale fixtures for the portable GPU helper."""
import argparse
import hashlib
import json
from pathlib import Path
from fractions import Fraction
import struct
import numpy as np
from export_represented_float_fixtures import rounded_bits


def cases():
    for x in (0.,-0.,2.**-149,3*2.**-149,2.**-126-2.**-149,2.**-126,1.,float(np.finfo(np.float32).max)):
        for power in (-512,-277,-150,-149,-127,-126,-25,-24,-23,-1,0,1,23,126,127,149,277,512):
            for sign in (1,-1):yield sign*x,power
    rng=np.random.default_rng(665331)
    raw=rng.integers(0,0xffffffff,16384,dtype=np.uint32)
    raw[(raw&0x7f800000)==0x7f800000]&=np.uint32(0xff7fffff)
    for x,p in zip(raw.view(np.float32),rng.integers(-512,513,len(raw))):yield float(x),int(p)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();manifest=args.output.with_suffix('.json')
    if args.output.exists() or manifest.exists():raise FileExistsError(args.output)
    payload=bytearray()
    for value,power in cases():
        bits=struct.unpack('<I',struct.pack('<f',value))[0]
        expected=bits if bits&0x7fffffff==0 else rounded_bits(Fraction(value)*Fraction(2)**power)
        payload.extend(struct.pack('<ffffI',value,power,0,0,expected))
    data=struct.pack('<III',0x52534650,7,len(payload)//20)+payload
    with args.output.open('xb') as output:output.write(data)
    report=dict(count=len(payload)//20,fixture_sha256=hashlib.sha256(data).hexdigest(),
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with manifest.open('x') as output:json.dump(report,output,indent=2)
    print(json.dumps(report))


if __name__=='__main__':main()
