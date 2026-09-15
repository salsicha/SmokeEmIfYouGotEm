"""SPD periodic reference preconditioning; actual source matrix is unchanged.

Opt-in for complete, fully wet rectangular source grids only. The constant
reference depth is used ONLY by the inverse preconditioner, never by physical
source moments, pressure actions or forces. No wet/front/native acceptance.
"""
from fractions import Fraction as F
import numpy as np


class SourceSpectralReference:
    def __init__(self, system):
        part = system.partition
        ny, nx = part.patch.shape
        if (not part.patch.exact_sources or len(part.pools) != nx*ny
                or any(owners != [i] for i, owners in enumerate(part.parent_pools))):
            raise ValueError('Spectral reference requires one exact-source pool per original cell')
        expected = {(y*nx+x, y*nx+(x+1)%nx, 0) for y in range(ny) for x in range(nx)}
        expected |= {(y*nx+x, ((y+1)%ny)*nx+x, 1) for y in range(ny) for x in range(nx)}
        observed = [(l, r, axis) for l, r, axis, _ in part.patch.faces]
        if len(observed) != 2*nx*ny or set(observed) != expected:
            raise ValueError('Spectral reference requires both original periodic boundaries')
        for pool, cell in zip(part.pools, part.patch.cells):
            form = pool['form']
            eta = F(form['datum'])+F(float(form['stage_offset']))
            if (set(pool['source_triangle_indices']) != set(cell.source_triangle_indices)
                    or any(eta <= v[2] for fragment in cell.fragments for v in fragment.polygon)):
                raise ValueError('Spectral reference requires fully wet original source support')
        dx, dy = part.patch.spacing
        depth = float(np.sum(system.h))/(nx*ny*dx*dy)
        kx = np.sin(2*np.pi*np.fft.fftfreq(nx))/dx
        ky = np.sin(2*np.pi*np.fft.fftfreq(ny))/dy
        for frequency in (kx, ky):
            frequency[0] = 0.
            if len(frequency) % 2 == 0:
                frequency[len(frequency)//2] = 0.  # Exact centered Nyquist null.
        y, x = np.meshgrid(ky, kx, indexing='ij')
        k = np.stack((x, y), axis=-1)
        magnitude = np.linalg.norm(k, axis=-1)
        self.unit = np.divide(k, magnitude[..., None], out=np.zeros_like(k),
                              where=magnitude[..., None] > 0)
        squared = (np.sqrt(system.length)*depth*magnitude)**2
        if not np.isfinite(squared).all():
            raise ValueError('Spectral reference exceeds represented range')
        self.longitudinal = 1/(1+squared)
        self.shape = (ny, nx, 2)

    def apply(self, residual):
        transformed = np.fft.fft2(residual.reshape(self.shape), axes=(0, 1))
        parallel = np.sum(self.unit*transformed, axis=-1)
        # Orthogonal directions retain eigenvalue one; the longitudinal
        # eigenvalue is strictly positive. Same real symmetric map each CG step.
        result = transformed+(self.longitudinal-1)[..., None]*self.unit*parallel[..., None]
        value = np.fft.ifft2(result, axes=(0, 1)).real.reshape(residual.shape)
        if not np.isfinite(value).all():
            raise ValueError('Spectral reference solve exceeds represented range')
        return value
