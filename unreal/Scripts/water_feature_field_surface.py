"""Independent cell-centered field/mesh checks; no particle or surface repair."""
import numpy as np


def regularize_exact_mesh(vertices,triangles):
    """Merge EXACT duplicate coordinates and discard EXACT zero-area faces.

    No epsilon weld, vertex motion, smoothing, or surface fitting. Native
    marching cubes may create coincident edge vertices at a zero-valued knot.
    Raw output stays separately preserved; closed-edge checks are still required.
    """
    vertices=np.asarray(vertices);triangles=np.asarray(triangles)
    if vertices.ndim!=2 or vertices.shape[1]!=3 or not np.isfinite(vertices).all():
        raise ValueError('Finite vertex coordinates required')
    unique,inverse=np.unique(vertices,axis=0,return_inverse=True)
    mapped=inverse[triangles]
    xyz=unique[mapped].astype(float)
    area=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
    zero=np.all(area==0.,axis=1)
    output=mapped[~zero]
    before=vertices[triangles].astype(float);after=unique[output].astype(float)
    volume_before=float(np.einsum('ij,ij->i',before[:,0],np.cross(before[:,1],before[:,2])).sum()/6)
    volume_after=float(np.einsum('ij,ij->i',after[:,0],np.cross(after[:,1],after[:,2])).sum()/6)
    if abs(volume_before-volume_after)>1e-12*max(1.,abs(volume_before)):
        raise ValueError('Exact topology cleanup changed signed volume beyond float64 summation allowance')
    return unique,output,dict(duplicate_vertices_merged=len(vertices)-len(unique),exact_zero_area_faces_removed=int(zero.sum()),
        vertex_displacement=0.,epsilon_weld=False,native_signed_volume_before=volume_before,native_signed_volume_after=volume_after,
        relative_summation_allowance=1e-12)


def refine_lattice(array,refinement):
    """Refine original cell-center knots, not a resized cell-center domain.

    Fine-grid centers map to base coordinates p/r + (1/2 - 1/(2r)).
    Every original knot remains present. Coverage is the original center box;
    no ghost values or unsupported half-cell exterior are fabricated.
    """
    array=np.asarray(array)
    if array.ndim!=3 or min(array.shape)<2 or refinement not in (1,2,4) or not np.isfinite(array).all():
        raise ValueError('Finite supported original lattice required')
    result=array.astype(float)
    for axis,n in enumerate(array.shape):
        coordinate=np.arange((n-1)*refinement+1)/refinement
        lower=np.minimum(np.floor(coordinate).astype(int),n-2)
        fraction=coordinate-lower;dims=[1,1,1];dims[axis]=len(coordinate)
        result=np.take(result,lower,axis=axis)*(1-fraction).reshape(dims)+np.take(result,lower+1,axis=axis)*fraction.reshape(dims)
    result=result.astype(np.float32)
    np.testing.assert_array_equal(result[::refinement,::refinement,::refinement],array.astype(np.float32))
    return result,.5-.5/refinement


def sample_centers(array,positions):
    array=np.asarray(array);positions=np.asarray(positions,dtype=float)
    if (array.ndim!=3 or positions.ndim!=2 or positions.shape[1]!=3
            or not np.isfinite(array).all() or not np.isfinite(positions).all()):
        raise ValueError('Finite scalar field and grid-coordinate points required')
    coordinates=positions-.5;base=np.floor(coordinates).astype(int)
    if np.any(coordinates<0) or np.any(coordinates>np.asarray(array.shape)-1):
        raise ValueError('Unsupported samples must not be clamped or extrapolated')
    # A point exactly on the final original knot has a valid one-sided
    # trilinear value. This is not extension/clamping of an exterior point.
    base=np.minimum(base,np.asarray(array.shape)-2)
    fraction=coordinates-base;result=np.zeros(len(positions))
    for bit in np.ndindex(2,2,2):
        ids=base+bit;weight=np.where(np.array(bit),fraction,1-fraction).prod(axis=1)
        result+=weight*array[ids[:,0],ids[:,1],ids[:,2]]
    return result


def interface_residuals(phi,obstacle,vertices,triangles):
    vertices=np.asarray(vertices);triangles=np.asarray(triangles)
    if triangles.ndim!=2 or triangles.shape[1]!=3 or triangles.min()<0 or triangles.max()>=len(vertices):
        raise ValueError('Matching finite mesh required')
    rows={}
    for name,points in (('vertices',vertices),('triangle_centers',vertices[triangles].mean(axis=1))):
        liquid=sample_centers(phi,points);solid=sample_centers(obstacle,points)
        rows[name]=dict(count=len(points),minimum_solid_phi_cells=float(solid.min()),
            maximum_inside_solid_phi_cells=float(max(0.,-solid.min())),
            composite_residual_abs_cells_quantiles=np.quantile(np.abs(np.maximum(liquid,-solid)),[0,.5,.95,1]).tolist(),
            liquid_phi_cells_quantiles=np.quantile(liquid,[0,.5,.95,1]).tolist(),
            scope='Trilinear native cell values, not signed geometric distances unless independently qualified')
    return rows


def planar_case(shape,normal,offset):
    normal=np.asarray(normal,dtype=float)
    if normal.shape!=(3,) or not np.isfinite(normal).all() or np.linalg.norm(normal)<1e-9:
        raise ValueError('Nonzero finite plane normal required')
    normal/=np.linalg.norm(normal)
    xyz=np.stack(np.meshgrid(*[np.arange(n)+.5 for n in shape],indexing='ij'),axis=-1)
    return (xyz@normal-offset).astype(np.float32),normal
