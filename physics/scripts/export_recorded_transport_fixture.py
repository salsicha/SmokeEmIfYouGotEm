"""Append an actual shallow-bank crop to preserved transport reference cases.

The crop is a closed-boundary operator fixture, not a full live interval or a
new observation. Original fixture payloads remain byte-identical.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
from audit_recorded_stages import read_records
from export_nonlinear_pressure_fixtures import fixture


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base',type=Path);parser.add_argument('trace',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();manifest=args.output.with_suffix('.json')
    if args.output.exists() or manifest.exists():raise FileExistsError(args.output)
    base=args.base.read_bytes();magic,version,count=struct.unpack('<III',base[:12])
    if magic!=0x52534656 or version!=1 or not 8<=count<32:raise ValueError('Invalid base transport fixture')
    meta=json.loads(args.trace.read_text());binary=Path(meta['binary']).read_bytes()
    trial,stages,*_=list(read_records(meta,binary))[18]
    stage=stages[0];state=stage['state'][74:81,69:76,:3];bed=stage['geometry'][74:81,69:76,1]
    fields,record=fixture(state,bed,.5,False,'nonbreaking',second_order=True)
    with args.output.open('xb') as stream:
        stream.write(struct.pack('<III',magic,version,count+1));stream.write(base[12:])
        stream.write(struct.pack('<IIIIff',7,7,0,1,.5,record['cfl_bound_s']))
        for i,field in enumerate([fields[0][...,1],fields[1],fields[2],fields[5],fields[3],fields[9],fields[4]]):
            stream.write(np.asarray(field,dtype='<u4' if i==3 else '<f4').tobytes())
    report=dict(scope=__doc__,source_trial=trial,source_stage=0,crop_yx=[74,69],shape=[7,7],
                original_cases=count,appended_cases=1,original_payload_unchanged=True,
                base_sha256=hashlib.sha256(base).hexdigest(),trace_binary_sha256=hashlib.sha256(binary).hexdigest(),
                fixture_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),reference=record)
    with manifest.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
