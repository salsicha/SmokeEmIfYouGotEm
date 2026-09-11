"""Reference anisotropic density reconstruction; never changes simulated positions.

Weighted covariance/center filtering follows Yu & Turk (SCA2010), equations6-16.
Scale adaptation: use the analytic covariance .15*r^2 of a uniform 3D ball with
weight 1-(distance/r)^3, rather than their example's unit-dependent ks=1400.
FLIP particle volume is an explicit assumption, not a calibrated mass budget.
"""
from itertools import product
from pathlib import Path
import argparse
import hashlib
import json
import time
import numpy as np


def fit_kernels(positions, radius, smoothing=.9, max_ratio=4., min_neighbors=25, smooth_sparse=False):
    points = np.asarray(positions, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or not len(points) or not np.isfinite(points).all():
        raise ValueError('Finite nonempty XYZ particle positions required')
    if not np.isfinite([radius, smoothing, max_ratio]).all() or radius <= 0 or not 0 <= smoothing <= 1 or max_ratio < 1 or min_neighbors < 1:
        raise ValueError('Invalid reconstruction controls')
    support = 2*radius
    cells = np.floor(points/support).astype(np.int64)
    bins = {}
    for i, key in enumerate(map(tuple, cells)):
        bins.setdefault(key, []).append(i)
    centers = np.empty_like(points)
    covariance = np.empty((len(points), 3, 3))
    counts = np.empty(len(points), dtype=int)
    number_density = np.empty(len(points))
    support_weight = np.empty(len(points))
    offsets = list(product((-1, 0, 1), repeat=3))
    for key, indices in bins.items():
        adjacent = [bins.get(tuple(k+d for k, d in zip(key, offset)), []) for offset in offsets]
        nearby = points[[i for group in adjacent for i in group]]
        for start in range(0, len(indices), 64):
            batch = np.asarray(indices[start:start+64])
            delta = nearby[None, :, :]-points[batch, None, :]
            q = np.linalg.norm(delta, axis=-1)/support
            weights = np.maximum(1-q**3, 0)
            total = weights.sum(axis=1)
            support_weight[batch] = total
            mean = np.einsum('ij,ijk->ik', weights, delta)/total[:, None]
            covariance[batch] = (np.einsum('ij,ijk,ijl->ikl', weights, delta, delta)/total[:, None, None]
                                 - mean[:, :, None]*mean[:, None, :])
            centers[batch] = points[batch]+smoothing*mean
            counts[batch] = (q < 1).sum(axis=1)
            # Equal-mass version of eq.1: m/rho = 1/sum(W). Evaluate
            # at the original positions, not the render-only shifted centers.
            number_density[batch] = cubic_kernel(2*q).sum(axis=1)/radius**3
    eigenvalues, basis = np.linalg.eigh(covariance)
    degenerate = eigenvalues[:, -1] <= radius**2*1e-10
    # Positive-definite, bounded aspect ratio, with spherical sparse fallback.
    eigenvalues = np.maximum(eigenvalues, np.maximum(eigenvalues[:, -1:]/max_ratio, radius**2*1e-12))
    scale = eigenvalues/(.15*support**2)
    sparse = (counts <= min_neighbors) | degenerate
    confidence=np.clip((support_weight-1-8)/16,0,1)
    confidence=confidence*confidence*(3-2*confidence)
    confidence[degenerate]=0
    if smooth_sparse:
        # A neighbor crossing the support boundary has zero weight. A raw
        # integer-count branch instead changes an entire kernel discontinuously.
        # This authored transition leaves quadrature mass and positions intact.
        scale=.5+(scale-.5)*confidence[:,None]
        centers=points+(centers-points)*confidence[:,None]
    else:
        scale[sparse] = .5
    # Isolated spray must not be pulled toward unrelated nearby particles.
    # The paper's single smoothing step is retained for nonsparse liquid only.
    if not smooth_sparse:centers[sparse] = points[sparse]
    axes = radius*scale
    matrix = np.einsum('nik,nk,njk->nij', basis, 1/axes, basis)
    return dict(centers=centers, matrix=matrix, axes=axes, basis=basis,
                neighbor_counts=counts, sparse=sparse, degenerate=degenerate,
                sample_volumes=1/number_density,support_weight=support_weight,sparse_confidence=confidence)


def cubic_kernel(q):
    """Unit-support, normalized3D cubic spline radial factor; multiply det(G)."""
    q = np.asarray(q, dtype=float)
    return 8/np.pi*np.where(q < .5, 1-6*q*q+6*q*q*q,
                           np.where(q < 1, 2*(1-q)**3, 0))


def filter_kernels(kernels, footprint):
    """Moment-matched isotropic voxel prefilter, without moving centers.

    The normalized unit-support cubic has covariance .075 I. A box of width
    footprint has covariance footprint^2/12 I. Convolution adds covariances;
    reproduce that second moment with a broadened normalized cubic ellipsoid.
    This is an approximation of box convolution, not an exact box integral.
    The world-space footprint is explicit and may be held fixed when testing
    raster convergence. Kernel integral and particle quadrature weights stay
    unchanged; this does not conserve the volume of a selected isosurface.
    """
    if not np.isfinite(footprint) or footprint < 0:
        raise ValueError('Finite nonnegative metric footprint required')
    axes = np.sqrt(kernels['axes']**2+footprint**2/(12*.075))
    matrix = np.einsum('nik,nk,njk->nij', kernels['basis'], 1/axes, kernels['basis'])
    return dict(kernels, axes=axes, matrix=matrix)


def splat_density(kernels, particle_volume, minimum, extent, cells):
    minimum, extent = np.asarray(minimum, dtype=float), np.asarray(extent, dtype=float)
    cells = np.asarray(cells, dtype=int)
    volumes = np.asarray(particle_volume, dtype=float)
    if minimum.shape != (3,) or extent.shape != (3,) or cells.shape != (3,) or not np.isfinite([*minimum, *extent]).all() or (extent <= 0).any() or (cells <= 0).any() or not np.isfinite(volumes).all() or (volumes <= 0).any() or volumes.shape not in ((), (len(kernels['centers']),)):
        raise ValueError('Positive metric grid and particle volume required')
    volumes = np.broadcast_to(volumes, (len(kernels['centers']),))
    spacing = extent/cells
    result = np.zeros(tuple(cells[::-1]), dtype=float)
    flat = result.ravel()
    for center, matrix, axes, basis, volume in zip(kernels['centers'], kernels['matrix'], kernels['axes'], kernels['basis'], volumes):
        # Exact ellipsoid AABB: never truncate a stretched kernel to a sphere.
        bounds = np.sqrt(np.sum((basis*axes[None, :])**2, axis=1))
        lo = np.maximum(np.ceil((center-bounds-minimum)/spacing-.5).astype(int), 0)
        hi = np.minimum(np.floor((center+bounds-minimum)/spacing-.5).astype(int), cells-1)
        if np.any(lo > hi):
            continue
        z, y, x = np.meshgrid(np.arange(lo[2], hi[2]+1), np.arange(lo[1], hi[1]+1), np.arange(lo[0], hi[0]+1), indexing='ij')
        index = np.stack((x, y, z), axis=-1).reshape(-1, 3)
        delta = minimum+(index+.5)*spacing-center
        q = np.linalg.norm(delta@matrix.T, axis=1)
        value = volume*np.linalg.det(matrix)*cubic_kernel(q)
        linear = index[:, 0]+cells[0]*(index[:, 1]+cells[1]*index[:, 2])
        flat[linear] += value
    return result


def upper_surface(density, minimum, extent, level=.5):
    """Highest interior liquid-to-air crossing, in meters. No crossing => NaN.

    Boundary-clipped columns are not silently treated as a free surface.
    Linear interpolation uses voxel centers and works for anisotropic spacing.
    """
    density = np.asarray(density, dtype=float)
    if density.ndim != 3 or density.shape[0] < 2 or not np.isfinite(density).all():
        raise ValueError('Finite ZYX density volume required')
    crossings = (density[:-1] >= level) & (density[1:] < level)
    has = crossings.any(axis=0) & (density[-1] < level)
    z = density.shape[0]-2-np.argmax(crossings[::-1], axis=0)
    y, x = np.indices(z.shape)
    below, above = density[z, y, x], density[z+1, y, x]
    fraction = np.divide(below-level, below-above, out=np.zeros_like(below), where=below != above)
    height = minimum[2]+(z+.5+fraction)*extent[2]/density.shape[0]
    return np.where(has, height, np.nan)


def run_capture(source, output, radius, particle_volume, density_normalized=False, grid_refinement=1, smoothing=.9, footprint=0):
    if output.exists():
        raise FileExistsError(output)
    data = json.loads(source.read_text())
    emitters = [e for e in data['emitters'] if e.get('position_count', 0)]
    if len(emitters) != 1 or emitters[0]['particle_rows_columns'] != 'unique_id,source_index,local_x_cm,local_y_cm,local_z_cm,local_vx_cm_s,local_vy_cm_s,local_vz_cm_s':
        raise ValueError('One unambiguous actual GPU particle readback required')
    points = np.asarray(emitters[0]['particle_rows'], dtype=float)[:, 2:5]/100
    start = time.perf_counter()
    kernels = fit_kernels(points, radius, smoothing=smoothing)
    kernels = filter_kernels(kernels, footprint)
    fit_seconds = time.perf_counter()-start
    # Local fixture z is0..8m; source Transform already subtracts world350cm.
    minimum, extent = (-11.15625, -11.15625, 0), (22.3125, 22.3125, 8)
    if grid_refinement not in (1, 2, 4):
        raise ValueError('Grid refinement must be 1, 2, or 4')
    cells = np.asarray((136, 136, 48))*grid_refinement
    volumes = kernels['sample_volumes'] if density_normalized else particle_volume
    density = splat_density(kernels, volumes, minimum, extent, cells)
    output.mkdir(parents=True)
    surface = upper_surface(density, minimum, extent)
    np.savez_compressed(output/'reconstruction.npz', **kernels, density=density, upper_surface=surface,
                        minimum=minimum, extent=extent, cells=cells)
    shift = np.linalg.norm(kernels['centers']-points, axis=1)
    report = dict(source=str(source.resolve()), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  particle_count=len(points), kernel_radius_m=radius, assumed_particle_volume_m3=particle_volume,
                  grid_cells=cells.tolist(),
                  center_smoothing=smoothing,
                  moment_matched_footprint_m=footprint,
                  fitted_seconds=fit_seconds, total_seconds=time.perf_counter()-start,
                  sparse_particles=int(kernels['sparse'].sum()),
                  degenerate_particles=int(kernels['degenerate'].sum()),
                  weighting='equal_mass_over_local_density' if density_normalized else 'constant_nominal_flip_volume',
                  sample_volume_percentiles_m3=np.percentile(kernels['sample_volumes'], [0, 50, 95, 100]).tolist(),
                  subvoxel_minor_axis_particles=int((kernels['axes'].min(axis=1) < max(np.asarray(extent)/cells)).sum()),
                  center_shift_percentiles_m=np.percentile(shift, [50, 95, 99, 100]).tolist(),
                  axis_range_m=[float(kernels['axes'].min()), float(kernels['axes'].max())],
                  max_axis_ratio=float((kernels['axes'].max(axis=1)/kernels['axes'].min(axis=1)).max()),
                  density_range=[float(density.min()), float(density.max())],
                  density_integral_m3=float(density.sum()*np.prod(np.asarray(extent)/cells)),
                  kernel_integral_before_grid_clipping_m3=float(np.broadcast_to(volumes, (len(points),)).sum()),
                  iso_05_voxel_volume_m3=float((density >= .5).sum()*np.prod(np.asarray(extent)/cells)),
                  upper_crossing_columns=int(np.isfinite(surface).sum()),
                  upper_crossing_height_percentiles_m=np.nanpercentile(surface, [0, 50, 95, 100]).tolist(),
                  source_positions_modified=False, renderer_integrated=False, physical_or_visual_acceptance=False,
                  deviations_from_paper=['Analytic unit-aware bulk covariance scale instead of example ks1400',
                      'Center averaging disabled to test surface-elevation preservation' if smoothing == 0 else 'Sparse/degenerate particle centers are not shifted',
                      'Equal-mass density estimated from FLIP positions, not supplied by SPH' if density_normalized else 'Explicit constant nominal FLIP volume instead of SPH mass/density'])
    if footprint:
        report['deviations_from_paper'].append('Moment-matched voxel prefilter added; not exact box convolution')
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--radius', type=float, required=True)
    parser.add_argument('--particle-volume', type=float, required=True)
    parser.add_argument('--density-normalized', action='store_true')
    parser.add_argument('--grid-refinement', type=int, choices=(1, 2, 4), default=1)
    parser.add_argument('--smoothing', type=float, default=.9)
    parser.add_argument('--footprint', type=float, default=0)
    args = parser.parse_args()
    run_capture(args.source, args.output, args.radius, args.particle_volume, args.density_normalized, args.grid_refinement, args.smoothing, args.footprint)
