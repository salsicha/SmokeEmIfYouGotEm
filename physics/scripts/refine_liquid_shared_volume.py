"""Refine an early native-coordinate density map with same-map surface volume.

Sequential linearized volume/contact solves keep one field for particles and
inverse scalar transport. Actual nonlinear volume, density, exact bed/survey,
native rounding and continuous no-fold bounds decide each step. Nominal volume
comes only from unchanged particle IDs/volumes, not an authored surface height.
This CPU reference does not advance physical time or integrate native momentum.
"""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path
import numpy as np
from audit_liquid_native_handoff import read
from audit_liquid_particle_routes import physical_owners
from liquid_dataset import resolve
from diagnose_liquid_projection_packet import load_field
from liquid_shared_density import shared_direction,constrained_field
from liquid_particle_density import objective
from liquid_compatible_advection import sample_compact
from liquid_correction_map import transport_interface
from liquid_map_injectivity import compact_map_bound
from liquid_surface_volume_gradient import integrate_gradient
from liquid_split_volume_gradient import integrate_gradient_split
from liquid_adaptive_terrain_volume import integrate_gradient_terrain
from liquid_bed_ray_intervals import bed_ray_intervals
from liquid_map_volume_gradient import map_volume_gradient
from liquid_interface_volume import integrate
from liquid_volume_interface import sample_centred
from liquid_swept_bed import swept_clearance
from south_fork_registered_mesh import RegisteredMeshSampler


def run(package,output,*,iterations=4,volume_tolerance=.01,split_quadrature=False,terrain_quadrature=False):
    package=package.resolve();output=output.resolve();started=time.perf_counter();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if output.exists():raise FileExistsError(output)
    if iterations<1 or not np.isfinite(volume_tolerance) or volume_tolerance<=0:raise ValueError('Positive refinement controls required')
    report=json.loads((package/'report.json').read_text());capture=Path(report['native_capture']);geometry=Path(report['geometry_package'])
    if not report['accepted'] or not report['sources_unchanged'] or not report['native_positions']:raise ValueError('Accepted native-coordinate shared-map seed required')
    for path,digest in ((capture/'stages.json',report['native_stages_sha256']),(geometry/'manifest.json',report['geometry_manifest_sha256']),
                        (package/'state.npz',report['state_sha256']),(package/'field.npz',report['field_sha256'])):
        if sha(path)!=digest:raise ValueError('Shared-map seed provenance changed')
    for name,digest in report['native_field_sources'].items():
        if sha(capture/name)!=digest:raise ValueError('Native scalar or boundary source changed')
    for name,digest in report['source_files_sha256'].items():
        if sha(package/'sources'/name)!=digest:raise ValueError('Seed algorithm snapshot changed')
    native=json.loads((capture/'stages.json').read_text());g=json.loads((geometry/'manifest.json').read_text());dataset=resolve(native)
    if sha(dataset['mesh'])!=report['registered_mesh_sha256']:raise ValueError('Captured bed changed')
    cells=np.array(g['cells']);h=np.array(g['spacing_cm']);axes=np.array(g['world_axes']);lower=np.array(g['world_lower_cm'])
    packets=native['native_transfer_packet'];pairs=native['native_interface_transport']['regions']
    positions=np.concatenate([read(capture,r,'positions',(r['particle_count'],4)).view('<f4')[:,:3].astype(float) for r in packets])
    identities=np.concatenate([read(capture,r,'identities',(r['particle_count'],4)) for r in packets])
    volumes=np.concatenate([np.full(r['particle_count'],float(np.float32(r['particle_volume_m3']))*1e6) for r in packets])
    target=float(volumes.sum()/1e6);local=(positions-lower)@axes.T;lo=np.array([2*h[0],2*h[1],0]);hi=(cells-[2,2,0])*h
    with np.load(package/'state.npz') as data:
        current_phi=data['phi'];current_positions=data['positions_world_cm'];required=data['required_clearance_cm']
        if not np.array_equal(data['identities'],identities):raise ValueError('Seed particle identities changed')
    with np.load(package/'field.npz') as data:current_delta=data['delta_cm']
    predicted=(positions+sample_compact(local,current_delta.transpose(2,1,0,3),h)@axes).astype('<f4').astype(float)
    if not np.array_equal(current_positions,predicted) or len(np.unique(positions,axis=0))!=len(positions):raise ValueError('Seed does not preserve shared native motion/unique input')
    with np.load(dataset['mesh']) as data:sampler=RegisteredMeshSampler(data)
    clearance=positions[:,2]-100*sampler.sample(positions[:,0]/100,-positions[:,1]/100)
    if (clearance<0).any() or not np.array_equal(required,np.minimum(clearance,2.)):raise ValueError('Original physical skin changed')
    survey=[json.loads((dataset['regions']/f'region-{i:03d}.json').read_text()) for i in range(12)]
    if (physical_owners(positions,survey)<0).any():raise ValueError('Original particle outside survey')
    item=g['files']['solid_kernel_fraction'];path=geometry/item['file']
    if sha(path)!=report['solid_kernel_sha256']:raise ValueError('Bed integral changed')
    solid=np.fromfile(path,dtype='<f4').reshape(cells[::-1]).astype(float)
    phi=np.zeros(cells[::-1]);phase=np.zeros(cells[::-1]);written=np.zeros(cells[::-1],bool)
    for r,pair,region in zip(packets,pairs,g['regions'],strict=True):
        if r['region_id']!=pair['region_id'] or r['region_id']!=region['region_id']:raise ValueError('Owner identity mismatch')
        ox,oy=region['offset_xy'];nx,ny,nz=r['cells'];x0=0 if ox==0 else 2;y0=0 if oy==0 else 2
        x1=nx if ox+nx==cells[0] else nx-2;y1=ny if oy+ny==cells[1] else ny-2
        dest=(slice(None),slice(oy+y0,oy+y1),slice(ox+x0,ox+x1));src=(slice(None),slice(y0,y1),slice(x0,x1))
        if written[dest].any():raise ValueError('Duplicate scalar ownership')
        phi[dest]=np.fromfile(capture/pair['before'],dtype='<f4').reshape(nz,ny,nx)[src]
        phase[dest]=load_field(capture,r,'projection_boundary',4)[src][...,3];written[dest]=True
    if not written.all():raise ValueError('Incomplete scalar ownership')
    selected=np.isin(phase,[0,2]);selected[:2]=False;selected[-2:]=False;selected[:,:2]=False;selected[:,-2:]=False;selected[:,:,:2]=False;selected[:,:,-2:]=False
    mobility=np.repeat(selected[...,None],3,axis=-1).astype(float)
    if np.any(current_delta[~selected]!=0) or not np.array_equal(phi[~selected],current_phi[~selected]):raise ValueError('Seed moves fixed boundary data')
    def bed(xy):
        world=xy@axes[:2,:2]+lower[:2]/100
        return sampler.sample(world[:,0],-world[:,1])-lower[2]/100
    def bed_segments(a,b):
        start=(a@axes[:2,:2]+lower[:2]/100)*[1,-1];end=(b@axes[:2,:2]+lower[:2]/100)*[1,-1]
        row,lo,hi,z0,z1=bed_ray_intervals(sampler,start,end)
        return row,lo,hi,z0-lower[2]/100,z1-lower[2]/100
    volume_args=(h/100,2*h[:2]/100,(cells[:2]-2)*h[:2]/100,bed)
    names=['refine_liquid_shared_volume.py','liquid_shared_density.py','liquid_field_equality.py','liquid_surface_volume_gradient.py','liquid_split_volume_gradient.py',
        'liquid_adaptive_terrain_volume.py','liquid_terrain_volume_gradient.py','liquid_bed_ray_intervals.py','liquid_bed_contour_intervals.py',
        'liquid_map_volume_gradient.py','liquid_map_injectivity.py','liquid_particle_density.py','liquid_affine_transfer.py',
        'liquid_correction_map.py','liquid_compatible_advection.py','liquid_interface_volume.py','liquid_volume_interface.py',
        'liquid_boundary_displacement.py','liquid_contact_psor.py','liquid_contact_active_set.py','liquid_swept_bed.py',
        'liquid_edge_visibility.py','liquid_particle_quantization.py','south_fork_registered_mesh.py']
    sources={n:(Path(__file__).parent/n).read_bytes() for n in names};output.mkdir(parents=True);(output/'sources').mkdir()
    for n,data in sources.items():(output/'sources'/n).write_bytes(data)
    def log(event):
        event['elapsed_seconds']=time.perf_counter()-started
        with (output/'progress.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event,allow_nan=False)+'\n')
        print(json.dumps(event,allow_nan=False),flush=True)
    def measure(field,label):
        diagnostics={}
        if terrain_quadrature:
            gradient,proof=integrate_gradient_terrain(field/100,*volume_args[:3],bed_segments,diagnostics=diagnostics,progress=log)
        elif split_quadrature:
            gradient,proof=integrate_gradient_split(field/100,*volume_args,diagnostics=diagnostics,progress=log)
        else:
            gradient,proof=integrate_gradient(field/100,*volume_args,orders=(2,4,8,16,32,64,128))
        artifact=output/f'{label}-quadrature.npz'
        np.savez_compressed(artifact,scalar_gradient=gradient,**diagnostics)
        proof['diagnostics_file']=artifact.name;proof['diagnostics_sha256']=sha(artifact)
        return gradient,proof
    initial=objective(local,cells,h,volumes,solid);desired,_=shared_direction(local,initial['gradient'],cells,h,mobility)
    history=[];failure=None;converged=False;current_volume=None
    log(dict(event='prepared',pid=os.getpid(),particles=len(positions),target_particle_volume_m3=target))
    for iteration in range(iterations):
        scalar_gradient,geometry_proof=measure(current_phi,f'iteration-{iteration:02d}')
        current_volume=geometry_proof['volume'];error=current_volume-target
        record=dict(iteration=iteration,before_volume=geometry_proof,before_volume_error_m3=error);history.append(record)
        log(dict(event='volume_gradient',iteration=iteration,volume_m3=current_volume,error_m3=error,
            unresolved_columns=geometry_proof['unresolved_columns'],zero_endpoint_rays=geometry_proof['zero_endpoint_rays_across_orders']))
        if geometry_proof['unresolved_columns']:
            failure='Unresolved geometric volume/gradient quadrature';break
        if abs(error)<=volume_tolerance:converged=True;break
        gradient,map_proof=map_volume_gradient(phi,current_delta,h,selected,scalar_gradient/100,mobility)
        rhs=target-current_volume+float(np.sum(gradient*current_delta));record['map_gradient']=map_proof
        log(dict(event='map_gradient',iteration=iteration,**map_proof))
        delta,contact=constrained_field(positions,local,desired,axes,h,lo,hi,sampler,required,mobility,
            native_positions=True,max_sweeps=128,active_set=True,field_equality=(gradient,rhs))
        record['contact']=contact
        log(dict(event='volume_contacts',iteration=iteration,converged=contact['converged'],constraints=contact['constraints'],geometric_iterations=len(contact['history'])))
        if not contact['converged']:failure='Linearized volume and exact shared contacts failed';break
        accepted=False;trials=[];record['trials']=trials
        for power in range(10):
            alpha=2.**-power;trial_delta=current_delta+alpha*(delta-current_delta)
            no_fold=compact_map_bound(trial_delta,h);trial=dict(alpha=alpha,no_fold=no_fold,rejections=[]);trials.append(trial)
            if not no_fold['continuous_map_globally_injective']:trial['rejections'].append('continuous fold bound');continue
            movement=sample_compact(local,trial_delta.transpose(2,1,0,3),h)
            candidate=(positions+movement@axes).astype('<f4').astype(float);actual=(candidate-lower)@axes.T
            final=objective(actual,cells,h,volumes,solid,derivatives=False)
            swept,_,_=swept_clearance(sampler,positions*[1,-1,1]/100,candidate*[1,-1,1]/100);margin=100*swept-required
            if (swept<0).any() or (margin < -1e-6).any():trial['rejections'].append('exact bed/skin')
            if np.any((actual<lo)|(actual>hi)) or (physical_owners(candidate,survey)<0).any():trial['rejections'].append('original exterior')
            if len(np.unique(candidate,axis=0))!=len(candidate):trial['rejections'].append('native coincidence')
            if final['energy']>=initial['energy']:trial['rejections'].append('no density improvement over original')
            trial.update(density_energy=final['energy'],minimum_required_margin_cm=float(margin.min()))
            if trial['rejections']:continue
            z,y,x=np.nonzero(selected);updated=phi.copy();inverse=[]
            for first in range(0,len(x),32768):
                choose=np.zeros(phi.shape,bool);choose[z[first:first+32768],y[first:first+32768],x[first:first+32768]]=True
                part,proof=transport_interface(phi,trial_delta,h,choose);updated[choose]=part[choose];inverse.append(proof)
                if not proof['candidate_valid']:break
            if not all(r['candidate_valid'] for r in inverse):trial['rejections'].append('same-map inverse');continue
            trial['inverse_max_residual_cm']=max(r['maximum_valid_inverse_residual'] for r in inverse)
            if split_quadrature or terrain_quadrature:
                _,volume=measure(updated,f'iteration-{iteration:02d}-trial-{power:02d}')
            else:
                volume=integrate(updated/100,*volume_args,orders=(2,4,8,16,32,64,128))
            trial['volume']=volume
            candidate_error=volume['volume']-target
            if volume['unresolved_columns'] or abs(candidate_error)>=(1-1e-4*alpha)*abs(error):trial['rejections'].append('nonlinear volume error')
            log(dict(event='nonlinear_trial',iteration=iteration,alpha=alpha,volume_error_m3=candidate_error,
                density_energy=final['energy'],rejections=trial['rejections']))
            if trial['rejections']:continue
            current_delta=trial_delta;current_phi=updated;current_positions=candidate;current_volume=volume['volume'];accepted=True
            record.update(after_volume=volume,after_volume_error_m3=candidate_error,
                after_density={k:v for k,v in final.items() if not isinstance(v,np.ndarray)})
            np.savez_compressed(output/f'accepted-{iteration+1:02d}.npz',delta_cm=current_delta,positions_world_cm=current_positions,phi=current_phi)
            if abs(candidate_error)<=volume_tolerance:converged=True
            break
        if not accepted:failure='Nonlinear shared volume/contact line search failed';break
        if converged:break
    if not converged and failure is None:failure='Volume iteration limit reached'
    final_local=(current_positions-lower)@axes.T;before_value,v0=sample_centred(phi,local,h);after_value,v1=sample_centred(current_phi,final_local,h)
    np.savez_compressed(output/'state.npz',delta_cm=current_delta,positions_world_cm=current_positions,identities=identities,phi=current_phi,required_clearance_cm=required)
    unchanged=all((Path(__file__).parent/n).read_bytes()==b for n,b in sources.items())
    result=dict(schema='raftsim.shared_volume_refinement.v1',seed_package=str(package),seed_report_sha256=sha(package/'report.json'),
        native_capture=str(capture),native_stages_sha256=report['native_stages_sha256'],geometry_package=str(geometry),
        geometry_manifest_sha256=report['geometry_manifest_sha256'],registered_mesh_sha256=report['registered_mesh_sha256'],
        particles=len(positions),nominal_particle_volume_m3=target,volume_tolerance_m3=volume_tolerance,
        split_quadrature=split_quadrature,terrain_quadrature=terrain_quadrature,
        final_volume_m3=current_volume,final_volume_error_m3=current_volume-target if current_volume is not None else None,
        iterations=history,converged=converged,failure=failure,state_sha256=sha(output/'state.npz'),
        particles_outside_before=int((before_value>0).sum()),particles_outside_after=int((after_value>0).sum()),
        unsupported_scalar_particles=int((~v0|~v1).sum()),sources_unchanged=unchanged,
        sources_sha256={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},
        geometric_quadrature_estimated_not_certified=True,native_integrated=False,momentum_modified=False,particle_volume_modified=False,
        physical_time_advanced=False,physical_visual_or_performance_acceptance=False,elapsed_seconds=time.perf_counter()-started)
    (output/'report.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--iterations',type=int,default=4);p.add_argument('--volume-tolerance',type=float,default=.01)
    method=p.add_mutually_exclusive_group();method.add_argument('--split-quadrature',action='store_true')
    method.add_argument('--terrain-quadrature',action='store_true');a=p.parse_args()
    r=run(a.package,a.output,iterations=a.iterations,volume_tolerance=a.volume_tolerance,
        split_quadrature=a.split_quadrature,terrain_quadrature=a.terrain_quadrature)
    print(json.dumps({k:v for k,v in r.items() if k!='iterations'},indent=2,allow_nan=False));raise SystemExit(0 if r['converged'] and r['sources_unchanged'] else 1)
