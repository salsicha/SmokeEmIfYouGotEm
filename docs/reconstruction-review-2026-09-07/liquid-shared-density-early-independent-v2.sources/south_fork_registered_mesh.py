"""Exact barycentric sampling of the locally registered rock-vertex mesh.

This is not raster interpolation or unconstrained Delaunay triangulation.
Each original lattice quad retains its four corners and one valid diagonal.
Original XY can move by at most half a cell per axis, so a bounded 3x3-quad
search contains every possible source triangle covering a query.
"""
import numpy as np


class RegisteredMeshSampler:
    def __init__(self, mesh):
        x, y, z = (np.asarray(mesh[k], dtype=float) for k in ('east_m','north_m','z_m'))
        if x.shape != y.shape or x.shape != z.shape or x.ndim != 2 or min(x.shape) < 2:
            raise ValueError('Matching two-dimensional mesh coordinates required')
        if not all(np.isfinite(v).all() for v in (x,y,z)):
            raise ValueError('Finite mesh coordinates required')
        self.rows, self.cols = x.shape
        self.east = np.asarray(mesh['nominal_east_axis_m'], dtype=float)
        self.north = np.asarray(mesh['nominal_north_axis_m'], dtype=float)
        if self.east.shape != (self.cols,) or self.north.shape != (self.rows,):
            raise ValueError('Explicit nominal axes required')
        self.dx, self.dy = self.east[1]-self.east[0], self.north[0]-self.north[1]
        if self.dx <= 0 or self.dy <= 0 or not np.isfinite(self.dx+self.dy):
            raise ValueError('Nominal east increases and north decreases')
        if not np.allclose(np.diff(self.east), self.dx, atol=1e-9, rtol=0) or not np.allclose(np.diff(self.north), -self.dy, atol=1e-9, rtol=0):
            raise ValueError('Nominal lattice is not regular')
        if np.any(abs(x-self.east) > self.dx/2+1e-8) or np.any(abs(y-self.north[:,None]) > self.dy/2+1e-8):
            raise ValueError('Vertex registration exceeded the bounded source cell')
        self.xyz = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
        self.faces = np.asarray(mesh['triangles'])
        self.quads = (self.rows-1)*(self.cols-1)
        if self.faces.shape != (2*self.quads,3) or not np.issubdtype(self.faces.dtype,np.integer):
            raise ValueError('Two integer-indexed triangles per nominal quad required')
        if np.any(self.faces < 0) or np.any(self.faces >= len(self.xyz)):
            raise ValueError('Triangle index outside mesh')
        r,c = np.indices((self.rows-1,self.cols-1))
        a = (r*self.cols+c).ravel()
        allowed = np.stack((a,a+1,a+self.cols,a+self.cols+1),axis=1)
        pair = np.concatenate((self.faces[:self.quads],self.faces[self.quads:]),axis=1)
        if not np.all(np.any(pair[:,:,None] == allowed[:,None,:],axis=2)):
            raise ValueError('Triangle escaped its source quad')
        # Exactly the two supported partitions, with the preserved winding.
        b,cc,d = a+1,a+self.cols,a+self.cols+1
        bc = np.concatenate((np.stack((a,b,cc),axis=1),np.stack((b,d,cc),axis=1)),axis=1)
        ad = np.concatenate((np.stack((a,b,d),axis=1),np.stack((a,d,cc),axis=1)),axis=1)
        if not np.all(np.all(pair == bc,axis=1) | np.all(pair == ad,axis=1)):
            raise ValueError('Invalid quad partition')
        p,q,s = (self.xyz[self.faces[:,i],:2] for i in range(3))
        area = (q[:,0]-p[:,0])*(s[:,1]-p[:,1])-(q[:,1]-p[:,1])*(s[:,0]-p[:,0])
        if np.any(area >= -1e-9):
            raise ValueError('Folded or degenerate triangle')

    def sample(self, east, north, with_normals=False):
        """Sample exact triangle height; optionally return upward ENU normals.

        Normals use the same selected face as the height, including at shared
        edges. No finite-difference smoothing or altered rock geometry.
        """
        east,north = np.broadcast_arrays(np.asarray(east,dtype=float),np.asarray(north,dtype=float))
        shape = east.shape
        ex,ny = east.ravel(),north.ravel()
        if not np.isfinite(ex).all() or not np.isfinite(ny).all():
            raise ValueError('Finite query coordinates required')
        c0 = np.floor((ex-self.east[0])/self.dx).astype(int)
        r0 = np.floor((self.north[0]-ny)/self.dy).astype(int)
        result = np.full(len(ex),np.nan)
        normals = np.full((len(ex),3),np.nan) if with_normals else None
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                r,c = r0+dr,c0+dc
                valid = (r>=0)&(r<self.rows-1)&(c>=0)&(c<self.cols-1)&np.isnan(result)
                indices = np.flatnonzero(valid)
                for side in (0,1):
                    indices = indices[np.isnan(result[indices])]
                    faces = self.faces[r[indices]*(self.cols-1)+c[indices]+side*self.quads]
                    p,q,s = (self.xyz[faces[:,j]] for j in range(3))
                    ax,ay = q[:,0]-p[:,0],q[:,1]-p[:,1]
                    bx,by = s[:,0]-p[:,0],s[:,1]-p[:,1]
                    px,py = ex[indices]-p[:,0],ny[indices]-p[:,1]
                    det = ax*by-ay*bx
                    u,v = (px*by-py*bx)/det,(ax*py-ay*px)/det
                    inside = (u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)
                    result[indices[inside]] = ((1-u-v)*p[:,2]+u*q[:,2]+v*s[:,2])[inside]
                    if with_normals:
                        n=np.cross(s[inside]-p[inside],q[inside]-p[inside])
                        normals[indices[inside]]=n/np.linalg.norm(n,axis=1)[:,None]
        if np.isnan(result).any():
            raise ValueError(f'{np.isnan(result).sum()} queries outside the registered mesh; no clamp/fill fallback')
        if with_normals:return result.reshape(shape),normals.reshape((*shape,3))
        return result.reshape(shape)
