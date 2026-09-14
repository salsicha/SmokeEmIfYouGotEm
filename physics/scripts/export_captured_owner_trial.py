"""Export one trial from the actual captured evolved state and retained clock.

Fault isolation only: no changed source times, cropped cells, repaired states,
reconstructed history or gameplay qualification.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
from audit_live_temporal_evolution import observations


def pack(record):
    if record.get('schema') != 'raftsim.live_nonlinear_owner_audit.v1': raise ValueError('Invalid owner schema')
    clock=np.asarray(record['progress'],dtype=np.float32)
    if clock.shape!=(4,) or not np.isfinite(clock).all() or clock[2]<=0 or clock[3]<=0:
        raise ValueError('An active retained trial clock is required')
    time=float(clock[0])+float(clock[1]); origin=record['state_origin_meters']
    raw=record['observations']; matches=[]
    for i,(a,b) in enumerate(zip(raw,raw[1:])):
        if [a['origin_x'],a['origin_y']]==origin and [b['origin_x'],b['origin_y']]==origin and a['native_seconds']<=time<b['native_seconds']:
            matches.append(i)
    if len(matches)!=1:raise ValueError('Exactly one observed current-window bracket required')
    i=matches[0];a,b=observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',first=raw[i],second=raw[i+1]))
    if a['nx']!=128 or a['ny']!=128 or a['cell_meters']!=.5:raise ValueError('Expected actual128x128 half-metre owner')
    state=np.asarray(record['state'],dtype=np.float32).reshape(128,128,4)
    if not np.isfinite(state).all() or np.any(state[...,0]<0) or np.any(state[...,3]!=0):raise ValueError('Invalid evolved state')
    data=bytearray(struct.pack('<IIIIfdd',0x52535452,1,128,128,.5,a['native_seconds'],b['native_seconds']))
    for value in (clock,state,a['bed'],a['exterior_state'],b['exterior_state'],a['exterior_bed'],a['face_normal_velocity'],b['face_normal_velocity']):
        data+=np.asarray(value,dtype='<f4').tobytes()
    return data,dict(interval=i,origin_meters=origin,begin_native_seconds=time,progress=clock.astype(float).tolist(),
                     bracket=[a['native_seconds'],b['native_seconds']])


def pack_interval(source):
    """Append actual pending records without resetting any trial history."""
    data,record=pack(source)
    summary=np.asarray(source['summary']);flags=np.asarray(source['diagnostics'])
    ledger=np.asarray(source['cumulative_boundary_volume'],dtype=np.float32)
    for value in (summary,flags):
        if (value.shape!=(4,) or not np.isfinite(value).all() or np.any(value<0)
            or np.any(value>np.iinfo(np.uint32).max) or np.any(value!=np.floor(value))):
            raise ValueError('Actual uint32 interval records required')
    if (not 0<=summary[1]<=summary[0]<=4096 or summary[2]!=0 or summary[3]!=1
        or ledger.size!=2048 or not np.isfinite(ledger).all()):
        raise ValueError('Actual pending interval records and finite512-face ledger required')
    struct.pack_into('<I',data,4,2)
    for value,dtype in ((summary,'<u4'),(flags,'<u4'),(ledger,'<f4')):data+=np.asarray(value,dtype=dtype).tobytes()
    record.update(retained_summary=summary.tolist(),retained_diagnostics=flags.tolist(),cumulative_boundary_values=int(ledger.size))
    return data,record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--interval',action='store_true',help='Retain actual interval counters, diagnostics and cumulative exterior ledger')
    args=parser.parse_args();manifest=args.output.with_suffix('.json')
    if args.output.exists() or manifest.exists():raise FileExistsError(args.output)
    original=args.source.read_bytes();source=json.loads(original)
    data,record=(pack_interval if args.interval else pack)(source)
    record.update(schema='raftsim.captured_owner_interval.v1' if args.interval else 'raftsim.captured_owner_trial.v1',scope=__doc__,source=str(args.source.resolve()),
        source_sha256=hashlib.sha256(original).hexdigest(),input_sha256=hashlib.sha256(data).hexdigest())
    with args.output.open('xb') as stream:stream.write(data)
    with manifest.open('x') as stream:json.dump(record,stream,indent=2,allow_nan=False)
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
