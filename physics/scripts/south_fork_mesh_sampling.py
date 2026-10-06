"""Sample the exact source triangles exported by the South Fork mesh builder.

Each raster-centre quad (a,b,c,d) is split along b--c into (a,b,c) and (b,d,c).
This matches build_south_fork_survey_review_mesh.py; bilinear interpolation is
not the same surface when the four vertices are non-coplanar.
"""
import numpy as np


def grid_triangles(rows,cols):
    if rows<2 or cols<2:raise ValueError('At least two source vertices per axis required')
    idx=np.arange(rows*cols).reshape(rows,cols)
    a=idx[:-1,:-1].ravel(); b=idx[:-1,1:].ravel(); c=idx[1:,:-1].ravel(); d=idx[1:,1:].ravel()
    return np.concatenate([np.column_stack([a,b,c]),np.column_stack([b,d,c])])


def select_bed_sampling(requested=None, parent_registration=None, raw_resume=False):
    if requested is not None:
        if requested not in ('bilinear','render_triangles','registered_triangles'):raise ValueError('Unknown bed sampling')
        return requested
    if raw_resume:raise ValueError('A raw resume frame requires explicit --bed-sampling')
    if parent_registration is not None:
        return select_bed_sampling(parent_registration.get('bed_sampling','bilinear'))
    return 'render_triangles'


def sample_triangles(values, rows, cols):
    values=np.asarray(values)
    rows,cols=np.broadcast_arrays(np.asarray(rows,dtype=float),np.asarray(cols,dtype=float))
    if (values.ndim!=2 or min(values.shape)<2 or not np.isfinite(values).all() or
        not np.isfinite(rows).all() or not np.isfinite(cols).all() or
        np.any(rows<0) or np.any(cols<0) or np.any(rows>values.shape[0]-1) or np.any(cols>values.shape[1]-1)):
        raise ValueError('Finite samples inside the source vertex lattice required')
    r=np.minimum(np.floor(rows).astype(int),values.shape[0]-2)
    c=np.minimum(np.floor(cols).astype(int),values.shape[1]-2)
    fy,fx=rows-r,cols-c
    a,b,cc,d=values[r,c],values[r,c+1],values[r+1,c],values[r+1,c+1]
    return np.where(fx+fy<=1,a*(1-fx-fy)+b*fx+cc*fy,
        b*(1-fy)+d*(fx+fy-1)+cc*(1-fx))


def sample_mesh_raster(path,east,north):
    import rasterio
    with rasterio.open(path) as source:
        col,row=(~source.transform)*(east,north)
        return sample_triangles(source.read(1).astype(float),row-.5,col-.5)
