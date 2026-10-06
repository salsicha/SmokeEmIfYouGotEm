"""Independent manufactured-plane geometry checks, not liquid mass or foam."""
from collections import Counter
import numpy as np


def closed_box_phi(shape,border_cells=2):
    if len(shape)!=3 or any(n<2*border_cells+2 for n in shape) or border_cells<1:
        raise ValueError('Finite box with an interior required')
    xyz=np.stack(np.meshgrid(*[np.arange(n)+.5 for n in shape],indexing='ij'),axis=-1)
    return np.minimum(xyz-border_cells,np.asarray(shape)-border_cells-xyz).min(axis=-1)


def mesh_metrics(positions,triangles,columns,cell_m,mesh_cell_m,shape,border_cells=2):
    vertices=np.asarray(positions,dtype=float)*mesh_cell_m
    indices=np.asarray(triangles)
    if (vertices.ndim!=2 or vertices.shape[1]!=3 or not np.isfinite(vertices).all()
            or indices.ndim!=2 or indices.shape[1]!=3 or not np.issubdtype(indices.dtype,np.integer)
            or not len(indices) or indices.min()<0 or indices.max()>=len(vertices)
            or cell_m<=0 or mesh_cell_m<=0):
        raise ValueError('Finite unchanged native mesh and physical scale required')
    t=vertices[indices];normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
    areas=np.linalg.norm(normal,axis=1)/2
    edges=Counter(tuple(sorted((int(a),int(b)))) for tri in indices for a,b in
        ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])))
    determinant=normal[:,2];upward=np.flatnonzero(determinant>0.)
    samples=[]
    for column in columns:
        xy=(np.asarray(column)+.5)*cell_m
        a=t[upward,0,:2];b=t[upward,1,:2]-a;c=t[upward,2,:2]-a;q=xy-a
        den=determinant[upward]
        u=(q[:,0]*c[:,1]-q[:,1]*c[:,0])/den
        v=(b[:,0]*q[:,1]-b[:,1]*q[:,0])/den
        inside=(u>=-1e-12)&(v>=-1e-12)&(u+v<=1+1e-12)
        z=t[upward,0,2]+u*(t[upward,1,2]-t[upward,0,2])+v*(t[upward,2,2]-t[upward,0,2])
        samples.append(dict(column=list(column),status='supported' if inside.any() else 'absent',
            top_upward_triangle_height_m=float(z[inside].max()) if inside.any() else None,
            candidate_triangle_count=int(inside.sum())))
    lo=np.full(3,border_cells*cell_m);hi=(np.asarray(shape)-border_cells)*cell_m
    violation=np.maximum(np.maximum(lo-vertices,vertices-hi).max(axis=1),0.)
    return dict(vertex_count=len(vertices),triangle_count=len(indices),
        exact_zero_area_triangles=int((areas==0).sum()),minimum_triangle_area_m2=float(areas.min()),
        boundary_edges=sum(n==1 for n in edges.values()),nonmanifold_edges=sum(n>2 for n in edges.values()),
        signed_enclosed_volume_m3=float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6),
        vertex_extent_m=[vertices.min(0).tolist(),vertices.max(0).tolist()],
        sampled_vertices_outside_closed_fluid_box=int((violation>1e-8).sum()),
        maximum_vertex_wall_intrusion_m=float(violation.max()),samples=samples,
        scope='Unchanged native mesh vertices/faces; not self-intersection certification or conserved particle mass')


def paired_residuals(samples,interfaces,initial_height_m):
    if len(samples)!=len(interfaces):raise ValueError('Same fixed column cohort required')
    rows=[]
    for mesh,phi in zip(samples,interfaces):
        if mesh['column']!=phi['column']:raise ValueError('Column order changed')
        usable=mesh['status']==phi['interface']['status']=='supported'
        z=phi['interface']['crossings'][0]['relative_height_m'] if phi['interface']['status']=='supported' else None
        rows.append(dict(column=mesh['column'],mesh_status=mesh['status'],phi_status=phi['interface']['status'],
            phi_minus_initial_m=z-initial_height_m if z is not None else None,
            mesh_minus_phi_m=mesh['top_upward_triangle_height_m']-z if usable else None))
    return rows
