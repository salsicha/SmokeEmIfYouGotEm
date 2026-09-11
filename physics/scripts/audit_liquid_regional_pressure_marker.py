"""Audit native first-color GPU pressure before any shared-halo exchange.

This deliberately contains no liquid. Each owner starts with a different exact
nonzero pressure. The first global color clears solid/empty owned cells, leaves
the other color alone, and must not overwrite imported shared-halo pressure.
It verifies dispatch/ownership, not a wet pressure solution or performance.
"""
import argparse
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]


def expected_marker(region, boundary, parent_cells):
    nx,ny,nz=region['computational_cells']
    z,y,x=np.indices((nz,ny,nx))
    first,upper=region['cell_bounds_xy']
    gx=x+first[0]
    gy=y+parent_cells[1]-upper[1]
    first_color=(gx//2+gy//2+z//2)%2==0
    shared=np.zeros((ny,nx),dtype=bool)
    # Use independently prepared physical-owner maps, not the C++ predicate.
    for dx,dy,source,sx,sy in boundary['shared_halo_columns']:
        shared[ny-1-dy,dx]=True
    expected=np.full((nz,ny,nx),1000+region['id'],dtype=np.float32)
    expected[first_color & ~shared[None,:,:]]=0
    return expected,first_color,shared


def compare(region,boundary,parent_cells,actual):
    expected,color,shared=expected_marker(region,boundary,parent_cells)
    if actual.shape!=expected.shape or not np.isfinite(actual).all():
        raise ValueError('Complete finite R32F native pressure volume required')
    bad=actual!=expected
    examples=[dict(zyx=p.tolist(),actual=float(actual[tuple(p)]),expected=float(expected[tuple(p)]))
              for p in np.argwhere(bad)[:8]]
    return dict(region_id=region['id'],checked_cells=int(actual.size),mismatches=int(bad.sum()),
                first_color_cells=int(color.sum()),shared_cells=int(shared.sum()*actual.shape[0]),
                retained_marker_cells=int((expected!=0).sum()),mismatch_examples=examples)


def audit(directory):
    directory=Path(directory)
    capture=json.loads((directory/'capture.json').read_text())
    report=json.loads((directory/'stages.json').read_text())
    required=('zero_water','regional_compatible_projection_installed',
              'nonzero_pressure_marker_requested','nonzero_pressure_marker_seeded',
              'nonzero_pressure_marker_readback_valid','scheduler_alignment_observed')
    if not capture['complete'] or not all(report.get(k) for k in required):
        raise ValueError('Successful actual regional pressure marker capture required')
    files=report['pressure_marker_readbacks']
    if sorted(report['region_ids'])!=list(range(12)) or sorted(p['region_id'] for p in files)!=list(range(12)):
        raise ValueError('All twelve native pressure volumes required')
    state_dir=ROOT/'tmp/south-fork-liquid-regional-state-20260910'
    geometry=ROOT/'tmp/south-fork-liquid-regional-geometry-v4-20260910'
    parent=json.loads((ROOT/'tmp/south-fork-whole-rapid-liquid-float-seeds-20260910/grid_boundary_profile.json').read_text())
    parent_cells=parent['packed_vectors'][5]
    results=[]
    for item in files:
        rid=item['region_id']
        region=json.loads((state_dir/f'region-{rid:03d}.json').read_text())
        boundary=json.loads((geometry/f'region-{rid:03d}-boundary.json').read_text())
        nx,ny,nz=region['computational_cells']
        path=directory/item['file']
        if path.resolve().parent!=directory.resolve() or item['voxel_count']!=nx*ny*nz:
            raise ValueError('Pressure readback path or extent mismatch')
        data=np.fromfile(path,dtype='<f4')
        if data.size!=nx*ny*nz: raise ValueError('Truncated native pressure data')
        results.append(compare(region,boundary,parent_cells,data.reshape(nz,ny,nx)))
    accepted=all(r['mismatches']==0 for r in results)
    return dict(global_phase_and_shared_pressure_preservation_verified=accepted,
                checked_cells=sum(r['checked_cells'] for r in results),regions=results,
                absolute_tolerance=0,wet_pressure_solution_verified=False,
                fluid_or_performance_acceptance=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('capture');parser.add_argument('--output',required=True)
    args=parser.parse_args();output=Path(args.output)
    if output.exists(): raise FileExistsError('Retain previous pressure marker evidence')
    result=audit(args.capture);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='regions'},indent=2))
    raise SystemExit(0 if result['global_phase_and_shared_pressure_preservation_verified'] else 1)
