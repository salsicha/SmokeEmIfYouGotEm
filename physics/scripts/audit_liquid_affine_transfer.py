"""Compare persisted GPU APIC C matrices with the captured projected grid.

This checks the isolated, upright collocated fixture, not river accuracy or
conservation across contact and open boundaries. No fitted gradient scale.
Legacy gradient-named result keys remain for compatibility; quadratic C is a
weighted moment, explicitly identified in affine_state_semantics.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from analyze_liquid_grid_readback import load_fields
from liquid_affine_transfer import to_particles


def shader_text(data):
    return data.decode('utf-16' if data.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')


def compare(rows, velocity_zyx, boundary_zyx, extents,quadratic=False):
    rows=np.asarray(rows,float);extents=np.asarray(extents,float)
    if rows.ndim!=2 or rows.shape[1] not in (13,16) or not len(rows) or not np.isfinite(rows).all():
        raise ValueError('Finite GPU affine rows with 13 or 16 columns required')
    grid=np.asarray(velocity_zyx,float).transpose(2,1,0,3)
    shape=np.array(grid.shape[:3]);h=extents/shape
    points=rows[:,1:4]+np.array([extents[0]/2,extents[1]/2,0])
    grid_position=points/h
    if rows.shape[1]==16:
        # Replay the exact recorded GPU unit coordinate and float32 cell
        # indexing. Ideal rigid inversion is not equivalent to UE's stored
        # scaled-matrix inverse near a boundary. Grid velocities remain an
        # independent readback, not an expected value stored by the shader.
        grid_position=rows[:,13:16].astype(np.float32)*shape.astype(np.float32)
        q=grid_position-np.float32(.5)
        points=(q.astype(float)+.5)*h
    low=np.floor(points/h-.5-(.5 if quadratic else 0)).astype(int)
    parent=np.clip(grid_position.astype(int),0,shape-1)
    solid=np.rint(boundary_zyx[parent[:,2],parent[:,1],parent[:,0],3])==1
    support=(low>=0).all(axis=1)&(low+(2 if quadratic else 1)<shape).all(axis=1)&~solid
    expected=np.zeros((len(rows),3,3))
    if support.any():
        _,expected[support]=to_particles(points[support],grid,h,quadratic=quadratic)
    actual=rows[:,4:13].reshape(-1,3,3).transpose(0,2,1)
    error=np.max(np.abs(actual-expected),axis=(1,2))
    # Shader position/world-matrix operations are float32; the replay evaluates
    # derivatives in float64 on serialized positions and half-float grid data.
    tolerance=0.001
    return dict(particles=len(rows),supported_particles=int(support.sum()),
                nonzero_gradient_particles=int((np.max(abs(actual),axis=(1,2))>1e-5).sum()),
                gradient_max_error_per_s=float(error.max()),
                gradient_error_quantiles_per_s=np.quantile(error,[.5,.9,.99,1]).tolist(),
                unsupported_gradient_max_per_s=float(abs(actual[~support]).max(initial=0)),
                gradient_tolerance_per_s=tolerance,
                gradient_parity=bool(support.any() and error.max()<=tolerance),
                actual_gpu_sampling_coordinates=rows.shape[1]==16,
                spacing_cm=h.tolist(),
                affine_state_semantics='quadratic APIC B D^-1 moment, not point derivative' if quadratic else 'trilinear velocity derivative')


def audit(directory):
    directory=Path(directory)
    capture=json.loads((directory/'capture.json').read_text())
    if not capture.get('complete') or capture.get('error') or not capture.get('affine_transfer_requested'):
        raise ValueError('Completed affine capture required')
    steps=capture['simulation_steps'];stem=f'terrain_{steps:04d}'
    particle_file=directory/(stem+'_particles.json')
    data=json.loads(particle_file.read_text())
    emitters=[e for e in data['emitters'] if e['emitter']=='Grid3D_FLIP_FluidControl_Emitter']
    if len(emitters)!=1:
        raise ValueError('Exactly one primary emitter required')
    primary=emitters[0];rows=primary.get('affine_rows',[])
    if len(rows)!=primary['position_count']:
        raise ValueError('Affine state must cover every actual primary particle')
    fields=load_fields(directory/(stem+'_grids'))
    state=data['captured_system_state']
    unit_to_world=np.array(state['Grid3D_FLIP_FluidControl_Emitter.UnitToWorld']).reshape(4,4)
    extents=np.linalg.norm(unit_to_world[:3,:3],axis=1)
    if not np.allclose(extents,[2231.25,2231.25,800],atol=.01,rtol=0):
        raise ValueError('Unexpected fixture extent')
    quadratic=capture.get('quadratic_transfer_requested',False)
    result=compare(rows,fields['Velocity'],fields['SolidVelocity_Boundary'],extents,quadratic=quadratic)
    if result['actual_gpu_sampling_coordinates']:
        world_to_unit=np.array(state['Grid3D_FLIP_FluidControl_Emitter.WorldToUnit']).reshape(4,4)
        rotation=unit_to_world[:3,:3]/extents[:,None]
        bottom_origin=unit_to_world[3,:3]+.5*(unit_to_world[0,:3]+unit_to_world[1,:3])
        a=np.asarray(rows);world=a[:,1:4]@rotation+bottom_origin
        expected_unit=np.c_[world,np.ones(len(a))]@world_to_unit
        result['sampling_coordinate_max_error']=float(abs(expected_unit[:,:3]-a[:,13:16]).max())
        result['sampling_coordinate_verified']=result['sampling_coordinate_max_error']<=1e-6
        result['stored_transform_inverse_max_error']=float(abs(unit_to_world@world_to_unit-np.eye(4)).max())
    else:
        result['sampling_coordinate_verified']=False
    ids=np.asarray(rows)[:,0];pids=np.asarray(primary['particle_rows'])[:,0]
    result['particle_identity_exact']=bool(np.array_equal(ids,pids) and len(np.unique(ids))==len(ids))
    shader_files=list((directory/'active_compiled_shaders').glob('*.hlsl'))
    code='\n'.join(shader_text(p.read_bytes()) for p in shader_files)
    result['compiled_transfer_markers']={s:s in code for s in ('RiverAffineGridToParticle','RiverAffineParticleToGrid','RiverAffineX','RiverAffineY','RiverAffineZ')}
    if quadratic:
        result['compiled_transfer_markers'].update({s:s in code for s in ('RiverQuadraticGridToParticle','RiverQuadraticParticleToGrid')})
    result['verified']=bool(result['gradient_parity'] and result['sampling_coordinate_verified'] and result['particle_identity_exact'] and result['nonzero_gradient_particles']>0 and all(result['compiled_transfer_markers'].values()))
    files=[directory/'capture.json',particle_file,*sorted((directory/(stem+'_grids')).glob('*')),*shader_files]
    result['source_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
    result['physical_or_visual_acceptance']=False
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args();output=args.output or args.directory/'affine_audit.json'
    if output.exists():raise FileExistsError(output)
    report=audit(args.directory)
    output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
    raise SystemExit(0 if report['verified'] else 1)
