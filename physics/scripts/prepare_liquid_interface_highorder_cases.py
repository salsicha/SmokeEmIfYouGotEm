"""Actual twelve-owner interface/velocity cases for limited BFECC GPU integration.

Operator evidence at one captured native step, not an evolved high-order river.
Retains source paths/hashes instead of copying large immutable capture inputs.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from audit_liquid_native_interface import audit as audit_interface
from diagnose_liquid_projection_packet import load_field
from liquid_interface_highorder import advect_limited
from liquid_interface_transport import advect


def prepare(capture,output):
    capture=capture.resolve();output=output.resolve();started=time.perf_counter()
    if output.exists():raise FileExistsError(output)
    proof=audit_interface(capture)
    m=json.loads((capture/'stages.json').read_text())
    if not proof['compact_transport']:raise ValueError('Same compact velocity as current native markers required')
    source_names=['prepare_liquid_interface_highorder_cases.py','liquid_interface_highorder.py','liquid_interface_transport.py',
        'liquid_volume_interface.py','liquid_compatible_advection.py']
    sources={n:(Path(__file__).parent/n).read_bytes() for n in source_names}
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    output.mkdir(parents=True);(output/'sources').mkdir()
    for n,b in sources.items():(output/'sources'/n).write_bytes(b)
    records=[];dt=m['native_interface_transport']['fluid_delta_seconds'][-1]
    for r,pair in zip(m['native_transfer_packet'],m['native_interface_transport']['regions']):
        if r['region_id']!=pair['region_id']:raise ValueError('Current scalar/velocity owner mismatch')
        phi_path=(capture/pair['before']).resolve()
        if phi_path.parent!=capture:raise ValueError('Source escapes capture')
        cells=np.array(r['cells']);phi=np.fromfile(phi_path,dtype='<f4').reshape(cells[::-1]).astype(float)
        velocity=load_field(capture,r,'advection_velocity',4)[...,:3]
        boundary=load_field(capture,r,'projection_boundary',4)[...,3]
        solid=np.isin(boundary,[1,3]);h=np.asarray(np.array(r['extent_cm'])/cells,dtype='<f4').astype(float)
        low,a=advect(phi,velocity,h,dt,np.full(3,2),cells-2,True)
        high,b=advect_limited(phi,velocity,h,dt,np.full(3,2),cells-2,True,solid=solid)
        if not a['candidate_step_valid'] or not b['candidate_step_valid']:raise ValueError('Captured forward transport is not fully supported')
        path=output/f'expected-{r["region_id"]:03d}.r32f';high.astype('<f4').tofile(path)
        solid_path=output/f'solid-{r["region_id"]:03d}.u32';solid.astype('<u4').tofile(solid_path)
        row=dict(region_id=r['region_id'],cells=cells.tolist(),spacing_cm=h.tolist(),dt=dt,
            phi_file=str(phi_path),phi_sha256=sha(phi_path),
            velocity_file=str(capture/r['advection_velocity']),velocity_sha256=sha(capture/r['advection_velocity']),
            boundary_file=str(capture/r['projection_boundary']),boundary_sha256=sha(capture/r['projection_boundary']),
            expected_file=path.name,expected_sha256=sha(path),solid_file=solid_path.name,solid_sha256=sha(solid_path),
            limited_transport=b,max_change_from_first_order_cm=float(abs(high-low).max()),
            rms_change_from_first_order_cm=float(np.sqrt(np.mean((high-low)**2))),
            accuracy_or_volume_gain_on_this_state_proven=False)
        records.append(row);print(json.dumps(row),flush=True)
    unchanged=all((Path(__file__).parent/n).read_bytes()==b for n,b in sources.items())
    report=dict(schema='raftsim.interface_highorder_cases.v1',capture=str(capture),native_stages_sha256=sha(capture/'stages.json'),
        cases=records,algorithm_sources_sha256={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},
        sources_unchanged=unchanged,total_samples=sum(int(np.prod(r['cells'])) for r in records),
        scalar_arithmetic_gpu_tolerance_cm=.02,method='limited-bfecc-rk2',
        native_integrated=False,physical_visual_or_performance_acceptance=False,elapsed_seconds=time.perf_counter()-started)
    (output/'manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    if not unchanged:raise ValueError('Reference sources changed during case generation')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();prepare(a.capture,a.output)
