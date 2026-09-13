"""Full captured South Fork shared density/contact map and interface CPU trial.

No production or native state is changed. Uses current particle IDs/positions,
current paired scalar/phase and only the static, source-verified bed integral
from an older geometry package. Rejected candidates stay explicitly rejected.
"""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path
import numpy as np
from audit_liquid_native_dense import audit as audit_dense
from audit_liquid_native_handoff import read
from audit_liquid_particle_routes import physical_owners
from diagnose_liquid_projection_packet import load_field
from liquid_dataset import resolve
from liquid_particle_density import objective
from liquid_shared_density import shared_direction,constrained_field
from liquid_compatible_advection import sample_compact
from liquid_correction_map import transport_interface
from liquid_particle_quantization import quantized_endpoint
from liquid_swept_bed import swept_clearance
from liquid_volume_interface import sample_centred
from south_fork_registered_mesh import RegisteredMeshSampler
from audit_liquid_coincident_particles import coincident_rows
from liquid_map_injectivity import compact_map_bound


def run(capture,geometry,output,*,native_positions=False,max_sweeps=512,active_set=False):
    capture=capture.resolve();geometry=geometry.resolve();output=output.resolve();started=time.perf_counter()
    if output.exists():raise FileExistsError(output)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if not audit_dense(capture)['dense_native_state_verified']:raise ValueError('Complete verified native state required')
    native=json.loads((capture/'stages.json').read_text());dataset=resolve(native)
    meta=json.loads((geometry/'manifest.json').read_text());cells=np.array(meta['cells']);h=np.array(meta['spacing_cm'])
    axes=np.array(meta['world_axes']);lower=np.array(meta['world_lower_cm'])
    regions=json.loads((dataset['regions']/'manifest.json').read_text());domain=regions['domain']
    packets=native['native_transfer_packet'];pairs=native['native_interface_transport']['regions']
    first=packets[0]
    expected_lower=np.array(first['world_origin_cm'])-(np.array(first['extent_cm'])*[.5,.5,0])@axes
    expected_lower-=np.r_[meta['regions'][0]['offset_xy'],0]*h@axes
    if (sha(dataset['mesh'])!=meta['registered_mesh_sha256'] or cells.tolist()!=domain['computational_cells'] or
            not np.array_equal(h,np.array(domain['cell_size_m'])*100) or
            not np.array_equal(axes,np.array([first['world_axis_x'],first['world_axis_y'],[0,0,1]])) or
            not np.allclose(lower,expected_lower,rtol=0,atol=1e-10) or
            meta.get('unresolved_solid_kernel_columns',1)!=0 or meta['solid_quadrature_tolerance']>.001):
        raise ValueError('Unchanged captured frame, mesh and converged static bed integral required')
    item=meta['files']['solid_kernel_fraction'];path=(geometry/item['file']).resolve()
    if path.parent!=geometry or sha(path)!=item['sha256']:raise ValueError('Bed-kernel provenance changed')
    solid=np.fromfile(path,dtype='<f4').reshape(cells[::-1]).astype(float)
    positions=np.concatenate([read(capture,r,'positions',(r['particle_count'],4)).view('<f4')[:,:3].astype(float) for r in packets])
    identities=np.concatenate([read(capture,r,'identities',(r['particle_count'],4)) for r in packets])
    volumes=np.concatenate([np.full(r['particle_count'],float(np.float32(r['particle_volume_m3']))*1e6) for r in packets])
    duplicate_groups=coincident_rows(positions)
    if duplicate_groups:
        # A shared map cannot undo an existing exact collision. Reject before
        # spending time on futile smaller steps or misattributing it to rounding.
        raise ValueError(f'Native input already has {len(duplicate_groups)} coincident groups; trace/fix earlier motion, do not split or merge particles')
    survey=[json.loads((dataset['regions']/f'region-{i:03d}.json').read_text()) for i in range(12)]
    local=(positions-lower)@axes.T;lo=np.array([2*h[0],2*h[1],0]);hi=(cells-[2,2,0])*h
    if np.any((local<lo)|(local>hi)) or np.any(physical_owners(positions,survey)<0):raise ValueError('Input outside unchanged survey')
    with np.load(dataset['mesh']) as mesh:sampler=RegisteredMeshSampler(mesh)
    clearance=positions[:,2]-100*sampler.sample(positions[:,0]/100,-positions[:,1]/100)
    if (clearance<0).any():raise ValueError('Input penetrates captured bed')
    required=np.minimum(clearance,2.)
    # Each physical owner owns its adjacent outer extension. Internal shared
    # halos are NOT averaged. Provisional outer extensions remain unverified
    # physical boundary conditions; this CPU correction does not bless them.
    phi=np.zeros(cells[::-1]);boundary=np.zeros((*cells[::-1],4));written=np.zeros(cells[::-1],bool)
    edges=regions['explicit_cell_edges'];physical=np.array(domain['physical_cells']);inputs={}
    for r,pair in zip(packets,pairs,strict=True):
        owner=r['region_id']
        if pair['region_id']!=owner:raise ValueError('Paired scalar owner mismatch')
        row,col=divmod(owner,4);width=edges[0][col+1]-edges[0][col];height=edges[1][row+1]-edges[1][row]
        offset=np.array([edges[0][col],physical[1]-edges[1][row+1]])
        if r['cells']!=[width+4,height+4,int(cells[2])]:raise ValueError('Owner frame changed')
        a=np.where(offset==0,0,2)
        b=np.array([width+4 if offset[0]+width==physical[0] else width+2,height+4 if offset[1]+height==physical[1] else height+2])
        src=(slice(None),slice(a[1],b[1]),slice(a[0],b[0]))
        dest=(slice(None),slice(offset[1]+a[1],offset[1]+b[1]),slice(offset[0]+a[0],offset[0]+b[0]))
        path=(capture/pair['before']).resolve()
        if path.parent!=capture or written[dest].any():raise ValueError('Invalid scalar ownership')
        phi[dest]=np.fromfile(path,dtype='<f4').reshape(r['cells'][::-1])[src]
        boundary[dest]=load_field(capture,r,'projection_boundary',4)[src];written[dest]=True
        inputs[path.name]=sha(path);inputs[r['projection_boundary']]=sha(capture/r['projection_boundary'])
    if not written.all() or not np.isfinite(phi).all() or not np.isin(boundary[...,3],[0,1,2,3]).all():raise ValueError('Invalid assembled state')
    selected=np.isin(boundary[...,3],[0,2]);selected[:2]=False;selected[-2:]=False
    selected[:,:2]=False;selected[:,-2:]=False;selected[:,:,:2]=False;selected[:,:,-2:]=False
    mobility=np.repeat(selected[...,None],3,axis=-1).astype(float)
    names=['solve_liquid_shared_density.py','liquid_shared_density.py','liquid_particle_density.py','liquid_affine_transfer.py',
        'liquid_boundary_displacement.py','liquid_compatible_advection.py','liquid_correction_map.py','liquid_volume_interface.py',
        'liquid_particle_quantization.py','liquid_swept_bed.py','liquid_edge_visibility.py','south_fork_registered_mesh.py',
        'liquid_contact_active_set.py','audit_liquid_coincident_particles.py','liquid_map_injectivity.py']
    sources={n:(Path(__file__).parent/n).read_bytes() for n in names}
    output.mkdir(parents=True);(output/'sources').mkdir()
    for n,data in sources.items():(output/'sources'/n).write_bytes(data)
    def log(event):
        event.update(elapsed_seconds=time.perf_counter()-started)
        with (output/'progress.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event,allow_nan=False)+'\n')
        brief=dict(event)
        if event.get('event')=='trial':
            brief.pop('interface_batches',None)
            brief['contact']={k:v for k,v in event['contact'].items() if k!='history'}
            brief['contact']['geometric_iterations']=len(event['contact']['history'])
        print(json.dumps(brief,allow_nan=False),flush=True)
    metrics=lambda r:{k:v for k,v in r.items() if not isinstance(v,np.ndarray)}
    before=objective(local,cells,h,volumes,solid);log(dict(event='density',pid=os.getpid(),**metrics(before)))
    desired,direction=shared_direction(local,before['gradient'],cells,h,mobility)
    log(dict(event='shared_direction',**direction));trials=[];accepted=False
    for backtrack in range(12):
        alpha=2.**-backtrack
        delta,contact=constrained_field(positions,local,alpha*desired,axes,h,lo,hi,sampler,required,mobility,
            native_positions=native_positions,max_sweeps=max_sweeps,active_set=active_set)
        trial=dict(alpha=alpha,contact=contact,rejections=[]);trials.append(trial)
        if not contact['converged']:
            trial['rejections'].append('shared contact projection');log(dict(event='trial',**trial));continue
        certificate=compact_map_bound(delta,h);trial['continuous_map_certificate']=certificate
        if not certificate['continuous_map_globally_injective']:
            trial['rejections'].append('no global continuous-map no-fold certificate');log(dict(event='trial',**trial));continue
        move=sample_compact(local,delta.transpose(2,1,0,3),h)
        updated=positions+move@axes
        if native_positions:updated,_=quantized_endpoint(positions,move@axes,float(np.linalg.norm(h)))
        actual=(updated-lower)@axes.T;slope=float(np.sum(before['gradient']*((updated-positions)@axes.T)))
        after=objective(actual,cells,h,volumes,solid,derivatives=False)
        swept,_,_=swept_clearance(sampler,positions*[1,-1,1]/100,updated*[1,-1,1]/100);margin=100*swept-required
        outside=int((physical_owners(updated,survey)<0).sum())
        coincidences=len(updated)-len(np.unique(updated,axis=0))
        trial.update(after=metrics(after),directional_derivative=slope,minimum_required_margin_cm=float(margin.min()),
            minimum_swept_clearance_cm=float(100*swept.min()),survey_outside=outside,coincident_particles=coincidences)
        if slope>=0 or after['energy']>before['energy']+1e-4*slope:trial['rejections'].append('density energy')
        if (swept<0).any() or (margin < -1e-6).any():trial['rejections'].append('exact bed path')
        if outside or np.any((actual<lo)|(actual>hi)):trial['rejections'].append('original exterior')
        if coincidences:trial['rejections'].append('coincident positions')
        if trial['rejections']:log(dict(event='trial',**trial));continue
        # Same finite map inverse, immutable old scalar, batched query work.
        transported=phi.copy();z,y,x=np.nonzero(selected);reports=[]
        for first in range(0,len(x),32768):
            choose=np.zeros(phi.shape,bool);choose[z[first:first+32768],y[first:first+32768],x[first:first+32768]]=True
            part,proof=transport_interface(phi,delta,h,choose);transported[choose]=part[choose];reports.append(proof)
            log(dict(event='interface_batch',alpha=alpha,last=min(first+32768,len(x)),total=len(x),**proof))
            if not proof['candidate_valid']:break
        trial['interface_batches']=reports
        if not all(r['candidate_valid'] for r in reports):trial['rejections'].append('finite map inverse')
        else:
            previous,v0=sample_centred(phi,local,h);following,v1=sample_centred(transported,actual,h)
            trial.update(particles_outside_before=int((previous>0).sum()),particles_outside_after=int((following>0).sum()),
                particle_scalar_stencil_failures=int((~v0|~v1).sum()),material_scalar_change_rms_cm=float(np.sqrt(np.mean((following-previous)**2))),
                material_scalar_change_max_cm=float(abs(following-previous).max()))
            if not (v0&v1).all():trial['rejections'].append('particle scalar support')
        log(dict(event='trial',**trial))
        if not trial['rejections']:accepted=True;break
    # Retain last field even when rejected; never silently expose it as accepted.
    np.savez_compressed(output/'field.npz',delta_cm=delta)
    if accepted:np.savez_compressed(output/'state.npz',positions_world_cm=updated,identities=identities,phi=transported,required_clearance_cm=required)
    report=dict(schema='raftsim.shared_density_contact_trial.v1',native_capture=str(capture),native_stages_sha256=sha(capture/'stages.json'),
        geometry_package=str(geometry),geometry_manifest_sha256=sha(geometry/'manifest.json'),registered_mesh_sha256=sha(dataset['mesh']),
        solid_kernel_sha256=item['sha256'],native_field_sources=inputs,source_files_sha256={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},
        sources_unchanged=all((Path(__file__).parent/n).read_bytes()==b for n,b in sources.items()),particles=len(positions),initial=metrics(before),
        direction=direction,trials=trials,accepted=accepted,native_positions=native_positions,active_set=active_set,field_sha256=sha(output/'field.npz'),
        state_sha256=sha(output/'state.npz') if accepted else None,
        original_exterior_extensions_physically_verified=False,global_injectivity_proven=False,momentum_modified=False,
        particle_volume_modified=False,physical_time_advanced=False,native_integrated=False,physical_visual_or_performance_acceptance=False,
        elapsed_seconds=time.perf_counter()-started)
    (output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('geometry',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--native-positions',action='store_true')
    p.add_argument('--max-sweeps',type=int,default=512);p.add_argument('--active-set',action='store_true');a=p.parse_args()
    r=run(a.capture,a.geometry,a.output,native_positions=a.native_positions,max_sweeps=a.max_sweeps,active_set=a.active_set)
    print(json.dumps({k:v for k,v in r.items() if k not in ('trials','native_field_sources')},indent=2,allow_nan=False))
    raise SystemExit(0 if r['accepted'] and r['sources_unchanged'] else 1)
