"""Native stage boundary for the registered collocated GPU review fixture."""
import numpy as np


def outlet_pressure_grid(profile):
    packed = np.asarray(profile['packed_vectors'], dtype=float)
    if packed.shape != (260, 3) or not np.isfinite(packed).all():
        raise ValueError('Complete finite native boundary profile required')
    dx, half, floor = packed[2]
    dz, count, nz = packed[3]
    if not np.allclose([dx, half, floor, dz, count, nz], [32.8125, 1050, 350, 800/24, 64, 24]):
        raise ValueError('Registered fixture dimensions changed')
    z, y, x = np.meshgrid(floor+(np.arange(24)+.5)*dz,
                          (np.arange(68)+.5)*dx-1115.625,
                          (np.arange(68)+.5)*dx-1115.625, indexing='ij')
    known = np.zeros(x.shape, dtype=bool)
    pressure = np.zeros(x.shape)
    for face in range(4):
        if face < 2:
            mask = (abs(y) < half) & ((x <= -half) if face == 0 else (x >= half))
            along = y
        else:
            mask = (abs(x) < half) & ((y <= -half) if face == 2 else (y >= half))
            along = x
        column = np.clip(np.floor((along+half)/dx).astype(int), 0, 63)
        rows = packed[4+face*64+column]
        selected = mask & (rows[..., 2] < 0) & (z > rows[..., 0])
        known |= selected
        pressure[selected] = 980*np.maximum(rows[..., 1]-z, 0)[selected]
    return known, pressure
