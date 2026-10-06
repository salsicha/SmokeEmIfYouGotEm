"""Closed manufactured still-water control with actual compiled native FLIP.

No host emitters, new flow, foam, cache retiming or velocity/surface correction.
Native body/mesh recipes run on owned resources; source case is read-only.
Flat-lattice radius is an orientation/grid-phase-specific control, NOT a repair
for arbitrary particle clouds, overturning/curved interfaces or river features.
"""
import argparse
import ctypes
from decimal import Decimal
import gc
import hashlib
import json
from pathlib import Path
import sys
import time
import types
import bpy
import manta
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from water_feature_flat_reference import planar_phi,lattice_particle_phi,flat_lattice_radius,root_height
from water_feature_private_step import global_names,bind_owned
from probe_water_feature_native_transport import actual_space,make_owned,scalar_view,GRID_TYPES
from probe_water_feature_solver_stages import grid_array,vector_data_address,cleanup
from audit_water_feature_native_mac_extension import native_view,digest
from water_feature_stage_interfaces import column_interface

SHAPE=(32,24,24)
H=.075
HEIGHT=12
LEVELS=list(range(9,16))
COLUMNS=[[x,y] for x in range(4,28,4) for y in range(4,20,4)]


def particle_copy(space,identifier):
    count=space[f'pp_s{identifier}'].pySize()
    if count<=0:raise ValueError('Missing manufactured particles')
    pointer=vector_data_address(space[f'pp_s{identifier}'].getDataPointer(),count,16)
    payload=bytes((ctypes.c_ubyte*(count*16)).from_address(pointer))
    return np.frombuffer(payload,dtype=np.dtype([('position','<f4',3),('flags','<i4')])).copy()


def mesh_copy(mesh,path,upres):
    """Pinned native Node/Triangle layout; OBJ normalization checked independently.

    Node: int flags, Vec3<float> position, Vec3<float> normal (28 bytes).
    Triangle: int vertices[3], int flags (16 bytes). Public getters return
    addresses of std::vector headers, not their payloads. Validate lengths
    against the independently exported OBJ before reading any payload.
    """
    lines=path.read_text().splitlines()
    obj_vertices=np.array([[float(v) for v in line.split()[1:]] for line in lines if line.startswith('v ')])
    obj_triangles=np.array([[int(v)-1 for v in line.split()[1:]] for line in lines if line.startswith('f ')])
    counts=(len(obj_vertices),len(obj_triangles))
    if min(counts)<=0:raise ValueError('Empty native manufactured mesh')
    arrays=[]
    for getter,count,stride,dtype in (
            (mesh.getNodesDataPointer,counts[0],28,np.dtype([('flags','<i4'),('position','<f4',3),('normal','<f4',3)])),
            (mesh.getTrisDataPointer,counts[1],16,np.dtype([('vertices','<i4',3),('flags','<i4')]))):
        pointer=vector_data_address(getter(),count,stride)
        payload=bytes((ctypes.c_ubyte*(count*stride)).from_address(pointer))
        arrays.append(np.frombuffer(payload,dtype=dtype).copy())
    positions=arrays[0]['position'].copy();triangles=arrays[1]['vertices'].copy()
    mesh_shape=np.array(SHAPE)*upres
    # The pinned writer casts to Vec3<float> BEFORE subtracting/normalizing.
    # Preserve those operations; a float64 expression is not its exact output.
    expected=((positions-mesh_shape.astype(np.float32)*np.float32(.5))
        *np.float32(1/max(mesh_shape))).astype(np.float64)
    error=float(np.max(np.abs(obj_vertices-expected)))
    # At an EXACT decimal boundary, float64 subtraction can report
    # 0.000000500000000014 rather than 0.0000005. Check only these ambiguous
    # comparisons in exact Decimal arithmetic. The allowance remains 5e-7.
    decimal_errors=[abs(Decimal(str(obj_vertices[tuple(index)]))-Decimal.from_float(float(expected[tuple(index)])))
        for index in np.argwhere(np.abs(obj_vertices-expected)>5e-7)]
    if (not np.isfinite(positions).all() or any(e>Decimal('0.0000005') for e in decimal_errors)
            or not np.array_equal(triangles,obj_triangles)
            or triangles.min()<0 or triangles.max()>=len(positions)):
        raise ValueError('Native mesh ABI/OBJ coordinate mapping failed: '+str(dict(
            error=error,allowance=5e-7,position_extent=[positions.min(0).tolist(),positions.max(0).tolist()],
            obj_extent=[obj_vertices.min(0).tolist(),obj_vertices.max(0).tolist()],
            indices_match=np.array_equal(triangles,obj_triangles),mesh_shape=mesh_shape.tolist())))
    return positions,triangles,dict(node_stride_bytes=28,triangle_stride_bytes=16,
        obj_normalization_verified=True,max_normalized_coordinate_error=error,allowance=5e-7,
        exact_decimal_boundary_checks=len(decimal_errors),
        maximum_exact_decimal_boundary_error=str(max(decimal_errors)) if decimal_errors else None,
        all_triangle_indices_match=True,native_positions_are_mesh_grid_coordinates=True,
        physical_mapping='native_position * mesh_cell_m; OBJ * max(shape)*cell_m + shape*cell_m/2')


def allocate_mesh(source,identifier,base,shape,scope):
    original=source[f'liquid_step_mesh_{identifier}']
    upres=source[f'upres_sm{identifier}']
    scope[f'sm{identifier}']=manta.Solver(name='owned_flat_mesh',gridSize=manta.vec3(*[n*upres for n in shape]),dim=3)
    calls={}
    for name in global_names(original):
        if name in base:
            scope[name]=base[name]
            continue
        if name not in source:continue
        value=source[name];kind=type(value).__name__
        if isinstance(value,types.BuiltinFunctionType):calls[name]=value
        elif isinstance(value,(type(None),bool,int,float,str)):scope[name]=value
        elif kind=='vec3':scope[name]=manta.vec3(value.x,value.y,value.z)
        elif kind in GRID_TYPES:scope[name]=scope[f'sm{identifier}'].create(GRID_TYPES[kind],name='owned_'+name)
        elif kind=='BasicParticleSystem':scope[name]=scope[f'sm{identifier}'].create(manta.BasicParticleSystem,name='owned_'+name)
        elif kind=='ParticleIndexSystem':scope[name]=scope[f'sm{identifier}'].create(manta.ParticleIndexSystem,name='owned_'+name)
        elif kind=='Mesh':scope[name]=scope[f'sm{identifier}'].create(manta.Mesh,name='owned_'+name)
        elif name!=f'sm{identifier}':raise ValueError('Unknown mesh global '+name+':'+kind)
    for name in (f'phiParts_sm{identifier}',f'phi_sm{identifier}'):
        scope[name].setConst(9999.)
    function,proof=bind_owned(original,scope,calls,{'float':float,'str':str})
    scope[f'liquid_step_mesh_{identifier}']=function
    return proof,upres


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--subdivision',type=int,choices=(1,2,4),required=True)
    parser.add_argument('--radius',choices=('stock','flat-lattice'),default='stock')
    parser.add_argument('--frames',type=int,default=48)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists() or not 1<=args.frames<=48:raise ValueError('Fresh bounded control required')
    source_blend=Path(bpy.data.filepath).resolve();root=source_blend.parent
    if bpy.app.build_hash!=b'fbe6228777e7' or root.name!='eddy-v2-grid-aligned-modular':
        raise ValueError('Matched installed native recipe required')
    originals=[source_blend,root/'setup.json',root/'cache'/'data'/'fluid_data_0192.vdb',root/'cache'/'config'/'config_0192.uni']
    hashes={str(p):digest(p) for p in originals}
    names=('probe_water_feature_flat_equilibrium.py','water_feature_flat_reference.py','test_water_feature_flat_reference.py',
        'water_feature_private_step.py','probe_water_feature_native_transport.py','probe_water_feature_solver_stages.py',
        'audit_water_feature_native_mac_extension.py','water_feature_stage_interfaces.py')
    code={str(Path(__file__).with_name(n).resolve()):digest(Path(__file__).with_name(n)) for n in names}
    domain=bpy.data.objects['Feature liquid'];domain.modifiers[0].domain_settings.cache_directory=str(root/'cache')
    bpy.context.scene.frame_set(192)
    source,identifier=actual_space((80,21,39))
    def live_hashes():
        return {name:hashlib.sha256((native_view(source[f'{name}_s{identifier}'],(80,21,39)).copy()
            if name.startswith('vel') else grid_array(source[f'{name}_s{identifier}'],(80,21,39))).tobytes()).hexdigest()
            for name in ('phi','phiTmp','vel','velTmp')}
    live_before=live_hashes()
    args.output.mkdir();(args.output/'arrays').mkdir();(args.output/'mesh').mkdir()
    report=dict(complete=False,accepted=False,original_input_sha256=hashes,source_code_sha256=code,
        shape=list(SHAPE),cell_m=H,initial_height_m=HEIGHT*H,subdivision=args.subdivision,radius_policy=args.radius,
        frame_count=args.frames,fps=24,steps=[],frames=[],arrays={},meshes={},columns=COLUMNS,
        scope=__doc__,no_host_sources=True,closed_boundary=True,pressure_gravity_enabled=True)
    space={};mesh_scope={};error=None;start=time.perf_counter()
    try:
        space,calls,created,proof=make_owned(source,identifier,SHAPE,space)
        bound=space[f'liquid_step_{identifier}'];globals=bound.__globals__
        # Declared manufactured-domain changes, not modifications to the source
        # case or its cached field. No velocity is reset during evolution.
        globals[f'domainClosed_s{identifier}']=True
        globals[f'using_outflow_s{identifier}']=False
        original_radius=globals[f'radiusFactor_s{identifier}']
        radius=original_radius if args.radius=='stock' else flat_lattice_radius()
        globals[f'radiusFactor_s{identifier}']=radius
        report.update(exact_liquid_code=proof,stock_radius_factor=original_radius,radius_factor=radius,
            gravity_native=[getattr(globals[f'gravity_s{identifier}'],axis) for axis in 'xyz'],
            physical_velocity_scale=H*2.5,manufactured_overrides=['closed=True','outflow=False','radius='+str(radius)])
        report['inherited_native_parameters']={name:globals[f'{name}_s{identifier}'] for name in
            ('minParticles','maxParticles','adjustedNarrowBandWidth','narrowBandWidth','res','using_apic',
             'using_fractions','using_diffusion','using_viscosity','using_guiding','flipRatio')}
        if any(report['inherited_native_parameters'][name] for name in
                ('using_apic','using_fractions','using_diffusion','using_viscosity','using_guiding')):
            raise ValueError('Manufactured control requires the matched simple FLIP recipe')
        phi=planar_phi(SHAPE,HEIGHT)
        view=scalar_view(space[f'phi_s{identifier}'],SHAPE);view[:]=phi;del view
        space[f'phiTmp_s{identifier}'].copyFrom(space[f'phi_s{identifier}'])
        space[f'phiObs_s{identifier}'].setConst(9999.)
        space[f'flags_s{identifier}'].initDomain(boundaryWidth=1,phiWalls=space[f'phiObs_s{identifier}'])
        space[f'phiObsIn_s{identifier}'].copyFrom(space[f'phiObs_s{identifier}'])
        space[f'flags_s{identifier}'].updateFromLevelset(space[f'phi_s{identifier}'])
        for name in ('vel','velTmp','velOld','velParts','mapWeights','forces','obvel'):
            if f'{name}_s{identifier}' in space:space[f'{name}_s{identifier}'].setConst(manta.vec3(0.))
        space[f'pVel_pp{identifier}'].setSource(grid=space[f'vel_s{identifier}'],isMAC=True)
        manta.sampleLevelsetWithParticles(phi=space[f'phi_s{identifier}'],flags=space[f'flags_s{identifier}'],
            parts=space[f'pp_s{identifier}'],discretization=2,randomness=0.,reset=True)
        space[f'pVel_pp{identifier}'].setConst(manta.vec3(0.))
        particles=particle_copy(space,identifier)
        pos=particles['position']
        if not np.all(np.isin(np.mod(pos*4,4),[1.,3.])) or np.any(pos[:,2]>=HEIGHT):
            raise ValueError('Native seed is not the declared zero-jitter interior lattice')
        report['initial_particles']=dict(count=len(particles),payload_sha256=hashlib.sha256(particles.tobytes()).hexdigest(),
            exact_quarter_cell_lattice=True,all_below_analytic_surface=True)
        del pos,particles
        predicted=lattice_particle_phi(LEVELS,HEIGHT,radius)
        report['analytic_particle_union_reference']=dict(levels=LEVELS,phi_cells=predicted.tolist(),
            predicted_zero_height_cells=root_height(LEVELS,predicted),not_a_physical_foam_model=True)
        report['exact_mesh_code'],upres=allocate_mesh(source,identifier,space,SHAPE,mesh_scope)
        report['mesh_cell_m']=H/upres
        report['mesh_native_public_api']=sorted(name for name in dir(mesh_scope[f'mesh_sm{identifier}']) if not name.startswith('_'))
        report['native_mesh_sources']=['https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/'+p
            for p in ('mesh.h','mesh.cpp','fileio/iomeshes.cpp')]
        report['native_mesh_source_license']='Apache-2.0; exact-build source used for ABI/coordinate verification, not captured river evidence'
        obstacle=grid_array(space[f'phiObs_s{identifier}'],SHAPE)
        obstacle_path=args.output/'arrays'/'obstacle.npy'
        with obstacle_path.open('xb') as stream:np.save(stream,obstacle,allow_pickle=False)
        report['arrays'][str(obstacle_path.resolve())]=digest(obstacle_path)
        report['obstacle_array']=str(obstacle_path.resolve())
        def snapshot(label,frame):
            fields={name:(native_view(space[f'{prefix}_s{identifier}'],SHAPE,integer=name=='flags').copy()
                if name in ('velocity','flags') else grid_array(space[f'{prefix}_s{identifier}'],SHAPE))
                for name,prefix in (('phi','phi'),('flags','flags'),('velocity','vel'))}
            if any(not np.isfinite(v).all() for v in fields.values()):raise ValueError('Nonfinite manufactured evolution')
            samples=[dict(column=c,interface=column_interface(fields['phi'],fields['flags'],c,H)) for c in COLUMNS]
            row=dict(frame=frame,label=label,primary_count=space[f'pp_s{identifier}'].pySize(),columns=samples,fields={},
                max_grid_speed_mps=float(np.linalg.norm(fields['velocity'],axis=-1).max())*H*2.5)
            for name,array in fields.items():
                path=args.output/'arrays'/f'{frame:03d}-{label}-{name}.npy'
                with path.open('xb') as stream:np.save(stream,array,allow_pickle=False)
                sha=digest(path);report['arrays'][str(path.resolve())]=sha;row['fields'][name]=str(path.resolve())
            report['frames'].append(row)
        snapshot('initial',0)
        def mesh_snapshot(frame):
            before={name:hashlib.sha256(grid_array(space[f'{name}_s{identifier}'],SHAPE).tobytes()).hexdigest()
                for name in ('phi','phiTmp')}
            started=time.perf_counter()
            mesh_scope[f'liquid_step_mesh_{identifier}']()
            path=args.output/'mesh'/f'frame_{frame:03d}.obj'
            mesh_scope[f'mesh_sm{identifier}'].save(str(path.resolve()))
            if not path.is_file() or path.stat().st_size<100:raise ValueError('Native manufactured mesh export failed')
            positions,triangles,mapping=mesh_copy(mesh_scope[f'mesh_sm{identifier}'],path,upres)
            report['meshes'][str(path.resolve())]=digest(path)
            row=dict(frame=frame,obj=str(path.resolve()),mapping=mapping,elapsed_s=time.perf_counter()-started)
            for name,array in (('positions',positions),('triangles',triangles)):
                array_path=args.output/'mesh'/f'frame_{frame:03d}-{name}.npy'
                with array_path.open('xb') as stream:np.save(stream,array,allow_pickle=False)
                report['meshes'][str(array_path.resolve())]=digest(array_path)
                row[name]=str(array_path.resolve())
            if any(hashlib.sha256(grid_array(space[f'{name}_s{identifier}'],SHAPE).tobytes()).hexdigest()!=sha
                    for name,sha in before.items()):raise ValueError('Meshing changed native base phi fields')
            report.setdefault('mesh_frames',[]).append(row)
        mesh_snapshot(0)
        observations=[];first={'active':False,'union_checked':False}
        def union_observer(*a,**kwargs):
            result=calls['unionParticleLevelset'](*a,**kwargs)
            if first['active'] and not first['union_checked']:
                array=grid_array(space[f'phiParts_s{identifier}'],SHAPE)
                interior=array[4:28,4:20,9:16]
                expected=np.broadcast_to(predicted,interior.shape)
                # Fixed predeclared float32 arithmetic allowance, not fitted
                # after seeing a failed comparison or a pressure response.
                maximum=float(np.max(np.abs(interior-expected)))
                if maximum>2e-6:raise ValueError('Native particle union differs from analytic lattice reference')
                report['analytic_union_verified']=dict(maximum_error_cells=maximum,allowance_cells=2e-6,
                    compared_scalars=interior.size,particle_count_unchanged=space[f'pp_s{identifier}'].pySize()==report['initial_particles']['count'])
                first['union_checked']=True
            return result
        globals['unionParticleLevelset']=union_observer
        def advect_observer(*a,**kwargs):
            result=calls['advectSemiLagrange'](*a,**kwargs)
            if first['active'] and kwargs.get('grid') is space[f'phi_s{identifier}']:
                actual=grid_array(space[f'phi_s{identifier}'],SHAPE)
                report['initial_zero_velocity_phi_advection_bitexact']=np.array_equal(actual[4:28,4:20,2:22],phi[4:28,4:20,2:22])
            return result
        globals['advectSemiLagrange']=advect_observer
        # First join is sampled before any extrapolation/pressure update.
        def extrapolate_observer(*a,**kwargs):
            if first['active'] and kwargs.get('phi') is space[f'phi_s{identifier}'] and not observations:
                actual=grid_array(space[f'phi_s{identifier}'],SHAPE)
                flags=native_view(space[f'flags_s{identifier}'],SHAPE,integer=True).copy()
                observations.extend(dict(column=c,interface=column_interface(actual,flags,c,H)) for c in COLUMNS)
            return calls['extrapolateLsSimple'](*a,**kwargs)
        globals['extrapolateLsSimple']=extrapolate_observer
        space[f's{identifier}'].frameLength=2.5/24
        # Native step() snaps its clock to (++frame)*frameLength. A zero-time
        # manufactured initial condition must therefore start at native frame0.
        space[f's{identifier}'].frame=0
        space[f's{identifier}'].timeTotal=0.
        space[f's{identifier}'].timePerFrame=0.
        space[f's{identifier}'].timestep=2.5/(24*2*args.subdivision)
        for frame in range(1,args.frames+1):
            for substep in range(2*args.subdivision):
                index=len(report['steps']);first['active']=index==0
                row=dict(index=index,requested_frame=frame,substep=substep,
                    frame=space[f's{identifier}'].frame,dt_native=space[f's{identifier}'].timestep,
                    time_native_before=space[f's{identifier}'].timeTotal,primary_before=space[f'pp_s{identifier}'].pySize())
                started=time.perf_counter()
                bound();space[f's{identifier}'].step()
                row.update(time_native_after=space[f's{identifier}'].timeTotal,primary_after=space[f'pp_s{identifier}'].pySize())
                row['body_and_clock_elapsed_s']=time.perf_counter()-started
                report['steps'].append(row)
                expected=sum(step['dt_native'] for step in report['steps'])
                if abs(row['time_native_after']-expected)/2.5>1e-5:
                    raise ValueError('Native clock/integrated duration mismatch beyond the fixed 10-microsecond allowance')
            snapshot('evolved',frame)
            mesh_snapshot(frame)
        report.update(complete=True,first_join_columns=observations,
            nominal_duration_s=args.frames/24,integrated_duration_s=sum(r['dt_native'] for r in report['steps'])/2.5,
            native_final_clock_s=space[f's{identifier}'].timeTotal/2.5)
    except Exception as exc:
        error=f'{type(exc).__name__}: {exc}';report['error']=error;exc.__traceback__=None
    finally:
        # Mesh function aliases private base fields. Release all aliases before
        # either native owner is freed; actual scene native resources are never
        # cleaned here. Remove base aliases from the mesh scope before cleanup.
        mesh_fn=mesh_scope.get(f'liquid_step_mesh_{identifier}')
        if mesh_fn is not None:mesh_fn.__globals__.clear()
        del mesh_fn
        for name in list(mesh_scope):
            if name in space:mesh_scope.pop(name)
        cleanup(mesh_scope,identifier)
        fn=space.get(f'liquid_step_{identifier}')
        if fn is not None:fn.__globals__.clear()
        del fn
        cleanup(space,identifier)
        report.update(live_engine_fields_unchanged=live_hashes()==live_before,
            originals_unchanged=all(digest(p)==sha for p,sha in hashes.items()),
            executed_modules_unchanged=all(digest(p)==sha for p,sha in code.items()),elapsed_s=time.perf_counter()-start)
        with (args.output/'flat-equilibrium.json').open('x') as stream:json.dump(report,stream,indent=2)
    if error:raise RuntimeError(error)
    if not all(report[k] for k in ('live_engine_fields_unchanged','originals_unchanged','executed_modules_unchanged')):
        raise ValueError('Original source/engine changed')
    print('NATIVE_FLAT_EQUILIBRIUM_COMPLETE',args.radius,args.subdivision,len(report['steps']),report['elapsed_s'],flush=True)


if __name__=='__main__':
    error=None
    try:main()
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    if error:print('NATIVE_FLAT_EQUILIBRIUM_FAILED',error,flush=True);raise SystemExit(1)
