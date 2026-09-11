"""Explicit physical and computational domains for native liquid handoff data.

The old 20 m geometry manifest described a 21 m native-face fixture. Keep that
one documented legacy case, never silently apply it to a new rectangle.
"""
import numpy as np


def layout(window, audit, physical_cells=None, vertical_cells=24):
    bounds=np.asarray(audit['local_station_lateral_face_bounds_m'],dtype=float)
    if bounds.shape!=(2,2) or not np.isfinite(bounds).all() or (bounds[1]<=bounds[0]).any():
        raise ValueError('Finite nonempty native face bounds required')
    extent=bounds[1]-bounds[0];centre=bounds.mean(axis=0)
    local=np.asarray(window['fluid_domain_local_bounds_m'],dtype=float)
    if local.shape!=(2,3) or not np.isfinite(local).all() or (local[1]<=local[0]).any():
        raise ValueError('Finite nonempty local XYZ domain required')
    declared_centre=np.asarray(window.get('centre_station_lateral_m',[0.,0.]))
    declared=local[:,:2]+declared_centre
    legacy=bool(np.array_equal(extent,[21.,21.]) and np.array_equal(centre,[0.,0.]) and
                np.array_equal(local,[[-10.,-10.,0.],[10.,10.,8.]]))
    if not legacy and not np.allclose(bounds,declared,rtol=0,atol=1e-9):
        raise ValueError('Native faces do not match the declared physical domain')
    if physical_cells is None:
        if not legacy:
            raise ValueError('Non-legacy domains require explicit physical cell counts')
        physical_cells=[64,64]
    counts=np.asarray(physical_cells,dtype=float)
    if counts.shape!=(2,) or not np.isfinite(counts).all() or (counts<2).any() or not np.array_equal(counts,np.rint(counts)):
        raise ValueError('Positive integer XY grid counts required')
    if not isinstance(vertical_cells,int) or vertical_cells<2:
        raise ValueError('Positive integer Z grid count required')
    counts=counts.astype(int);height=local[1,2]-local[0,2]
    spacing=np.r_[extent/counts,height/vertical_cells]
    cells=np.r_[counts,vertical_cells];computational=cells+np.array([4,4,0])
    # Explicit arithmetic estimates, not GPU memory or throughput measurements.
    legacy_fixture=bool(legacy and np.array_equal(counts,[64,64]) and vertical_cells==24)
    nominal_volume=(spacing[0]**3 if legacy_fixture
                    else float(np.prod(spacing)))/4
    return dict(native_face_bounds_m=bounds.tolist(),centre_station_lateral_m=centre.tolist(),
                physical_extents_m=[*extent.tolist(),float(height)],physical_cells=cells.tolist(),
                computational_cells=computational.tolist(),cell_size_m=spacing.tolist(),
                computational_extents_m=(computational*spacing).tolist(),
                nominal_particle_volume_m3=float(nominal_volume),particles_per_cell=4,
                legacy_fixture=legacy_fixture,grid_cell_count=int(np.prod(computational)),
                runtime_support_verified=False,performance_verified=False)
