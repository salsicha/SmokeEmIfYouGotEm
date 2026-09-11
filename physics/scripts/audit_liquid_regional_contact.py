"""Compare actual regional GPU solid masks with preserved contact triangles.

Only physical XY interiors and non-border Z cells are checked. The inherited
numerical border is deliberately excluded: exterior/shared rules and wet mass
transfer are NOT established by an empty-grid terrain classification check.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from build_south_fork_liquid_contact import sample_packed

ROOT=Path(__file__).resolve().parents[2]


def query_centres(region):
    cells=np.asarray(region['computational_cells'],dtype=int)
    extent=np.asarray(region['computational_extents_m'],dtype=np.float64)*100
    origin=np.asarray(region['origin_canonical_cm'],dtype=np.float32)
    dx=np.asarray(region['axis_x_canonical'],dtype=np.float32)
    dy=np.asarray(region['axis_y_canonical'],dtype=np.float32)
    x,y=np.meshgrid(np.arange(2,cells[0]-2),np.arange(2,cells[1]-2))
    # Positive-scale Niagara Y is the opposite of canonical lateral Y.
    local=((np.column_stack((x.ravel(),y.ravel()))+.5)*extent[:2]/cells[:2]-extent[:2]/2).astype(np.float32)
    xy=origin[:2]+local[:,0,None]*dx-local[:,1,None]*dy
    z=(origin[2]+(np.arange(2,cells[2]-2)+.5)*extent[2]/cells[2]).astype(np.float32)
    return xy,z


def compare(region,contact,values):
    nx,ny,nz=region['computational_cells']
    if values.shape!=(nz,ny,nx,4) or not np.isfinite(values).all():
        raise ValueError('Complete finite RGBA16F native boundary volume required')
    xy,z=query_centres(region)
    bed=sample_packed(contact['packed_vectors'],xy,relative_vertices=True,anchored=True)
    if not np.isfinite(bed).all():
        raise ValueError('Canonical contact page does not cover actual physical query centres')
    actual=values[2:-2,2:-2,2:-2,3].reshape(len(z),-1)
    clearance=z[:,None]-bed[None,:]
    expected=np.where(clearance<=0,1,2) # static solid versus empty (zero water)
    mismatch=actual!=expected
    indices=np.argwhere(mismatch)
    examples=[dict(xy_cm=xy[j].tolist(),z_cm=float(z[k]),bed_cm=float(bed[j]),
        clearance_cm=float(clearance[k,j]),actual=float(actual[k,j]),expected=int(expected[k,j]))
        for k,j in indices[:12]]
    return dict(region_id=region['id'],checked_cells=int(actual.size),query_columns=len(xy),
        solid_cells=int((actual==1).sum()),empty_cells=int((actual==2).sum()),
        mismatches=int(mismatch.sum()),mismatch_examples=examples,
        nonzero_wall_velocity_cells=int(np.any(values[2:-2,2:-2,2:-2,:3]!=0,axis=-1).sum()))


def audit(directory):
    directory=Path(directory)
    capture=json.loads((directory/'capture.json').read_text())
    report=json.loads((directory/'stages.json').read_text())
    if not capture['complete'] or not report['zero_water'] or not report['canonical_regional_contact_installed'] or not report['boundary_readback_valid']:
        raise ValueError('Successful zero-water canonical-contact native capture required')
    if sorted(report['region_ids'])!=list(range(12)) or sorted(b['region_id'] for b in report['boundary_readbacks'])!=list(range(12)):
        raise ValueError('All twelve regional boundary readbacks required')
    states=ROOT/'tmp/south-fork-liquid-regional-state-20260910'
    geometry=ROOT/'tmp/south-fork-liquid-regional-geometry-v4-20260910'
    results=[]
    for item in report['boundary_readbacks']:
        region_id=item['region_id']
        region=json.loads((states/f'region-{region_id:03d}.json').read_text())
        contact=json.loads((geometry/f'region-{region_id:03d}-contact.json').read_text())
        nx,ny,nz=region['computational_cells']
        if contact['region_id']!=region_id or item['voxel_count']!=nx*ny*nz:
            raise ValueError('Readback/contact identity or allocation mismatch')
        path=directory/item['file']
        if path.resolve().parent!=directory.resolve(): raise ValueError('Readback outside capture directory')
        data=np.fromfile(path,dtype='<f2')
        if data.size!=nx*ny*nz*4: raise ValueError('Truncated native GPU boundary data')
        results.append(compare(region,contact,data.reshape(nz,ny,nx,4)))
    accepted=all(r['mismatches']==0 and r['nonzero_wall_velocity_cells']==0 for r in results)
    return dict(physical_interior_terrain_classification_verified=accepted,
        checked_cells=sum(r['checked_cells'] for r in results),regions=results,
        wet_particle_contact_verified=False,exterior_shared_boundary_verified=False,
        visual_or_performance_acceptance=False,classification_tolerance=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('capture');parser.add_argument('--output',required=True)
    args=parser.parse_args();output=Path(args.output)
    if output.exists(): raise FileExistsError('Retain previous regional contact evidence')
    result=audit(args.capture);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='regions'},indent=2))
    raise SystemExit(0 if result['physical_interior_terrain_classification_verified'] else 1)
