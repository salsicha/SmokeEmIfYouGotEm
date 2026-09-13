"""Actual-river CPU prototype: shared-field density and geometric constraints.

Alternating Dykstra projections use the project's D M G density solve and sparse
off-grid wall rows. New contact planes are discovered against the exact mesh.
Convergence and every actual particle endpoint are reported, never assumed.
"""
import argparse
import hashlib
import json
import time
import os
from pathlib import Path
import numpy as np
from liquid_dataset import resolve
from audit_liquid_native_handoff import read
from liquid_compatible_advection import sample_compact
from liquid_compatible_projection import project,constrain_velocity,divergence
from liquid_boundary_displacement import compact_rows,project_rows,coupled_projection
from south_fork_registered_mesh import RegisteredMeshSampler
from liquid_swept_bed import swept_contact_planes


def contact_clearance_targets(before_cm,skin_cm,guard_cm):
    """Preserve native input clearance where it is already below nominal skin.

    Float-stored captured particles are not all exactly 2 cm above the double
    precision mesh. Never demand an impossible displacement from fixed nodes
    merely to repair that pre-existing input discrepancy. Do not allow such
    particles any closer to the bed, and report nominal-skin failures separately.
    """
    before=np.asarray(before_cm,float)
    if not np.isfinite(before).all() or (before<0).any() or skin_cm<0 or guard_cm<0:
        raise ValueError('Nonpenetrating input and nonnegative contact margins required')
    return np.minimum(before,skin_cm+guard_cm),np.minimum(before,skin_cm)


def run(capture,package,output,iterations=12,joint=False,direct=False,geometric_mobility=False,cached=False,relaxation=1.,active_set=False,swept_contact=False,state=None):
    started=time.perf_counter()
    if iterations<1:raise ValueError('At least one geometric iteration required')
    capture=capture.resolve();package=package.resolve();output=output.resolve()
    if output.exists():raise FileExistsError(output)
    source_names=['solve_liquid_geometric_density.py','liquid_boundary_schur.py',
        'liquid_boundary_displacement.py','liquid_compatible_projection.py','liquid_compatible_advection.py',
        'liquid_contact_system.py','liquid_contact_dual.py','liquid_contact_psor.py','liquid_contact_active_set.py',
        'south_fork_registered_mesh.py','liquid_swept_bed.py','liquid_edge_visibility.py',
        'liquid_correction_state.py','liquid_density_projection.py']
    source_bytes={name:(Path(__file__).parent/name).read_bytes() for name in source_names}
    meta=json.loads((package/'manifest.json').read_text());native=json.loads((capture/'stages.json').read_text())
    if meta['native_stages_sha256']!=hashlib.sha256((capture/'stages.json').read_bytes()).hexdigest():raise ValueError('Native source changed')
    cells=np.array(meta['cells']);h=np.array(meta['spacing_cm']);axes=np.array(meta['world_axes']);lower=np.array(meta['world_lower_cm'])
    def field(key,channels=1):
        item=meta['files'][key];p=(package/item['file']).resolve()
        if p.parent!=package or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Prepared input changed')
        return np.fromfile(p,dtype='<f4').reshape((*cells[::-1],channels) if channels>1 else cells[::-1]).astype(float)
    boundary=field('boundary',4);target=field('target');delta=field('displacement_cm',3)
    positions=np.concatenate([read(capture,r,'positions',(r['particle_count'],4)).view('<f4')[:,:3].astype(float) for r in native['native_transfer_packet']])
    state_reference=None;overrides={}
    if state is not None:
        if not (cached and geometric_mobility and swept_contact):
            raise ValueError('Repeated state requires cached exact-mobility swept-contact solve')
        from liquid_correction_state import load_state
        from liquid_density_projection import density_target
        arrays,state_reference=load_state(state,package,meta['native_stages_sha256'],meta,len(positions))
        positions=arrays['positions_world_cm'];boundary=arrays['boundary']
        target,stats=density_target(arrays['particle_density'],field('solid_kernel_fraction'),boundary)
        meta['statistics']=stats
        overrides=dict(boundary=boundary,phi=arrays['phi'],particle_density=arrays['particle_density'],target=target.copy())
    elif meta['status']!='converged':
        raise ValueError('A geometric package cannot be reused as an unscaled seed; supply its verified updated state')
    local=(positions-lower)@axes.T
    with np.load(resolve(native)['mesh']) as mesh:sampler=RegisteredMeshSampler(mesh)
    _,mobility,fluid=constrain_velocity(np.zeros_like(delta),boundary)
    if geometric_mobility:
        if not direct:raise ValueError('Exact-contact position mobility requires the coupled direct reference')
        from liquid_boundary_schur import geometric_position_mobility
        mobility=geometric_position_mobility(boundary)
    contact_system=None
    if cached:
        if not direct:raise ValueError('Cached system requires coupled direct reference')
        from liquid_contact_system import ContactSystem
        contact_system=ContactSystem(boundary,h,mobility,relaxation=relaxation,active_set=active_set)
    elif relaxation!=1. or active_set:raise ValueError('Contact relaxation/refinement requires cached coupled reference')
    if state is not None:
        delta,seed_report=contact_system.solve(target,np.empty((0,96),int),np.empty((0,96)),np.empty(0))
        if not seed_report['converged']:raise ValueError('Updated-phase density seed did not converge')
        meta['updated_phase_seed_solve']=seed_report
    movement=sample_compact(local,delta.transpose(2,1,0,3),h)
    maximum=float(np.linalg.norm(movement/h,axis=1).max());alpha=min(1,.5/maximum) if maximum else 1
    delta*=alpha;target*=alpha
    a_residual=np.zeros_like(delta);indices=np.empty((0,96),int);weights=np.empty((0,96));bounds=np.empty(0);dual=np.empty(0)
    known=set();history=[];failure=None
    lo=np.array([2*h[0],2*h[1],0]);hi=(cells-np.array([2,2,0]))*h
    # Match the existing native contact's physical 2 cm bed clearance. The
    # additional inward guard covers float32 FIELD serialization and the
    # contact solver's 1e-6 cm residual gate, not native world-position stores.
    # Neither the bed nor physical domain is moved or expanded.
    skin_cm=2.
    storage_guard_cm=float(1e-5+float(np.finfo(np.float32).eps)*float(abs(delta).max()))
    initial_clearance=positions[:,2]-100*sampler.sample(positions[:,0]/100,-positions[:,1]/100)
    required_clearance,accepted_clearance=contact_clearance_targets(initial_clearance,skin_cm,storage_guard_cm)
    output.mkdir(parents=True);(output/'sources').mkdir()
    for name,data in source_bytes.items():(output/'sources'/name).write_bytes(data)
    def record_progress(event):
        event=dict(event,elapsed_seconds=time.perf_counter()-started)
        with (output/'progress.jsonl').open('a',encoding='utf-8') as log:log.write(json.dumps(event,allow_nan=False)+'\n')
        print(json.dumps(event),flush=True)
    record_progress(dict(event='prepared',pid=os.getpid(),particles=len(positions),cached_contact_system=cached))
    for iteration in range(iterations):
        if iteration and not joint:
            candidate=delta+a_residual
            delta,_,p=project(candidate,boundary,h,dt=1,max_iterations=180,tolerance=1e-7,
                boundary_pressure=np.zeros_like(target),target_divergence=target)
            a_residual=candidate-delta
            if not p['converged']:failure='Density equality projection failed to converge';break
        movement=sample_compact(local,delta.transpose(2,1,0,3),h)
        predicted=positions+movement@axes
        bed,n=sampler.sample(predicted[:,0]/100,-predicted[:,1]/100,with_normals=True)
        n[:,1]*=-1
        clearance=predicted[:,2]-100*bed
        points=[];normals=[];rhs=[]
        if swept_contact:
            selected,normal_rows,lower_rows,sweep_audit,times,faces=swept_contact_planes(sampler,positions,movement,axes,required_clearance)
            for j,k in enumerate(selected):
                key=(int(k),'swept',int(faces[j]),round(float(times[j]),12),round(float(lower_rows[j]),7))
                if key not in known:
                    known.add(key);points.append(local[k]);normals.append(normal_rows[j]);rhs.append(lower_rows[j])
            record_progress(dict(event='swept_discovery',iteration=iteration,**sweep_audit))
        else:
            selected=np.flatnonzero(clearance<required_clearance)
            for k in selected:
                plane=predicted[k].copy();plane[2]=100*bed[k]+required_clearance[k]
                normal=n[k]@axes.T;c=float((plane-positions[k])@n[k])
                key=(int(k),*np.round(normal,8),round(c,7))
                if key not in known:known.add(key);points.append(local[k]);normals.append(normal);rhs.append(c)
        endpoint=local+movement
        for axis in range(3):
            for sign,edge in ((1,lo[axis]),(-1,hi[axis])):
                edge+=sign*storage_guard_cm
                selected=np.flatnonzero(sign*(endpoint[:,axis]-edge)<0)
                for k in selected:
                    normal=np.zeros(3);normal[axis]=sign;c=sign*(edge-local[k,axis]);key=(int(k),'outer',axis,sign)
                    if key not in known:known.add(key);points.append(local[k]);normals.append(normal);rhs.append(c)
        if points:
            ii,ww=compact_rows(np.array(points),np.array(normals),cells,h,mobility)
            indices=np.r_[indices,ii];weights=np.r_[weights,ww];bounds=np.r_[bounds,rhs];dual=np.r_[dual,np.zeros(len(points))]
        record_progress(dict(event='constraints',iteration=iteration,contact_rows=len(bounds),new_rows=len(points)))
        # Retain the actual operator input even when the bounded solve fails.
        # This permits direct replay without repeating earlier geometry steps.
        np.savez_compressed(output/f'contact_rows_{iteration:03d}.npz',indices=indices,weights=weights,lower=bounds)
        try:
            if joint:
                if direct:
                    if contact_system is not None:delta,joint_report=contact_system.solve(target,indices,weights,bounds)
                    else:
                        from liquid_boundary_schur import solve as direct_solve
                        delta,joint_report=direct_solve(target,boundary,h,indices,weights,bounds,mobility=mobility)
                else:delta,joint_report=coupled_projection(target,boundary,h,indices,weights,bounds)
                if contact_system is not None and contact_system._dual is not None:
                    np.save(output/f'contact_dual_{iteration:03d}.npy',contact_system._dual)
                record_progress(dict(event='joint_projection',iteration=iteration,joint_projection=joint_report))
                violation=float(np.maximum(bounds-np.sum(delta.ravel()[indices]*weights,axis=1),0).max(initial=0))
                if not joint_report['converged']:failure='Joint density/contact Schur solve did not converge';break
            else:delta,dual,violation=project_rows(delta,indices,weights,bounds,dual,sweeps=12)
        except (ValueError,RuntimeError) as error:
            failure=str(error);record_progress(dict(event='failure',failure=failure));break
        movement=sample_compact(local,delta.transpose(2,1,0,3),h);predicted=positions+movement@axes
        bed=sampler.sample(predicted[:,0]/100,-predicted[:,1]/100);clearance=predicted[:,2]-100*bed
        endpoint=local+movement;outside=((endpoint<lo)|(endpoint>hi)).any(axis=1)
        residual=(divergence(delta,h)-target)[fluid]
        record=dict(iteration=iteration,active_geometry_rows=len(bounds),new_rows=len(points),
            maximum_density_equation_error=float(abs(residual).max(initial=0)),rms_density_equation_error=float(np.sqrt(np.mean(residual**2))),
            minimum_exact_bed_clearance_cm=float(clearance.min()),particles_below_bed=int((clearance<0).sum()),
            minimum_preserved_skin_margin_cm=float((clearance-accepted_clearance).min()),
            particles_below_nominal_skin=int((clearance<skin_cm).sum()),
            particles_outside_exterior=int(outside.sum()),maximum_linear_boundary_violation_cm=violation,
            maximum_displacement_cells=float(np.linalg.norm(movement/h,axis=1).max()))
        if swept_contact:
            _,_,_,sweep_audit,_,_=swept_contact_planes(sampler,positions,movement,axes,accepted_clearance)
            record.update(sweep_audit)
        history.append(record);record_progress(dict(record,event='geometry'))
        swept_ok=not swept_contact or (record['particles_with_swept_bed_penetration']==0 and record['minimum_swept_required_margin_cm']>=-1e-6)
        if record['maximum_density_equation_error']<=1e-5 and record['minimum_preserved_skin_margin_cm']>=-1e-6 and not outside.any() and swept_ok:break
    changed_sources=[name for name,data in source_bytes.items() if (Path(__file__).parent/name).read_bytes()!=data]
    if changed_sources:failure='Algorithm source changed during run: '+','.join(changed_sources)
    path=output/'displacement_cm.bin';np.asarray(delta,dtype='<f4').tofile(path)
    # Keep the same package interface for the independent all-particle evaluator.
    files={}
    for key,item in meta['files'].items():
        # The density-only potential is not the coupled contact solution.
        if key in ('displacement_cm','potential_cm2') or key in overrides:continue
        data=(package/item['file']).read_bytes();(output/item['file']).write_bytes(data);files[key]=item
    for key,array in overrides.items():
        name=key+'.bin';np.asarray(array,dtype='<f4').tofile(output/name)
        files[key]=dict(file=name,sha256=hashlib.sha256((output/name).read_bytes()).hexdigest())
    files['displacement_cm']=dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    meta.update(files=files,geometric_constraint_history=history,geometric_constraint_failure=failure,
        input_package=str(package),elapsed_seconds=time.perf_counter()-started,
        input_state=state_reference,iteration_scope='one density correction; no physical time advanced',
        physical_bed_clearance_cm=skin_cm,field_serialization_inward_guard_cm=storage_guard_cm,
        input_particles_below_nominal_skin=int((initial_clearance<skin_cm).sum()),
        input_minimum_bed_clearance_cm=float(initial_clearance.min()),
        contact_skin_policy='preserve input clearance if already below nominal; never repair fixed input by moving the bed',
        native_world_position_storage_verified=False,
        density_target_scale=alpha,status='geometric-reference',joint_projection=joint,direct_contact_schur=direct,
        cached_contact_system=cached,contact_relaxation=relaxation,source_snapshot_at_start=True,
        active_set_refinement=active_set,swept_contact_constraints=swept_contact,
        geometric_position_mobility=geometric_mobility,
        geometric_density_converged=bool(history and not failure and history[-1]['maximum_density_equation_error']<=1e-5 and
            history[-1]['minimum_preserved_skin_margin_cm']>=-1e-6 and history[-1]['particles_outside_exterior']==0 and
            (not swept_contact or (history[-1]['particles_with_swept_bed_penetration']==0 and history[-1]['minimum_swept_required_margin_cm']>=-1e-6))),
        native_integrated=False,physical_visual_or_performance_acceptance=False)
    meta['algorithm_sources']={name:hashlib.sha256(data).hexdigest() for name,data in source_bytes.items()}
    (output/'manifest.json').write_text(json.dumps(meta,indent=2,allow_nan=False)+'\n')
    return dict(failure=failure,iterations=len(history),converged=meta['geometric_density_converged'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('package',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--iterations',type=int,default=12);p.add_argument('--joint',action='store_true')
    p.add_argument('--direct',action='store_true');p.add_argument('--geometric-mobility',action='store_true')
    p.add_argument('--cached',action='store_true');p.add_argument('--relaxation',type=float,default=1.)
    p.add_argument('--active-set',action='store_true');p.add_argument('--swept-contact',action='store_true')
    p.add_argument('--state',type=Path,help='Verified updated-particle/interface package from audit_liquid_correction_interface');a=p.parse_args()
    if a.direct or a.cached:
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tmp/south-fork-density-numerics'))
    print(json.dumps(run(a.capture,a.package,a.output,a.iterations,a.joint or a.direct or a.cached,a.direct or a.cached,a.geometric_mobility,a.cached,a.relaxation,a.active_set,a.swept_contact,a.state),indent=2))
