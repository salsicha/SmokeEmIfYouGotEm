"""Independent native primary-particle mapping and authored contact, no solve."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import bpy
import manta
import numpy as np
from mathutils.bvhtree import BVHTree

sys.path.insert(0,str(Path(__file__).resolve().parent))
from probe_water_feature_native_transport import actual_space
from probe_water_feature_solver_stages import vector_data_address,cleanup
from water_feature_geometry import world_coordinates
from water_feature_solid_clip import EDDY_SOLIDS
from audit_water_feature_mesh_contact import topology,contact


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    audit=json.loads(args.audit.read_text());control=audit['controls'][0];root=Path(control['source_blend']).parent
    if not audit['complete'] or audit['accepted'] or Path(bpy.data.filepath).resolve()!=Path(control['source_blend']).resolve():
        raise ValueError('Exact preserved native panel required')
    hashes={**audit['dependency_sha256'],**audit['outputs_sha256']}
    for p in (Path(__file__),args.audit,Path(__file__).with_name('audit_water_feature_particle_mapping.py')):
        hashes[str(p.resolve())]=digest(p)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned audit changed before particle check')
    scene=bpy.context.scene;domain=bpy.data.objects['Feature liquid'];state=domain.modifiers[0].domain_settings
    state.cache_directory=str(root/'cache');scene.frame_set(145);shape=tuple(control['shape']);actual_space(shape)
    origin=np.asarray(control['origin_m']);h=control['cell_m'];solids={};rows=[]
    for name in EDDY_SOLIDS:
        obj=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
        try:
            mesh.calc_loop_triangles();vertices=world_coordinates([v.co[:] for v in mesh.vertices],obj.matrix_world)
            triangles=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int64)
            if topology(triangles)!=dict(boundary_edges=0,nonmanifold_edges=0):raise ValueError('Closed actual solid required')
            solids[name]=(vertices.min(0),vertices.max(0),BVHTree.FromPolygons(vertices.tolist(),triangles.tolist(),all_triangles=True))
        finally:obj.to_mesh_clear()
    for frame in (145,169,191):
        scene.frame_set(frame);obj=domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
        ps=next(s for s in obj.particle_systems if s.name.lower()=='liquid');count=len(ps.particles)
        if count<=0:raise ValueError('Actual primary particles missing')
        p=np.empty(count*3,np.float32);v=np.empty(count*3,np.float32)
        ps.particles.foreach_get('location',p);ps.particles.foreach_get('velocity',v)
        p=p.reshape(-1,3);v=v.reshape(-1,3);scope={};error=None;row=None
        try:
            scope['s99']=manta.Solver(name='owned_padded_particle_check',gridSize=manta.vec3(*shape),dim=3)
            scope['pp_s99']=scope['s99'].create(manta.BasicParticleSystem,name='particles')
            scope['pVel_pp99']=scope['pp_s99'].create(manta.PdataVec3,name='particles_velocity')
            if manta.load(name=str(root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'),
                objects=[scope['pVel_pp99'],scope['pp_s99']],worldSize=6)!=1:raise ValueError('Native typed primary load failed')
            if scope['pp_s99'].pySize()!=count:raise ValueError('Native/display primary count mismatch')
            ptr=vector_data_address(scope['pp_s99'].getDataPointer(),count,16)
            payload=bytes((ctypes.c_ubyte*(count*16)).from_address(ptr))
            records=np.frombuffer(payload,dtype=np.dtype([('position','<f4',3),('flags','<i4')]))
            world=records['position']*h+origin
            ptr=vector_data_address(scope['pVel_pp99'].getDataPointer(),count,12)
            native_v=np.ctypeslib.as_array((ctypes.c_float*(count*3)).from_address(ptr)).copy().reshape(-1,3)/80
            np.testing.assert_allclose(world,p,atol=1e-6,rtol=1e-6)
            np.testing.assert_allclose(native_v,v,atol=1e-6,rtol=1e-6)
            row=dict(frame=frame,primary_count=count,native_display_position_velocity_match=True,
                maximum_position_component_error_m=float(np.abs(world-p).max()),
                maximum_velocity_component_error_mps=float(np.abs(native_v-v).max()),
                world_z_m_quantiles=np.quantile(world[:,2],[0,.01,.5,.99,1]).tolist(),
                actual_authored_contact={name:contact(world,solid) for name,solid in solids.items()},
                scope='Primary point centers only, not finite liquid mesh or particle-sphere clearance; no contact projection or flow change.')
        except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
        finally:cleanup(scope,'99')
        if error:raise RuntimeError(error)
        rows.append(row);print('PADDED_PRIMARY_CONTACT',control['panel'],frame,row['actual_authored_contact'],flush=True)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned evidence changed during particle check')
    with args.output.open('x') as stream:
        json.dump(dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,
            panel=control['panel'],frames=rows,scope=__doc__),stream,indent=2)


if __name__=='__main__':
    error=None
    try:main()
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    if error:print('PADDED_PRIMARY_CHECK_FAILED',error,flush=True);raise SystemExit(1)
