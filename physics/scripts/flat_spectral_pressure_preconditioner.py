"""SPD frozen-depth FFT preconditioner, never a replacement pressure solve.

Constant flat Q=h^2*k*k^T is rank one at each centered-difference frequency.
Variable depth still uses the complete original matrix at every CG iteration.
Only positive periodic flat full-dispersion research systems are supported.
"""
import numpy as np


def precondition(system, residual):
    g = system.geometry
    if (not g.periodic or np.any(g.h <= 0) or not np.all(g.bed == g.bed.flat[0])
            or not np.all(system.fraction == 1)):
        raise ValueError('Spectral preconditioner requires positive periodic flat full dispersion')
    r = system._vector(residual)
    if not hasattr(system, '_flat_spectral_symbol'):
        frequencies = []
        for n in g.h.shape:
            k = np.sin(2*np.pi*np.fft.fftfreq(n))/g.dx
            k[0] = 0.
            if n % 2 == 0:
                k[n//2] = 0.  # Exact centered-difference Nyquist null.
            frequencies.append(k)
        ky, kx = np.meshgrid(*frequencies, indexing='ij')
        k = np.stack((kx, ky), axis=-1)
        frozen_depth = float(np.mean(g.h))
        coefficient = system.length*frozen_depth*frozen_depth
        denominator = 1+coefficient*np.sum(k*k, axis=-1)
        if not np.isfinite(coefficient) or not np.isfinite(denominator).all():
            raise ValueError('Frozen spectral preconditioner exceeds represented range')
        system._flat_spectral_symbol = k, coefficient/denominator
    k, factor = system._flat_spectral_symbol
    transformed = np.fft.fftn(r, axes=(0, 1))
    longitudinal = np.sum(k*transformed, axis=-1)
    result = np.fft.ifftn(transformed-factor[..., None]*k*longitudinal[..., None], axes=(0, 1)).real
    if not np.isfinite(result).all():
        raise ValueError('Spectral preconditioner exceeds represented range')
    return result
