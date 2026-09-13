"""Bed-constrained whole-support density descent on captured native particles.

Position-only CPU reference. No grid phase masks density, no particle or mass
is deleted, and no native state or terrain is changed. Exact triangle paths
constrain each trial direction BEFORE a common nonlinear energy line search.
This is not physical-time integration, a renderer, or a real-time claim.
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
from liquid_dataset import resolve
from liquid_particle_density import objective,descent_direction
from liquid_particle_contacts import project_contacts
from liquid_particle_quantization import position_error_box,quantized_endpoint
from liquid_represented_retry import represented_retry
from liquid_swept_bed import swept_contact_planes,swept_clearance
from south_fork_registered_mesh import RegisteredMeshSampler


def constrained_direction(points,local,direction,axes,h,lo,hi,sampler,required,*,iterations=16,native_positions=False):
    """Project in cell metric with optional native representation error bounds.

    Solve separable contact QPs with three PARTICLE displacement unknowns
    per row, not the older shared compact-field pressure equality. The native
    coupling of this alternative is unimplemented and must not be implied.
    """
    base=direction/h;current=base.copy();indices=np.empty((0,3),int)
    weights=np.empty((0,3));bounds=np.empty(0);dual=np.empty(0);known=set();history=[]
    radius=float(np.linalg.norm(h));error_box=position_error_box(points,radius) if native_positions else np.zeros_like(points)
    for iteration in range(iterations):
        move=current*h
        tested_move=move
        if native_positions:
            stored,_=quantized_endpoint(points,move@axes,radius)
            tested_move=(stored-points)@axes.T
        selected,normals,limits,sweep,times,faces=swept_contact_planes(sampler,points,tested_move,axes,required)
        if native_positions:
            # n*(d+rounding) >= c for every error inside the derived box.
            # The coefficient already contains the crossing-time factor for
            # face contacts, or the time-independent ridge visibility normal.
            limits=limits+np.sum(np.abs(normals@axes)*error_box[selected],axis=1)
        rows=[];ws=[];cs=[]
        for row,k in enumerate(selected):
            key=(int(k),int(faces[row]),normals[row].tobytes(),float(limits[row]))
            if key not in known:
                known.add(key);rows.append(3*k+np.arange(3));ws.append(normals[row]*h);cs.append(limits[row])
        end=local+tested_move;outside=(end<lo)|(end>hi)
        for axis in range(3):
            for k in np.flatnonzero(outside[:,axis]):
                sign=1 if end[k,axis]<lo[axis] else -1
                key=(int(k),'outer',axis,sign)
                if key not in known:
                    known.add(key);n=np.zeros(3);n[axis]=sign
                    rows.append(3*k+np.arange(3));ws.append(n*h)
                    guard=float(np.abs(axes[axis])@error_box[k])
                    cs.append(float((lo[axis]-local[k,axis]) if sign==1 else (local[k,axis]-hi[axis]))+guard)
        history.append(dict(iteration=iteration,new_constraints=len(rows),outer_violations=int(outside.any(1).sum()),**sweep))
        if not len(selected) and not outside.any():return move,dict(converged=True,history=history,constraints=len(bounds),
            native_positions=native_positions,maximum_rounding_error_box_cm=float(error_box.max(initial=0)))
        if not rows:break
        indices=np.concatenate((indices,np.asarray(rows)));weights=np.concatenate((weights,np.asarray(ws)));bounds=np.r_[bounds,cs]
        # Restart from the same descent direction with all discovered planes.
        # No sequential pushout, stale warm residual or moved bed.
        current,projection=project_contacts(base,indices,weights,bounds)
        history[-1]['contact_projection']=projection
    return current*h,dict(converged=False,history=history,constraints=len(bounds))


def run(capture,geometry,output,iterations=4,native_positions=False,local_contact_retry=False):
    capture=capture.resolve();geometry=geometry.resolve();output=output.resolve();started=time.perf_counter()
    if output.exists():raise FileExistsError(output)
    if iterations<1:raise ValueError('Positive iteration count required')
    if local_contact_retry and not native_positions:raise ValueError('Local represented retry requires native positions')
    proof=audit_dense(capture)
    if not proof['dense_native_state_verified']:raise ValueError('Verified complete dense capture required')
    native=json.loads((capture/'stages.json').read_text());dataset=resolve(native)
    meta=json.loads((geometry/'manifest.json').read_text())
    cells=np.array(meta['cells']);h=np.array(meta['spacing_cm']);axes=np.array(meta['world_axes']);lower=np.array(meta['world_lower_cm'])
    mesh_hash=hashlib.sha256(dataset['mesh'].read_bytes()).hexdigest()
    regions=json.loads((dataset['regions']/'manifest.json').read_text());domain=regions['domain']
    survey_regions=[json.loads((dataset['regions']/f'region-{i:03d}.json').read_text()) for i in range(12)]
    first=native['native_transfer_packet'][0]
    original_lower=np.array(first['world_origin_cm'])-(np.array(first['extent_cm'])*[.5,.5,0])@axes
    original_lower-=np.r_[meta['regions'][0]['offset_xy'],0]*h@axes
    if (mesh_hash!=meta['registered_mesh_sha256'] or cells.tolist()!=domain['computational_cells'] or
            not np.array_equal(h,np.array(domain['cell_size_m'])*100) or
            not np.array_equal(axes,np.array([first['world_axis_x'],first['world_axis_y'],[0,0,1]])) or
            not np.allclose(lower,original_lower,atol=1e-10,rtol=0) or
            meta.get('unresolved_solid_kernel_columns',1)!=0 or meta['solid_quadrature_tolerance']>.001):
        raise ValueError('Unchanged grid/mesh and converged original bed quadrature required')
    item=meta['files']['solid_kernel_fraction'];path=(geometry/item['file']).resolve()
    if path.parent!=geometry or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Bed-kernel source changed')
    solid=np.fromfile(path,dtype='<f4').reshape(cells[::-1]).astype(float)
    positions=np.concatenate([read(capture,r,'positions',(r['particle_count'],4)).view('<f4')[:,:3].astype(float) for r in native['native_transfer_packet']])
    identities=np.concatenate([read(capture,r,'identities',(r['particle_count'],4)) for r in native['native_transfer_packet']])
    volumes=np.concatenate([np.full(r['particle_count'],float(np.float32(r['particle_volume_m3']))*1e6) for r in native['native_transfer_packet']])
    local=(positions-lower)@axes.T;lo=np.array([2*h[0],2*h[1],0]);hi=(cells-[2,2,0])*h
    if np.any((local<lo)|(local>hi)) or np.any(physical_owners(positions,survey_regions)<0):
        raise ValueError('Native particles outside unchanged correction/survey domain')
    with np.load(dataset['mesh']) as mesh:sampler=RegisteredMeshSampler(mesh)
    clearance=positions[:,2]-100*sampler.sample(positions[:,0]/100,-positions[:,1]/100)
    if (clearance<0).any():raise ValueError('Input penetrates physical bed')
    required=np.minimum(clearance,2.)
    source_names=['solve_liquid_particle_density.py','liquid_particle_density.py','liquid_affine_transfer.py',
                  'liquid_particle_contacts.py','liquid_swept_bed.py','liquid_edge_visibility.py','south_fork_registered_mesh.py',
                  'audit_liquid_particle_routes.py','liquid_particle_quantization.py','liquid_represented_retry.py']
    sources={name:(Path(__file__).parent/name).read_bytes() for name in source_names}
    output.mkdir(parents=True);(output/'sources').mkdir()
    for name,data in sources.items():(output/'sources'/name).write_bytes(data)
    def log(event):
        event.update(elapsed_seconds=time.perf_counter()-started)
        with (output/'progress.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event,allow_nan=False)+'\n')
        print(json.dumps(event,allow_nan=False),flush=True)
    history=[];failure=None;start_positions=positions.copy();initial=None;accepted_steps=[]
    for iteration in range(iterations):
        result=objective(local,cells,h,volumes,solid)
        metrics={k:v for k,v in result.items() if not isinstance(v,np.ndarray)}
        if initial is None:initial=metrics
        log(dict(event='density',iteration=iteration,pid=os.getpid(),**metrics))
        direction=descent_direction(result,h)
        move,contact=constrained_direction(positions,local,direction,axes,h,lo,hi,sampler,required,native_positions=native_positions)
        slope=float(np.sum(result['gradient']*move));record=dict(iteration=iteration,before=metrics,contact=contact,directional_derivative=slope)
        if not contact['converged'] or slope>=0:
            failure='No verified feasible density-descent direction';history.append(record);break
        accepted=False
        trials=[]
        for backtrack in range(16):
            alpha=2.**(-backtrack)
            if native_positions and backtrack:
                # Re-solve contacts for a smaller density step. Scaling an
                # already guarded move would also shrink its rounding margin.
                move,contact=constrained_direction(positions,local,alpha*direction,axes,h,lo,hi,sampler,required,native_positions=True)
                slope=float(np.sum(result['gradient']*move))
                if not contact['converged'] or slope>=0:
                    trials.append(dict(alpha=alpha,rejection='no feasible represented descent'));continue
            factor=1. if native_positions else alpha
            trial=local+factor*move
            candidate=objective(trial,cells,h,volumes,solid,derivatives=False)
            if candidate['energy']>result['energy']+1e-4*factor*slope:
                trials.append(dict(alpha=alpha,rejection='nonlinear energy'));continue
            updated=positions+(factor*move)@axes
            if native_positions:updated,_=quantized_endpoint(positions,(factor*move)@axes,float(np.linalg.norm(h)))
            retry=None
            if local_contact_retry:
                def project_subset(indices,subset_direction):
                    return constrained_direction(positions[indices],local[indices],subset_direction,axes,h,lo,hi,
                        sampler,required[indices],native_positions=True)
                move,updated,retry=represented_retry(positions,move,alpha*direction,axes,float(np.linalg.norm(h)),project_subset)
                if not retry['converged']:
                    trials.append(dict(alpha=alpha,rejection='local contact retry failed',local_contact_retry=retry));continue
                # Armijo uses the actual represented displacement, including
                # all locally re-solved QPs, not the former larger trial.
                slope=float(np.sum(result['gradient']*((updated-positions)@axes.T)))
                if slope>=0:
                    trials.append(dict(alpha=alpha,rejection='no represented descent',local_contact_retry=retry));continue
            # Include stored-world geometry in the same global line search.
            # Rounding at a closed outer plane cannot authorize an outside point.
            actual_local=(updated-lower)@axes.T
            final=objective(actual_local,cells,h,volumes,solid,derivatives=False)
            swept,_,_=swept_clearance(sampler,positions*[1,-1,1]/100,updated*[1,-1,1]/100)
            margin=100*swept-required
            outside=(actual_local<lo)|(actual_local>hi)
            survey_outside=physical_owners(updated,survey_regions)<0
            reasons=[]
            if (swept<0).any():reasons.append('physical bed penetration')
            if (margin < -1e-6).any():reasons.append('required skin')
            if outside.any():reasons.append('physical exterior')
            if survey_outside.any():reasons.append('original survey exterior')
            if final['energy']>result['energy']+1e-4*factor*slope:reasons.append('stored-world energy')
            if native_positions and len(np.unique(updated,axis=0))!=len(updated):reasons.append('coincident represented particles')
            trials.append(dict(alpha=alpha,rejections=reasons,outer_violations=int(outside.any(1).sum()),
                original_survey_outer_violations=int(survey_outside.sum()),
                maximum_exterior_distance_cm=float(np.maximum(lo-actual_local,actual_local-hi).max()),
                minimum_required_margin_cm=float(margin.min()),local_contact_retry=retry))
            if not reasons:accepted=True;break
        record.update(alpha=alpha,backtracks=backtrack,accepted=accepted,trials=trials,contact=contact,directional_derivative=slope)
        if not accepted:failure='Nonlinear energy/geometry line search failed';history.append(record);break
        record.update(after={k:v for k,v in final.items() if not isinstance(v,np.ndarray)},
            minimum_swept_bed_clearance_cm=float(100*swept.min()),minimum_required_margin_cm=float(margin.min()),
            raw_negative_required_margins=int((margin<0).sum()),maximum_displacement_cells=float(np.linalg.norm((updated-positions)@axes.T/h,axis=1).max()))
        positions=updated;local=actual_local
        step_file=output/f'step-{len(accepted_steps)+1:03d}.npz'
        np.savez_compressed(step_file,positions_world_cm=positions)
        accepted_steps.append(dict(file=step_file.name,sha256=hashlib.sha256(step_file.read_bytes()).hexdigest()))
        history.append(record);log(dict(event='accepted',**record))
    np.savez_compressed(output/'state.npz',positions_world_cm=positions,identities=identities,required_clearance_cm=required)
    final=objective((positions-lower)@axes.T,cells,h,volumes,solid,derivatives=False)
    unchanged=all((Path(__file__).parent/name).read_bytes()==data for name,data in sources.items())
    report=dict(schema='raftsim.liquid_particle_density_descent.v1',native_capture=str(capture),
        native_stages_sha256=hashlib.sha256((capture/'stages.json').read_bytes()).hexdigest(),
        geometry_package=str(geometry),geometry_manifest_sha256=hashlib.sha256((geometry/'manifest.json').read_bytes()).hexdigest(),
        registered_mesh_sha256=mesh_hash,solid_kernel_sha256=item['sha256'],quadrature_is_estimated_not_certified=True,
        state_sha256=hashlib.sha256((output/'state.npz').read_bytes()).hexdigest(),
        source_files_sha256={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},sources_unchanged=unchanged,
        particles=len(positions),iterations=history,failure=failure,initial=initial,accepted_steps=accepted_steps,
        final={k:v for k,v in final.items() if not isinstance(v,np.ndarray)},
        accepted_iterations=len(accepted_steps),
        moved_particles=int(np.any(positions!=start_positions,axis=1).sum()),stored_positions_dtype=str(positions.dtype),
        position_representation='float32-world-cm' if native_positions else 'float64-world-cm',
        local_contact_retry_enabled=local_contact_retry,
        momentum_modified=False,particle_volume_modified=False,physical_time_advanced=False,native_integrated=False,
        shared_field_or_interface_coupled=False,physical_visual_or_performance_acceptance=False,elapsed_seconds=time.perf_counter()-started)
    (output/'manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('geometry',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--iterations',type=int,default=4)
    p.add_argument('--native-positions',action='store_true');p.add_argument('--local-contact-retry',action='store_true');a=p.parse_args()
    r=run(a.capture,a.geometry,a.output,a.iterations,a.native_positions,a.local_contact_retry)
    print(json.dumps({k:v for k,v in r.items() if k!='iterations'},indent=2,allow_nan=False))
    raise SystemExit(1 if r['failure'] or not r['sources_unchanged'] else 0)
