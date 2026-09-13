"""Reopen a saved shared-map trial and independently check its persisted state.

Checks all IDs, native coordinate rounding, exact swept terrain/survey paths,
density, a global continuous-map no-fold bound, inverse scalar replay and actual
above-bed geometric surface volume. Numerical checks are not scene acceptance.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from audit_liquid_native_handoff import read
from audit_liquid_particle_routes import physical_owners
from liquid_dataset import resolve
from liquid_compatible_advection import sample_compact
from liquid_particle_density import objective
from liquid_swept_bed import swept_clearance
from liquid_correction_map import inverse_map
from liquid_map_injectivity import compact_map_bound
from liquid_volume_interface import sample_centred
from liquid_interface_volume import integrate
from diagnose_liquid_projection_packet import load_field
from south_fork_registered_mesh import RegisteredMeshSampler


def audit(package,output):
    package=package.resolve();output=output.resolve();started=time.perf_counter()
    if output.exists():raise FileExistsError(output)
    names=['audit_liquid_shared_density.py','liquid_map_injectivity.py','liquid_interface_volume.py',
        'liquid_correction_map.py','liquid_compatible_advection.py','liquid_particle_density.py','liquid_affine_transfer.py',
        'liquid_volume_interface.py','liquid_swept_bed.py','liquid_edge_visibility.py','south_fork_registered_mesh.py']
    source_bytes={n:(Path(__file__).parent/n).read_bytes() for n in names}
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    m=json.loads((package/'report.json').read_text());capture=Path(m['native_capture']);geometry=Path(m['geometry_package'])
    if not m['accepted'] or not m['sources_unchanged'] or not m['native_positions']:raise ValueError('Accepted native-coordinate CPU candidate required')
    for p,digest in ((capture/'stages.json',m['native_stages_sha256']),(geometry/'manifest.json',m['geometry_manifest_sha256']),
                     (package/'field.npz',m['field_sha256']),(package/'state.npz',m['state_sha256'])):
        if sha(p)!=digest:raise ValueError('Captured or corrected artifact changed')
    for name,digest in m['source_files_sha256'].items():
        if sha(package/'sources'/name)!=digest:raise ValueError('Algorithm snapshot changed')
    for name,digest in m['native_field_sources'].items():
        if sha(capture/name)!=digest:raise ValueError('Native scalar or phase changed')
    native=json.loads((capture/'stages.json').read_text());g=json.loads((geometry/'manifest.json').read_text());dataset=resolve(native)
    if sha(dataset['mesh'])!=m['registered_mesh_sha256']:raise ValueError('Captured bed changed')
    h=np.array(g['spacing_cm']);cells=np.array(g['cells']);axes=np.array(g['world_axes']);lower=np.array(g['world_lower_cm'])
    r=native['native_transfer_packet'];pairs=native['native_interface_transport']['regions']
    p=np.concatenate([read(capture,a,'positions',(a['particle_count'],4)).view('<f4')[:,:3].astype(float) for a in r])
    ids=np.concatenate([read(capture,a,'identities',(a['particle_count'],4)) for a in r])
    volumes=np.concatenate([np.full(a['particle_count'],float(np.float32(a['particle_volume_m3']))*1e6) for a in r])
    with np.load(package/'state.npz') as data:
        q=data['positions_world_cm'];new_phi=data['phi'];required=data['required_clearance_cm']
        if not np.array_equal(ids,data['identities']):raise ValueError('Particle identities changed')
    with np.load(package/'field.npz') as data:delta=data['delta_cm']
    local=(p-lower)@axes.T;actual=(q-lower)@axes.T
    prediction=(p+sample_compact(local,delta.transpose(2,1,0,3),h)@axes).astype('<f4').astype(float)
    if not np.array_equal(prediction,q):raise ValueError('Persisted native endpoints do not follow shared map')
    if len(np.unique(q,axis=0))!=len(q):raise ValueError('Persisted particles coincide')
    with np.load(dataset['mesh']) as data:sampler=RegisteredMeshSampler(data)
    original_clearance=p[:,2]-100*sampler.sample(p[:,0]/100,-p[:,1]/100)
    if not np.array_equal(required,np.minimum(original_clearance,2.)):raise ValueError('Required skin was changed')
    swept,_,_=swept_clearance(sampler,p*[1,-1,1]/100,q*[1,-1,1]/100);margin=100*swept-required
    survey=[json.loads((dataset['regions']/f'region-{i:03d}.json').read_text()) for i in range(12)]
    if (swept<0).any() or (margin < -1e-6).any() or (physical_owners(q,survey)<0).any():raise ValueError('Saved map violates exact bed or original survey')
    bound=compact_map_bound(delta,h)
    if not bound['continuous_map_globally_injective']:raise ValueError('No global continuous-map no-fold certificate')
    item=g['files']['solid_kernel_fraction'];path=geometry/item['file']
    if sha(path)!=m['solid_kernel_sha256']:raise ValueError('Bed-kernel fractions changed')
    solid=np.fromfile(path,dtype='<f4').reshape(cells[::-1]).astype(float)
    before=objective(local,cells,h,volumes,solid,derivatives=False);after=objective(actual,cells,h,volumes,solid,derivatives=False)
    if after['energy']>=before['energy']:raise ValueError('No all-node density improvement')
    phi=np.zeros(cells[::-1]);phase=np.zeros(cells[::-1]);written=np.zeros(cells[::-1],bool)
    for a,pair,region in zip(r,pairs,g['regions'],strict=True):
        if a['region_id']!=pair['region_id'] or a['region_id']!=region['region_id']:raise ValueError('Mismatched owner')
        ox,oy=region['offset_xy'];nx,ny,nz=a['cells']
        x0=0 if ox==0 else 2;y0=0 if oy==0 else 2
        x1=nx if ox+nx==cells[0] else nx-2;y1=ny if oy+ny==cells[1] else ny-2
        dest=(slice(None),slice(oy+y0,oy+y1),slice(ox+x0,ox+x1));src=(slice(None),slice(y0,y1),slice(x0,x1))
        if written[dest].any():raise ValueError('Double counted owner region')
        phi[dest]=np.fromfile(capture/pair['before'],dtype='<f4').reshape(nz,ny,nx)[src]
        phase[dest]=load_field(capture,a,'projection_boundary',4)[src][...,3];written[dest]=True
    if not written.all():raise ValueError('Incomplete scalar field')
    selected=np.isin(phase,[0,2]);selected[:2]=False;selected[-2:]=False
    selected[:,:2]=False;selected[:,-2:]=False;selected[:,:,:2]=False;selected[:,:,-2:]=False
    if np.any(delta[~selected]!=0) or not np.array_equal(new_phi[~selected],phi[~selected]):raise ValueError('Fixed solid/exterior/Z values changed')
    z,y,x=np.nonzero(selected);max_error=0.;max_residual=0.;min_det=np.inf
    for first in range(0,len(x),32768):
        last=min(first+32768,len(x));query=(np.column_stack((x[first:last],y[first:last],z[first:last]))+.5)*h
        departures,valid,proof=inverse_map(query,delta,h)
        if not valid.all():raise ValueError('Failed persisted inverse map')
        expected,complete=sample_centred(phi,departures,h)
        if not complete.all():raise ValueError('Missing scalar support')
        max_error=max(max_error,float(abs(expected-new_phi[z[first:last],y[first:last],x[first:last]]).max(initial=0)))
        max_residual=max(max_residual,proof['maximum_valid_inverse_residual']);min_det=min(min_det,proof['minimum_sampled_determinant'])
    if max_error!=0:raise ValueError('Saved scalar differs from same-map inverse replay')
    old_value,v0=sample_centred(phi,local,h);new_value,v1=sample_centred(new_phi,actual,h)
    if not (v0&v1).all():raise ValueError('Unsupported particle scalar samples')
    print(json.dumps(dict(event='saved_map_verified',particles=len(p),inverse_samples=len(x),elapsed_seconds=time.perf_counter()-started)),flush=True)
    def bed(xy):
        world=xy@axes[:2,:2]+lower[:2]/100
        return sampler.sample(world[:,0],-world[:,1])-lower[2]/100
    geometric=[]
    for label,scalar in (('before',phi),('after',new_phi)):
        volume=integrate(scalar/100,h/100,2*h[:2]/100,(cells[:2]-2)*h[:2]/100,bed,orders=(2,4,8,16,32,64,128))
        geometric.append(volume)
        print(json.dumps(dict(event='surface_volume',state=label,volume_m3=volume['volume'],unresolved_columns=volume['unresolved_columns'],elapsed_seconds=time.perf_counter()-started)),flush=True)
    unchanged=all((Path(__file__).parent/n).read_bytes()==data for n,data in source_bytes.items())
    result=dict(schema='raftsim.saved_shared_map_audit.v1',candidate_report_sha256=sha(package/'report.json'),native_stages_sha256=m['native_stages_sha256'],
        particles=len(p),all_ids_preserved=True,native_float32_endpoints_exact=True,coincident_positions=0,
        minimum_swept_clearance_cm=float(100*swept.min()),minimum_required_margin_cm=float(margin.min()),
        original_survey_outside=0,continuous_map_certificate=bound,inverse_samples=len(x),inverse_scalar_replay_max_error_cm=max_error,
        inverse_residual_max_cm=max_residual,minimum_sampled_inverse_determinant=min_det,
        before_density={k:v for k,v in before.items() if not isinstance(v,np.ndarray)},after_density={k:v for k,v in after.items() if not isinstance(v,np.ndarray)},
        particles_outside_before=int((old_value>0).sum()),particles_outside_after=int((new_value>0).sum()),
        nominal_particle_volume_m3=float(volumes.sum()/1e6),geometric_volume_before=geometric[0],geometric_volume_after=geometric[1],
        geometric_volume_change_m3=geometric[1]['volume']-geometric[0]['volume'],
        sources_sha256={n:hashlib.sha256(data).hexdigest() for n,data in source_bytes.items()},sources_unchanged=unchanged,
        saved_map_checks_passed=unchanged,
        physical_visual_or_performance_acceptance=False,native_integrated=False,elapsed_seconds=time.perf_counter()-started)
    snapshots=output.with_suffix('.sources');snapshots.mkdir()
    for n,data in source_bytes.items():(snapshots/n).write_bytes(data)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=audit(a.package,a.output);print(json.dumps({k:v for k,v in r.items() if not k.startswith('geometric_volume')},indent=2,allow_nan=False))
    raise SystemExit(0 if r['saved_map_checks_passed'] else 1)
