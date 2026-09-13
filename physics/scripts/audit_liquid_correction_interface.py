"""Audit the actual whole-parent correction map before repeating density steps.

No game changes. Transport captured phi by the inverse of the very same finite
particle correction, retaining all native particles and exact source hashes.
Saved state is a CPU candidate only, not an evolved native fluid simulation.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from audit_liquid_native_handoff import read
from liquid_compatible_advection import sample_compact
from liquid_correction_map import transport_interface,reclassify_interface
from liquid_density_projection import density_target
from liquid_affine_transfer import stencil
from liquid_volume_interface import sample_centred


def run(capture,package,output):
    capture=capture.resolve();package=package.resolve();output=output.resolve()
    if output.exists():raise FileExistsError(output)
    started=time.perf_counter()
    meta=json.loads((package/'manifest.json').read_text());native=json.loads((capture/'stages.json').read_text())
    native_hash=hashlib.sha256((capture/'stages.json').read_bytes()).hexdigest()
    if meta['native_stages_sha256']!=native_hash or not meta.get('geometric_density_converged'):
        raise ValueError('A converged correction of the specified native capture is required')
    source_names=['audit_liquid_correction_interface.py','liquid_correction_map.py','liquid_compatible_advection.py',
        'liquid_volume_interface.py','liquid_affine_transfer.py','liquid_density_projection.py','liquid_correction_state.py']
    sources={name:(Path(__file__).parent/name).read_bytes() for name in source_names}
    cells=np.array(meta['cells']);h=np.array(meta['spacing_cm']);axes=np.array(meta['world_axes']);lower=np.array(meta['world_lower_cm'])
    def field(key,channels=1):
        r=meta['files'][key];path=(package/r['file']).resolve()
        if path.parent!=package or hashlib.sha256(path.read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Changed package field')
        return np.fromfile(path,dtype='<f4').reshape((*cells[::-1],channels) if channels>1 else cells[::-1]).astype(float)
    phi=field('phi');boundary=field('boundary',4);solid=field('solid_kernel_fraction');delta=field('displacement_cm',3)
    positions=np.concatenate([read(capture,r,'positions',(r['particle_count'],4)).view('<f4')[:,:3].astype(float) for r in native['native_transfer_packet']])
    if meta.get('input_state'):
        from liquid_correction_state import load_state
        state=meta['input_state']
        arrays,verified=load_state(state['directory'],state['input_package'],native_hash,meta,len(positions))
        if verified!=state:raise ValueError('Recorded starting-state provenance changed')
        positions=arrays['positions_world_cm']
    local=(positions-lower)@axes.T
    determinants=[];mapped=[]
    for first in range(0,len(local),65536):
        p=local[first:first+65536];move,jac=sample_compact(p,delta.transpose(2,1,0,3),h,derivatives=True)
        determinants.append(np.linalg.det(jac+np.eye(3)));mapped.append(p+move)
    determinant=np.concatenate(determinants);moved=np.concatenate(mapped)
    print(json.dumps(dict(event='particle_map',particles=len(local),minimum_determinant=float(determinant.min()),
        nonpositive_determinants=int((determinant<=0).sum()),elapsed_seconds=time.perf_counter()-started)),flush=True)
    selected=np.zeros(phi.shape,bool);selected[2:-2,2:-2,2:-2]=True;selected&=np.isin(boundary[...,3],[0,2])
    if np.any((boundary[...,3]==0)&~selected):raise ValueError('A pressure-fluid cell was excluded from correction transport')
    # Batch only the inverse queries: scalar interpolation uses one immutable
    # original phi, never the progressively written destination field.
    z,y,x=np.nonzero(selected);updated=phi.copy();batch_reports=[]
    for first in range(0,len(x),65536):
        choose=np.zeros(phi.shape,bool);choose[z[first:first+65536],y[first:first+65536],x[first:first+65536]]=True
        part,r=transport_interface(phi,delta,h,choose);updated[choose]=part[choose];batch_reports.append(r)
        print(json.dumps(dict(event='interface_batch',last=min(first+65536,len(x)),total=len(x),**r)),flush=True)
    inverse_valid=all(r['candidate_valid'] for r in batch_reports)
    report=dict(native_stages_sha256=native_hash,input_package=str(package),
        input_manifest_sha256=hashlib.sha256((package/'manifest.json').read_bytes()).hexdigest(),
        particles=len(local),particle_minimum_sampled_determinant=float(determinant.min()),
        particle_nonpositive_sampled_determinants=int((determinant<=0).sum()),
        interface_cells=int(selected.sum()),interface_inverse_valid=inverse_valid,interface_batches=batch_reports,
        original_phi_phase_inconsistencies=int((((boundary[...,3]==0)&(phi>=0))|((boundary[...,3]==2)&(phi<0))).sum()),
        original_owned_phi_phase_inconsistencies=int((selected&(((boundary[...,3]==0)&(phi>=0))|((boundary[...,3]==2)&(phi<0)))).sum()),
        global_injectivity_proven=False,physical_visual_or_performance_acceptance=False,native_integrated=False)
    if inverse_valid:
        new_boundary,phase=reclassify_interface(boundary,updated)
        # Caller-owned Z/XY layers must retain their original labels as well.
        new_boundary[~selected]=boundary[~selected]
        phase['air_to_fluid_cells']=int(((boundary[...,3]==2)&(new_boundary[...,3]==0)).sum())
        phase['fluid_to_air_cells']=int(((boundary[...,3]==0)&(new_boundary[...,3]==2)).sum())
        phase['pressure_factorization_reusable']=bool(np.array_equal(boundary,new_boundary))
        volumes={r['particle_volume_m3'] for r in native['native_transfer_packet']}
        if len(volumes)!=1:raise ValueError('Uniform native volume required')
        volume=volumes.pop();rho=np.zeros(tuple(cells))
        for index,w,_,_ in stencil(moved,cells,h):np.add.at(rho,tuple(index.T),w*volume/np.prod(h/100))
        rho=rho.transpose(2,1,0);_,density=density_target(rho,solid,new_boundary)
        before_phi,before_valid=sample_centred(phi,local,h);after_phi,after_valid=sample_centred(updated,moved,h)
        report.update(phase_changes=phase,density_with_updated_phase=density,
            represented_volume_m3=float(rho.sum()*np.prod(h/100)),
            particles_outside_phi_before=int((before_phi>0).sum()),particles_outside_phi_after=int((after_phi>0).sum()),
            particle_phi_stencil_failures=int((~before_valid|~after_valid).sum()),
            particle_phi_change_rms_cm=float(np.sqrt(np.mean((after_phi-before_phi)**2))),
            particle_phi_change_max_cm=float(abs(after_phi-before_phi).max()))
    changed=[name for name,data in sources.items() if (Path(__file__).parent/name).read_bytes()!=data]
    report.update(algorithm_sources={name:hashlib.sha256(data).hexdigest() for name,data in sources.items()},
        algorithm_sources_changed=changed,elapsed_seconds=time.perf_counter()-started,
        candidate_map_and_inverse_valid=bool(inverse_valid and not (determinant<=0).any() and not changed))
    output.mkdir(parents=True);(output/'sources').mkdir()
    for name,data in sources.items():(output/'sources'/name).write_bytes(data)
    # Retain failed evidence too, but never a usable state for a failed map.
    if report['candidate_map_and_inverse_valid']:
        path=output/'candidate_state.npz'
        np.savez_compressed(path,positions_world_cm=positions+(moved-local)@axes,
            positions_local_cm=moved,phi=updated,boundary=new_boundary,particle_density=rho)
        report['candidate_state_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        report['candidate_state_file']=path.name
    (output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return {k:v for k,v in report.items() if k!='interface_batches'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('package',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(run(a.capture,a.package,a.output),indent=2))
