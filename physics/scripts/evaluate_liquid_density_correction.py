"""Evaluate a prepared correction on every captured particle without promotion.

Report geometry/source violations rather than deleting offending particles or
projecting them independently back onto the bed. This tests the correction's
actual boundary consistency, not only convergence of its pressure equation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_dataset import resolve
from audit_liquid_native_handoff import read
from liquid_compatible_advection import sample_compact
from liquid_affine_transfer import stencil
from liquid_density_projection import density_target
from south_fork_registered_mesh import RegisteredMeshSampler
from liquid_compatible_projection import divergence,constrain_velocity
from liquid_swept_bed import swept_clearance


def coincidence_counts(positions):
    """Identical markers cannot separate under a shared position-only field."""
    p=np.asarray(positions)
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all():raise ValueError('Finite XYZ positions required')
    unique,counts=np.unique(p,axis=0,return_counts=True)
    return dict(unique_positions=len(unique),exact_duplicate_groups=int((counts>1).sum()),
        particles_in_duplicate_groups=int(counts[counts>1].sum()),maximum_coincident_count=int(counts.max(initial=0)))


def correction_scale(meta,max_cells):
    """Do not rescale an already coupled geometric solution after its solve.

    Scaling a wall correction toward the original position can violate an
    off-grid plane. Failed prototypes remain evaluable, explicitly as failures.
    """
    if not np.isfinite(max_cells) or max_cells<0:raise ValueError('Finite nonnegative displacement required')
    if meta['status']=='geometric-reference':return 1.
    if meta['status']=='converged':return min(1,.5/max_cells) if max_cells else 1.
    raise ValueError('Unknown correction package status')


def evaluate(capture,package):
    capture=capture.resolve();package=package.resolve()
    source=json.loads((capture/'stages.json').read_text());meta=json.loads((package/'manifest.json').read_text())
    if meta['native_stages_sha256']!=hashlib.sha256((capture/'stages.json').read_bytes()).hexdigest():raise ValueError('Correction source changed')
    cells=np.asarray(meta['cells']);h=np.asarray(meta['spacing_cm']);axes=np.asarray(meta['world_axes']);lower=np.asarray(meta['world_lower_cm'])
    def field(key,channels=1):
        r=meta['files'][key];p=package/r['file']
        if p.resolve().parent!=package or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Changed correction input')
        shape=tuple(cells[::-1])+((channels,) if channels>1 else ())
        return np.fromfile(p,dtype='<f4').reshape(shape).astype(float)
    delta=field('displacement_cm',3);solid=field('solid_kernel_fraction');boundary=field('boundary',4)
    positions=np.concatenate([read(capture,r,'positions',(r['particle_count'],4)).view('<f4')[:,:3].astype(float) for r in source['native_transfer_packet']])
    if meta.get('input_state'):
        from liquid_correction_state import load_state
        state=meta['input_state']
        arrays,verified=load_state(state['directory'],state['input_package'],meta['native_stages_sha256'],meta,len(positions))
        if verified!=state:raise ValueError('Recorded starting-state provenance changed')
        positions=arrays['positions_world_cm']
    local=(positions-lower)@axes.T;q=local/h-.5;lo=np.floor(q).astype(int)-1
    valid=((lo>=0)&(lo+3<cells)).all(axis=1)
    moves=np.zeros_like(positions);moves[valid]=sample_compact(local[valid],delta.transpose(2,1,0,3),h)
    max_cells=float(np.linalg.norm(moves/h,axis=1).max(initial=0))
    # One common line-search step preserves the solved gradient field; this is
    # not per-particle clamping or a change to particle mass/momentum.
    alpha=correction_scale(meta,max_cells)
    moved_local=local+alpha*moves;moved=positions+(alpha*moves)@axes
    with np.load(resolve(source)['mesh']) as mesh:sampler=RegisteredMeshSampler(mesh)
    before=positions[:,2]/100-sampler.sample(positions[:,0]/100,-positions[:,1]/100)
    after=moved[:,2]/100-sampler.sample(moved[:,0]/100,-moved[:,1]/100)
    bounds_lo=np.array([2*h[0],2*h[1],0]);bounds_hi=(cells-np.array([2,2,0]))*h
    outside=((moved_local<bounds_lo)|(moved_local>bounds_hi)).any(axis=1)
    outside_before=((local<bounds_lo)|(local>bounds_hi)).any(axis=1)
    volumes={r['particle_volume_m3'] for r in source['native_transfer_packet']}
    if len(volumes)!=1:raise ValueError('Uniform captured particle volume required')
    volume=volumes.pop()
    def deposit(p):
        result=np.zeros(tuple(cells),float)
        for index,w,_,_ in stencil(p,cells,h):np.add.at(result,tuple(index.T),w*volume/np.prod(h/100))
        return result.transpose(2,1,0)
    initial=deposit(local);final=deposit(moved_local)
    _,before_stats=density_target(initial,solid,boundary);_,after_stats=density_target(final,solid,boundary)
    target=field('target')*meta.get('density_target_scale',1.)*alpha
    _,_,fluid=constrain_velocity(np.zeros_like(delta),boundary)
    equation_error=(divergence(alpha*delta,h)-target)[fluid]
    native_density=field('particle_density');difference=initial-native_density
    worst=np.unravel_index(np.argmax(abs(difference)),difference.shape)
    reconstruction=dict(maximum_error=float(abs(difference).max()),
        rms_error=float(np.sqrt(np.mean(difference**2))),
        fluid_rms_error=float(np.sqrt(np.mean(difference[fluid]**2))),
        worst_cell_zyx=[int(v) for v in worst],worst_cell_boundary_type=int(round(boundary[worst][3])),
        worst_cell_reconstructed_density=float(initial[worst]),worst_cell_native_density=float(native_density[worst]),
        native_grid_represented_volume_m3=float(native_density.sum()*np.prod(h/100)))
    reconstruction['reference_scope']='previous CPU corrected-state redeposit' if meta.get('input_state') else 'native P2G parent reconstruction'
    skin=meta.get('physical_bed_clearance_cm',0.)/100
    skin_margin=after-np.minimum(before,skin)
    sweep,sweep_time,sweep_face=swept_clearance(sampler,positions*np.array([1.,-1.,1.])/100,
        moved*np.array([1.,-1.,1.])/100)
    worst_sweep=int(np.argmin(sweep))
    return dict(particles=len(positions),unsupported_correction_stencils=int((~valid).sum()),
        input_status=meta['status'],input_geometric_density_converged=meta.get('geometric_density_converged'),
        serialized_field_density_equation_max_error=float(abs(equation_error).max(initial=0)),
        global_correction_scale=alpha,maximum_particle_displacement_cells=alpha*max_cells,
        before_density=before_stats,after_density=after_stats,
        coincidence_before=coincidence_counts(positions),coincidence_after=coincidence_counts(moved),
        minimum_bed_clearance_before_m=float(before.min()),minimum_bed_clearance_after_m=float(after.min()),
        particles_moved_below_exact_bed=int((after<0).sum()),particles_moved_outside_physical_exterior=int(outside.sum()),
        particles_outside_physical_exterior_before=int(outside_before.sum()),
        particles_newly_outside_physical_exterior=int((outside&~outside_before).sum()),
        particles_below_exact_bed_before=int((before<0).sum()),
        nominal_skin_m=skin,particles_below_nominal_skin_before=int((before<skin).sum()),
        particles_below_nominal_skin_after=int((after<skin).sum()),
        minimum_preserved_skin_margin_m=float(skin_margin.min()),
        particles_below_preserved_skin=int((skin_margin<0).sum()),
        minimum_swept_bed_clearance_m=float(sweep.min()),particles_with_swept_bed_penetration=int((sweep<0).sum()),
        minimum_swept_preserved_skin_margin_m=float((sweep-np.minimum(before,skin)).min()),
        worst_swept_particle=worst_sweep,worst_swept_fraction=float(sweep_time[worst_sweep]),
        worst_swept_face=int(sweep_face[worst_sweep]),sweep_scope='straight correction segment, not native advection',
        represented_volume_before_m3=float(initial.sum()*np.prod(h/100)),represented_volume_after_m3=float(final.sum()*np.prod(h/100)),
        parent_native_density_reconstruction_max_error=reconstruction['maximum_error'],
        parent_native_density_reconstruction=reconstruction,
        nominal_particle_volume_m3=volume,particle_mass_modified=False,momentum_modified=False,
        single_step_cpu_prediction_only=True,native_integrated=False,physical_visual_or_performance_acceptance=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('package',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    result=evaluate(a.capture,a.package);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))
