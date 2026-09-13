"""Measure tracked native surface and density candidate against exact river bed.

Does not substitute the density candidate for the native transported interface,
update either surface, or certify a rendered image. Keeps volume, marker coverage
and the absence of particle-correction/interface coupling as separate evidence.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from audit_liquid_native_handoff import read
from audit_liquid_native_interface import audit as audit_interface
from liquid_dataset import resolve
from liquid_volume_interface import sample_centred,deposit_volume
from liquid_interface_volume import integrate
from south_fork_registered_mesh import RegisteredMeshSampler


def audit(package,output,max_order=128):
    package=package.resolve();output=output.resolve();started=time.perf_counter()
    if output.exists():raise FileExistsError(output)
    if max_order not in (16,32,64,128):raise ValueError('Maximum quadrature order must be 16, 32, 64 or 128')
    source_names=['audit_liquid_particle_surface.py','liquid_interface_volume.py']
    algorithm_sources={n:(Path(__file__).parent/n).read_bytes() for n in source_names}
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    m=json.loads((package/'manifest.json').read_text());capture=Path(m['native_capture']);geometry=Path(m['geometry_package'])
    if sha(capture/'stages.json')!=m['native_stages_sha256'] or sha(geometry/'manifest.json')!=m['geometry_manifest_sha256'] or sha(package/'state.npz')!=m['state_sha256']:
        raise ValueError('Unchanged captured and corrected states required')
    native=json.loads((capture/'stages.json').read_text());dataset=resolve(native)
    proof=audit_interface(capture)
    g=json.loads((geometry/'manifest.json').read_text());regions=json.loads((dataset['regions']/'manifest.json').read_text())
    cells=np.array(g['cells']);h=np.array(g['spacing_cm'])/100;axes=np.array(g['world_axes']);lower=np.array(g['world_lower_cm'])/100
    if cells.tolist()!=regions['domain']['computational_cells'] or sha(dataset['mesh'])!=m['registered_mesh_sha256']:
        raise ValueError('Current physical frame/mesh required')
    physical=np.array(regions['domain']['physical_cells']);edges=regions['explicit_cell_edges']
    phi=np.zeros(tuple(cells[::-1]));written=np.zeros(phi.shape,bool);sources={}
    packets=native['native_transfer_packet'];pairs=native['native_interface_transport']['regions']
    if len(packets)!=12 or len(pairs)!=12 or sorted(r['region_id'] for r in packets)!=list(range(12)):
        raise ValueError('All twelve original owners required')
    for r,pair in zip(packets,pairs):
        if r['region_id']!=pair['region_id']:raise ValueError('Paired native surface owner differs')
        row,col=divmod(r['region_id'],4);width=edges[0][col+1]-edges[0][col];height=edges[1][row+1]-edges[1][row]
        offset=np.array([edges[0][col],physical[1]-edges[1][row+1]])
        if r['cells']!=[width+4,height+4,int(cells[2])]:raise ValueError('Native owner dimensions differ')
        lo=np.array([0 if offset[a]==0 else 2 for a in range(2)])
        hi=np.array([width+4 if offset[0]+width==physical[0] else width+2,height+4 if offset[1]+height==physical[1] else height+2])
        src=(slice(None),slice(lo[1],hi[1]),slice(lo[0],hi[0]))
        dest=(slice(None),slice(offset[1]+lo[1],offset[1]+hi[1]),slice(offset[0]+lo[0],offset[0]+hi[0]))
        path=(capture/pair['before']).resolve()
        if path.parent!=capture or written[dest].any():raise ValueError('Escaped source or double-counted halo')
        phi[dest]=np.fromfile(path,dtype='<f4').reshape(r['cells'][::-1])[src]/100
        sources[path.name]=sha(path);written[dest]=True
    if not written.all() or not np.isfinite(phi).all():raise ValueError('Complete finite tracked interface required')
    original=np.concatenate([read(capture,r,'positions',(r['particle_count'],4)).view('<f4')[:,:3].astype(float) for r in packets])
    identities=np.concatenate([read(capture,r,'identities',(r['particle_count'],4)) for r in packets])
    with np.load(package/'state.npz') as state:
        current=state['positions_world_cm']
        if not np.array_equal(identities,state['identities']) or current.shape!=original.shape or not np.isfinite(current).all():
            raise ValueError('All original finite particle identities required')
    volumes={float(np.float32(r['particle_volume_m3'])) for r in packets}
    if len(volumes)!=1:raise ValueError('One native conserved particle volume required')
    volume=volumes.pop();local_before=(original/100-lower)@axes.T;local_after=(current/100-lower)@axes.T
    initial,valid_before=sample_centred(phi,local_before,h);after,valid_after=sample_centred(phi,local_after,h)
    if not valid_before.all() or not valid_after.all():raise ValueError('Unsupported original/corrected particle scalar stencil')
    density=deposit_volume(local_after,cells,h,volume)/np.prod(h)
    density_phi=.5-density;density_sample,valid=sample_centred(density_phi,local_after,h)
    if not valid.all():raise ValueError('Incomplete density candidate')
    with np.load(dataset['mesh']) as mesh:sampler=RegisteredMeshSampler(mesh)
    def bed(p):
        world=p@axes[:2,:2]+lower[:2]
        return sampler.sample(world[:,0],-world[:,1])-lower[2]
    result=dict(schema='raftsim.liquid_particle_surface.v1',package=str(package),manifest_sha256=sha(package/'manifest.json'),
        native_stages_sha256=m['native_stages_sha256'],registered_mesh_sha256=m['registered_mesh_sha256'],
        interface_sources_sha256=sources,particles=len(current),nominal_particle_volume_m3=len(current)*volume,
        native_interface_transport_verified=proof,coordinate_contract='unchanged surveyed orthogonal parent frame',
        tracked_scalar_is_signed_distance=False,
        original_particles_outside_tracked_surface=int((initial>0).sum()),
        corrected_particles_outside_unmoved_tracked_surface=int((after>0).sum()),
        corrected_particles_outside_density_candidate=int((density_sample>0).sum()),
        newly_outside_unmoved_tracked_surface=int(((initial<=0)&(after>0)).sum()),
        newly_inside_unmoved_tracked_surface=int(((initial>0)&(after<=0)).sum()),
        material_scalar_change_rms_m=float(np.sqrt(np.mean((after-initial)**2))),
        material_scalar_change_max_m=float(abs(after-initial).max()),
        particle_correction_is_not_interface_transport=True,particle_or_terrain_modified=False,
        renderer_integrated=False,physical_visual_or_performance_acceptance=False)
    # Store compact transport validation, not its potentially long per-region history.
    result['native_interface_transport_verified']={k:v for k,v in proof.items() if isinstance(v,(bool,int,float,str))}
    print(json.dumps({k:v for k,v in result.items() if k not in ('interface_sources_sha256','native_interface_transport_verified')},indent=2),flush=True)
    for name,field in (('native_tracked_surface',phi),('corrected_density_candidate',density_phi)):
        orders=tuple(2**i for i in range(1,int(np.log2(max_order))+1))
        measurement=integrate(field,h,2*h[:2],(cells[:2]-2)*h[:2],bed,orders=orders)
        measurement['relative_difference_from_nominal_particle_volume']=(measurement['volume']-len(current)*volume)/(len(current)*volume)
        result[name]=measurement
        print(json.dumps(dict(event=name,**measurement,elapsed_seconds=time.perf_counter()-started)),flush=True)
    result['elapsed_seconds']=time.perf_counter()-started
    result['algorithm_sources_sha256']={n:hashlib.sha256(b).hexdigest() for n,b in algorithm_sources.items()}
    result['sources_unchanged']=all((Path(__file__).parent/n).read_bytes()==b for n,b in algorithm_sources.items())
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-order',type=int,default=128)
    a=p.parse_args();audit(a.package,a.output,a.max_order)
