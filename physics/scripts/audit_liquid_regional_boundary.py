"""Check full native boundary tuples at every shared face/corner halo.

The actual zero-water native run proves same-step boundary synchronization and
preserved terrain, not moving liquid, mass exchange, exterior forcing or visuals.
"""
import argparse
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]


def compare(volumes,columns):
    for data in volumes.values():
        if data.ndim!=4 or data.shape[-1]!=4 or data.dtype!=np.dtype('<f2') or not np.isfinite(data).all():
            raise ValueError('Complete finite native RGBA16F boundary data required')
    written=set();checked=0;mismatches=0;examples=[]
    for source,dest,sx,sy,dx,dy in columns:
        if source==dest or source not in volumes or dest not in volumes:
            raise ValueError('Distinct present physical owners required')
        sv,dv=volumes[source],volumes[dest]
        if sv.shape[0]!=dv.shape[0] or not (2<=sx<sv.shape[2]-2 and 2<=sy<sv.shape[1]-2):
            raise ValueError('Physical source and matching Z dimensions required')
        if not (0<=dx<dv.shape[2] and 0<=dy<dv.shape[1]) or (2<=dx<dv.shape[2]-2 and 2<=dy<dv.shape[1]-2):
            raise ValueError('Only a valid halo destination may be written')
        if (dest,dx,dy) in written: raise ValueError('Duplicate shared halo destination')
        written.add((dest,dx,dy))
        actual=dv[:,dy,dx,:];expected=sv[:,sy,sx,:]
        # Exact native half bits, including velocity signs; no type averaging.
        bad=np.any(actual.view('<u2')!=expected.view('<u2'),axis=-1)
        checked+=sv.shape[0];mismatches+=int(bad.sum())
        for z in np.flatnonzero(bad):
            if len(examples)<12:
                examples.append(dict(source=source,dest=dest,source_xy=[sx,sy],dest_xy=[dx,dy],
                                     z=int(z),actual=actual[z].tolist(),expected=expected[z].tolist()))
    return dict(checked_columns=len(written),checked_cells=checked,mismatches=mismatches,mismatch_examples=examples)


def audit(directory):
    directory=Path(directory)
    capture=json.loads((directory/'capture.json').read_text())
    report=json.loads((directory/'stages.json').read_text())
    keys=('zero_water','shared_boundary_exchange_enabled','canonical_regional_contact_installed',
          'regional_compatible_projection_installed','boundary_readback_valid','scheduler_alignment_observed')
    if not capture['complete'] or not all(report.get(k) for k in keys) or report['exchange_error']:
        raise ValueError('Successful native shared-boundary capture required')
    groups=sum(g['entries'][0]['name']=='Compute Boundary' for g in report['groups'])
    if report['boundary_halo_dispatches']!=groups or groups<=0:
        raise ValueError('Every native boundary stage must exchange before downstream stages')
    files=report['boundary_readbacks']
    if sorted(report['region_ids'])!=list(range(12)) or sorted(b['region_id'] for b in files)!=list(range(12)):
        raise ValueError('All twelve native boundary volumes required')
    geometry=ROOT/'tmp/south-fork-liquid-regional-geometry-v4-20260910'
    pages={i:json.loads((geometry/f'region-{i:03d}-boundary.json').read_text()) for i in range(12)}
    columns=[];volumes={}
    for dest,page in pages.items():
        for dx,dy,source,sx,sy in page['shared_halo_columns']:
            columns.append((source,dest,sx,pages[source]['computational_cells'][1]-1-sy,
                            dx,page['computational_cells'][1]-1-dy))
    if sorted(columns)!=sorted(map(tuple,report['halo_columns_niagara'])):
        raise ValueError('Runtime addresses differ from independently prepared physical ownership')
    for item in files:
        rid=item['region_id'];nx,ny,nz=pages[rid]['computational_cells']
        path=directory/item['file']
        if path.resolve().parent!=directory.resolve() or item['voxel_count']!=nx*ny*nz:
            raise ValueError('Readback path or extent mismatch')
        data=np.fromfile(path,dtype='<f2')
        if data.size!=nx*ny*nz*4: raise ValueError('Truncated native boundary volume')
        volumes[rid]=data.reshape(nz,ny,nx,4)
    result=compare(volumes,columns)
    result.update(shared_boundary_owner_values_verified=result['mismatches']==0,
                  native_boundary_exchanges=groups,absolute_tolerance=0,
                  wet_boundary_or_mass_transfer_verified=False,exterior_forcing_verified=False,
                  visual_or_performance_acceptance=False)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('capture');parser.add_argument('--output',required=True)
    args=parser.parse_args();output=Path(args.output)
    if output.exists(): raise FileExistsError('Retain prior boundary evidence')
    result=audit(args.capture);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['shared_boundary_owner_values_verified'] else 1)
