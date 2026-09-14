"""Research block-Jacobi preconditioner from exact local principal blocks.

Only preconditioning changes: the full factored two-pole operator and original
40-CG iteration count are untouched. Disjoint <=8x8-cell patches include both
velocity components. No dropped physical stencil edges, diagonal shift, depth
floor, or pressure-result projection. Not a measured native-budget solution.
"""
import numpy as np
from reconstructed_acceleration_system import ReconstructedAccelerationSystem


class PatchPressureSystem(ReconstructedAccelerationSystem):
    def __init__(self,geometry,length):
        super().__init__(geometry,length)
        ny,nx=self.h.shape;owners=np.empty(2*self.h.size,dtype=int)
        local=np.empty_like(owners);self.patches=[]
        for y in range(0,ny,8):
            for x in range(0,nx,8):
                cells=np.array([iy*nx+ix for iy in range(y,min(y+8,ny))
                                for ix in range(x,min(x+8,nx))])
                columns=(2*cells[:,None]+np.arange(2)).ravel();index=len(self.patches)
                owners[columns]=index;local[columns]=np.arange(columns.size)
                self.patches.append(dict(columns=columns,matrix=np.eye(columns.size)))
        # Rows have already combined aliases in the authoritative operator.
        _,starts=np.unique(self.rows,return_index=True)
        ends=np.r_[starts[1:],self.rows.size]
        for start,end in zip(starts,ends):
            columns=self.columns[start:end]
            w=self.w_coefficients[start:end];v=self.v_coefficients[start:end]
            for index in np.unique(owners[columns]):
                selected=owners[columns]==index;positions=local[columns[selected]]
                a=w[selected];b=v[selected]
                self.patches[index]['matrix'][np.ix_(positions,positions)]+=self.length*(np.outer(a,a)+.75*np.outer(b,b))
        for patch in self.patches:
            patch['factor']=np.linalg.cholesky(patch['matrix'])
            for value in patch.values():value.flags.writeable=False

    def precondition(self,residual,scheme='patch'):
        if scheme!='patch':return super().precondition(residual,scheme)
        r=self._vector(residual).ravel();result=np.empty_like(r)
        for patch in self.patches:
            cols=patch['columns'];factor=patch['factor']
            result[cols]=np.linalg.solve(factor.T,np.linalg.solve(factor,r[cols]))
        if not np.isfinite(result).all():raise ValueError('Patch solve exceeds storage range')
        return result.reshape(residual.shape)
