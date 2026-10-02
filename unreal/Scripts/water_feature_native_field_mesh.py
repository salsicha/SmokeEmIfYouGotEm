"""Native zero-interface extraction from COPIES of fluid and obstacle fields.

This changes meshing, not simulated phi/velocities/particles. No particle-radius
surface is mixed into the output. Native source NEGATES values before testing
isovalue1e-4; subtracting1e-4 on the copy targets zero without changing simulation.
Sampling max(phi,-obstacle) introduces contact discretization error: report it.
"""
import ctypes
from decimal import Decimal
from pathlib import Path
import numpy as np
import bpy
import manta
from probe_water_feature_native_transport import scalar_view
from probe_water_feature_solver_stages import grid_array,vector_data_address,cleanup
from water_feature_field_surface import refine_lattice


def raw_mesh(mesh,obj_path,shape):
    lines=Path(obj_path).read_text().splitlines()
    obj_v=np.array([[float(s) for s in line.split()[1:]] for line in lines if line.startswith('v ')])
    obj_t=np.array([[int(s)-1 for s in line.split()[1:]] for line in lines if line.startswith('f ')])
    if not len(obj_v) or not len(obj_t):raise ValueError('No native extraction mesh')
    arrays=[]
    for getter,count,stride,dtype in (
            (mesh.getNodesDataPointer,len(obj_v),28,np.dtype([('flags','<i4'),('position','<f4',3),('normal','<f4',3)])),
            (mesh.getTrisDataPointer,len(obj_t),16,np.dtype([('vertices','<i4',3),('flags','<i4')]))):
        pointer=vector_data_address(getter(),count,stride)
        payload=bytes((ctypes.c_ubyte*(count*stride)).from_address(pointer))
        arrays.append(np.frombuffer(payload,dtype=dtype).copy())
    vertices=arrays[0]['position'].copy();triangles=arrays[1]['vertices'].copy()
    expected=((vertices-np.asarray(shape,dtype=np.float32)*np.float32(.5))*np.float32(1/max(shape))).astype(float)
    errors=[abs(Decimal(str(obj_v[tuple(i)]))-Decimal.from_float(float(expected[tuple(i)])))
        for i in np.argwhere(np.abs(obj_v-expected)>5e-7)]
    if (any(e>Decimal('0.0000005') for e in errors) or not np.array_equal(triangles,obj_t)
            or not np.isfinite(vertices).all() or triangles.min()<0 or triangles.max()>=len(vertices)):
        raise ValueError('Pinned native mesh ABI/OBJ coordinate check failed')
    return vertices,triangles


def extract(phi,obstacle,refinement,obj_path):
    if (bpy.app.build_hash!=b'fbe6228777e7' or manta.DOUBLEPRECISION
            or phi.ndim!=3 or phi.shape!=obstacle.shape or min(phi.shape)<8
            or refinement not in (1,2,4) or not np.isfinite(phi).all() or not np.isfinite(obstacle).all()):
        raise ValueError('Pinned float32 native build and finite matching fields required')
    scope={};error=None;result=None
    try:
        shape=phi.shape;fine_shape=tuple((n-1)*refinement+1 for n in shape)
        scope['s99']=manta.Solver(name='owned_field_extract',gridSize=manta.vec3(*shape),dim=3)
        scope['sm99']=manta.Solver(name='owned_field_extract_fine',gridSize=manta.vec3(*fine_shape),dim=3)
        for name,array in (('phi',phi),('obstacle',obstacle)):
            scope[name+'_s99']=scope['s99'].create(manta.LevelsetGrid,name='copied_'+name)
            view=scalar_view(scope[name+'_s99'],shape);view[:]=array;del view
            scope[name+'_sm99']=scope['sm99'].create(manta.LevelsetGrid,name='copied_fine_'+name)
            refined,offset=refine_lattice(array,refinement)
            view=scalar_view(scope[name+'_sm99'],fine_shape);view[:]=refined;del view
        fluid=grid_array(scope['phi_sm99'],fine_shape);solid=grid_array(scope['obstacle_sm99'],fine_shape)
        # Native LevelsetGrid.subtract is not a generic pointwise maximum
        # (its positive-air/obstacle branch differs). Define the intended
        # extraction field explicitly, on the owned copy only.
        view=scalar_view(scope['phi_sm99'],fine_shape);view[:]=np.maximum(fluid,-solid);del view
        combined=grid_array(scope['phi_sm99'],fine_shape)
        np.testing.assert_array_equal(combined,np.maximum(fluid,-solid))
        scope['phi_sm99'].addConst(-1e-4)
        scope['mesh_sm99']=scope['sm99'].create(manta.Mesh,name='native_field_zero_mesh')
        scope['phi_sm99'].createMesh(scope['mesh_sm99']);scope['mesh_sm99'].save(str(Path(obj_path).resolve()))
        vertices,triangles=raw_mesh(scope['mesh_sm99'],obj_path,fine_shape)
        for name,array in (('phi',phi),('obstacle',obstacle)):
            np.testing.assert_array_equal(grid_array(scope[name+'_s99'],shape),array)
        result=vertices,triangles,dict(refinement=refinement,fine_shape=list(fine_shape),
            base_coordinate_offset_cells=offset,original_cell_center_knots_preserved=True,
            position_mapping='base_grid_position = native_fine_position / refinement + base_coordinate_offset_cells',
            simulation_copies_unchanged=True,copied_max_grid_verified=True,isovalue=1e-4,
            native_values_negated_before_isovalue=True,extraction_copy_offset=-1e-4,
            isovalue_compensated_on_extraction_copy=True,native_indices_and_obj_coordinates_verified=True,
            field_units='base-grid cells even at refined extraction; vertex units are refined-grid cells',
            scope=__doc__)
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    finally:cleanup(scope,'99')
    if error:raise RuntimeError(error)
    return result
