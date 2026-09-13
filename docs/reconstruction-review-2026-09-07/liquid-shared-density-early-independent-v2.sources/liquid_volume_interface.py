"""Conserved-volume tent kernel surface reference, not a native solver change.

The zero set of .5 - sum(Vp * Wp)/Vcell is a candidate liquid interface.
It is NOT signed distance and nonzero interpolation support is NOT full water.
This module deliberately does not repair thin sheets, tune the iso value to a
desired picture, or claim that particle volume implies resolved surface volume.
"""
import itertools
import numpy as np


def _grid(cells, spacing):
    c = np.asarray(cells, dtype=float)
    h = np.asarray(spacing, dtype=float)
    if (c.shape != (3,) or h.shape != (3,) or not np.isfinite(c).all() or
            not np.isfinite(h).all() or (c < 2).any() or (c != np.floor(c)).any() or
            (h <= 0).any()):
        raise ValueError('Integer XYZ grid counts and positive metric spacing required')
    return c.astype(int), h


def deposit_volume(points, cells, spacing, particle_volume):
    """Deposit fixed-volume particles, in metres from the grid's lower corner.

    A sample at i+.5 receives the same centred trilinear tent as native P2G.
    Off-grid weights are reported as loss, never renormalized into the domain.
    """
    cells, spacing = _grid(cells, spacing)
    points = np.asarray(points, dtype=float)
    if (points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all() or
            not np.isfinite(particle_volume) or particle_volume <= 0):
        raise ValueError('Finite Nx3 positions and positive nominal volume required')
    flat = np.zeros(int(np.prod(cells)))
    for first in range(0, len(points), 65536):
        q = points[first:first+65536]/spacing-.5
        low = np.floor(q).astype(int)
        for offset in itertools.product((0, 1), repeat=3):
            index = low+offset
            selected = np.all((index >= 0) & (index < cells), axis=1)
            i = index[selected]
            weight = np.prod(1-np.abs(q[selected]-i), axis=1)
            address = (i[:, 2]*cells[1]+i[:, 1])*cells[0]+i[:, 0]
            np.add.at(flat, address, particle_volume*weight)
    return flat.reshape(tuple(cells[::-1]))


def sample_centred(field, points, spacing):
    """Trilinear sample; any stencil outside the captured grid is invalid.

    No clamped address or zero extrapolation may silently hide unsupported
    particles at physical boundaries. Returns values and a validity mask.
    """
    field, points = np.asarray(field, float), np.asarray(points, float)
    if field.ndim != 3 or not np.isfinite(field).all():
        raise ValueError('Finite ZYX scalar grid required')
    cells, spacing = _grid(field.shape[::-1], spacing)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError('Finite Nx3 sample points required')
    q = points/spacing-.5
    low = np.floor(q).astype(int)
    valid = np.all((low >= 0) & (low+1 < cells), axis=1)
    values = np.full(len(points), np.nan)
    values[valid] = 0
    for offset in itertools.product((0, 1), repeat=3):
        i = low[valid]+offset
        weight = np.prod(1-np.abs(q[valid]-i), axis=1)
        values[valid] += weight*field[i[:, 2], i[:, 1], i[:, 0]]
    return values, valid


def implicit_from_volume(mass, spacing):
    mass = np.asarray(mass, dtype=float)
    if mass.ndim != 3 or not np.isfinite(mass).all() or (mass < 0).any():
        raise ValueError('Finite nonnegative ZYX deposited particle volume required')
    _, spacing = _grid(mass.shape[::-1], spacing)
    return .5-mass/np.prod(spacing)


def measure_interface(mass, spacing, particles, physical_mask=None):
    phi = implicit_from_volume(mass, spacing)
    selected = np.ones(phi.shape, bool) if physical_mask is None else np.asarray(physical_mask)
    if selected.shape != phi.shape or selected.dtype != bool:
        raise ValueError('Matching boolean physical owner mask required')
    sample, valid = sample_centred(phi, particles, spacing)
    dry_particles = valid & (sample > 0)
    water = phi <= 0
    cell_volume = float(np.prod(spacing))
    address = np.floor(np.asarray(particles)/spacing).astype(int)
    inside = np.all((address >= 0) & (address < np.asarray(phi.shape[::-1])), axis=1)
    columns = np.unique(address[inside, :2], axis=0)
    columns_missing = ~(water & selected).any(0)[columns[:, 1], columns[:, 0]]
    return dict(particle_count=len(particles), sampled_particles=int(valid.sum()),
                particles_without_complete_stencil=int((~valid).sum()),
                particles_outside_candidate_interface=int(dry_particles.sum()),
                sampled_particles_outside_fraction=float(dry_particles.sum()/valid.sum()) if valid.any() else None,
                deposited_volume_m3=float(np.asarray(mass)[selected].sum()),
                candidate_wet_cell_count=int((water & selected).sum()),
                candidate_centre_classified_volume_m3=float((water & selected).sum()*cell_volume),
                supported_cell_count=int(((mass > 0) & selected).sum()),
                supported_columns_without_candidate_water=int((((mass*selected).sum(0)>0) & ~(water & selected).any(0)).sum()),
                particle_occupied_columns=int(len(columns)),
                particle_occupied_columns_without_candidate_water=int(columns_missing.sum()),
                maximum_density=float((.5-phi)[selected].max(initial=0)),
                candidate_isovalue=.5, scalar_is_signed_distance=False,
                centre_classified_volume_is_not_integrated_surface_volume=True)
