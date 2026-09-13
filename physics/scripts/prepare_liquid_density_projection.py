"""Prepare a whole-river position-density solve from actual twelve-owner data.

No independent tile corrections: assemble the actual owner interiors into one
parent domain. No scene writes, particle deletion, bathymetry changes or native
integration claim. Exact bed quadrature is compared at two orders.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from liquid_dataset import resolve
from audit_liquid_native_transfer import audit as audit_transfer
from audit_liquid_native_interface import audit as audit_interface
from diagnose_liquid_projection_packet import load_field
from south_fork_registered_mesh import RegisteredMeshSampler
from liquid_density_projection import solid_kernel_fraction,density_target,solve


def prepare(directory,output,run_solve=False):
    directory=directory.resolve();output=output.resolve()
    if output.exists():raise FileExistsError(output)
    proof=audit_transfer(directory)
    if not proof['native_packet_p2g_verified']:raise ValueError('Actual complete native P2G proof required')
    audit_interface(directory)
    native=json.loads((directory/'stages.json').read_text());dataset=resolve(native)
    manifest=json.loads((dataset['regions']/'manifest.json').read_text())
    domain=manifest['domain'];physical=np.array(domain['physical_cells']);cells=np.array(domain['computational_cells'])
    h=np.array(domain['cell_size_m'])*100;edges=manifest['explicit_cell_edges']
    if native['native_transfer_packet_step']<2 or cells.tolist()!=[498,170,24]:raise ValueError('Expected validated whole South Fork reservoir grid')
    shape=tuple(cells[::-1]);rho=np.zeros(shape);boundary=np.zeros((*shape,4));phi=np.zeros(shape)
    written=np.zeros(shape,bool);regions=[]
    for r,pair in zip(native['native_transfer_packet'],native['native_interface_transport']['regions']):
        owner=r['region_id'];row,col=divmod(owner,4)
        width=edges[0][col+1]-edges[0][col];height=edges[1][row+1]-edges[1][row]
        offset=np.array([edges[0][col],physical[1]-edges[1][row+1]])
        if r['cells']!=[width+4,height+4,int(cells[2])]:raise ValueError('Owner dimensions changed')
        lo=np.array([0 if offset[a]==0 else 2 for a in range(2)])
        hi=np.array([width+4 if offset[0]+width==physical[0] else width+2,
                     height+4 if offset[1]+height==physical[1] else height+2])
        local=(slice(None),slice(lo[1],hi[1]),slice(lo[0],hi[0]))
        dest=(slice(None),slice(offset[1]+lo[1],offset[1]+hi[1]),slice(offset[0]+lo[0],offset[0]+hi[0]))
        if written[dest].any():raise ValueError('Parent reconstruction double-counted a halo')
        for name in (r['total'],pair['before']):
            if (directory/name).resolve().parent!=directory:raise ValueError('Captured field path escapes directory')
        total=np.fromfile(directory/r['total'],dtype='<f4').reshape(*r['cells'][::-1],4)[...,3]
        rho[dest]=total[local]/np.prod(h/100)
        boundary[dest]=load_field(directory,r,'projection_boundary',4)[local]
        phi[dest]=np.fromfile(directory/pair['before'],dtype='<f4').reshape(r['cells'][::-1])[local]
        written[dest]=True;regions.append(dict(region_id=owner,offset_xy=offset.tolist()))
    if not written.all():raise ValueError('Parent reconstruction has uncovered cells')
    r=native['native_transfer_packet'][0]
    axes=np.array([r['world_axis_x'],r['world_axis_y'],[0,0,1.]])
    lower=np.array(r['world_origin_cm'])-(np.array(r['extent_cm'])*[.5,.5,0])@axes
    lower-=np.array([regions[0]['offset_xy'][0]*h[0],regions[0]['offset_xy'][1]*h[1],0])@axes
    y,x=np.indices((cells[1],cells[0]));local=np.column_stack(((x.ravel()+.5)*h[0],(y.ravel()+.5)*h[1]))
    xy=(local@axes[:2,:2]+lower[:2])*[1,-1]
    bed_axes=axes[:2,:2]*[1,-1];heights=lower[2]+(np.arange(cells[2])+.5)*h[2]
    with np.load(dataset['mesh']) as mesh:sampler=RegisteredMeshSampler(mesh)
    bed=lambda x,y:100*sampler.sample(x/100,y/100)
    solid=np.zeros((cells[2],len(xy)));coarse=np.zeros_like(solid);started=time.perf_counter()
    for first in range(0,len(xy),2048):
        last=min(first+2048,len(xy))
        coarse[:,first:last]=solid_kernel_fraction(bed,xy[first:last],heights,h,bed_axes,2)
        solid[:,first:last]=solid_kernel_fraction(bed,xy[first:last],heights,h,bed_axes,4)
        if first%16384==0:print(f'exact-bed kernel columns {last}/{len(xy)}',flush=True)
    difference=abs(solid-coarse);solid=solid.reshape(shape)
    # A position-only correction may not create an extra river source or exit.
    # Fix exterior correction components via solid wall labels on outer halos.
    # This is distinct from physical momentum's prescribed hydraulic reservoir.
    exterior=np.zeros(shape,bool);exterior[:,:2,:]=True;exterior[:,-2:,:]=True
    exterior[:,:,:2]=True;exterior[:,:,-2:]=True
    boundary[...,:3]=0;boundary[exterior,3]=1
    # No native pressure solve exists in these provisional two Z-edge layers.
    boundary[:2,...,3]=1;boundary[-2:,...,3]=2
    target,stats=density_target(rho,solid,boundary)
    output.mkdir(parents=True)
    arrays=dict(particle_density=rho,solid_kernel_fraction=solid,boundary=boundary,phi=phi,target=target)
    status='prepared'
    if run_solve:
        try:
            delta,potential,projection=solve(rho,solid,boundary,h,max_iterations=500,tolerance=1e-6)
            arrays.update(displacement_cm=delta,potential_cm2=potential);stats['projection']=projection
            status='converged' if projection['solver']['converged'] else 'unconverged'
        except ValueError as error:
            status='rejected';stats['solve_error']=str(error)
    files={}
    for name,a in arrays.items():
        path=output/(name+'.bin');np.asarray(a,dtype='<f4').tofile(path)
        files[name]=dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    report=dict(schema='raftsim.liquid_density_projection_cases.v1',native_step=native['native_transfer_packet_step'],
        particles=proof['particle_count'],cells=cells.tolist(),spacing_cm=h.tolist(),world_lower_cm=lower.tolist(),world_axes=axes.tolist(),
        native_stages_sha256=hashlib.sha256((directory/'stages.json').read_bytes()).hexdigest(),
        registered_mesh_sha256=hashlib.sha256(dataset['mesh'].read_bytes()).hexdigest(),regions=regions,files=files,
        quadrature_orders=[2,4],maximum_solid_fraction_difference=float(difference.max()),
        rms_solid_fraction_difference=float(np.sqrt(np.mean(difference**2))),
        preparation_seconds=time.perf_counter()-started,statistics=stats,status=status,
        measured_terrain_changed=False,particle_mass_modified=False,native_integrated=False,
        boundary_limitation='Existing centered stair-step mobility and provisional Z layers; closed position-correction exterior, no per-particle pushout BC yet',
        physical_visual_or_performance_acceptance=False)
    (output/'manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return {k:v for k,v in report.items() if k not in ('files','regions')}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--solve',action='store_true');a=p.parse_args()
    print(json.dumps(prepare(a.directory,a.output,a.solve),indent=2,allow_nan=False))
