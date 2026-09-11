"""Compare nested reconstruction grids without mistaking density for an SDF."""
import argparse
from collections import deque
import json
from pathlib import Path
import numpy as np
from liquid_anisotropic_surface import upper_surface


def main_liquid_body(density, level=.5):
    """Six-connected liquid components; retain detached liquid as a diagnostic.

    This analysis does not delete particles or change the renderer. Components
    touching only at a corner are not considered a resolved fluid connection.
    """
    wet = np.asarray(density) >= level
    nz, ny, nx = wet.shape
    labels = np.zeros(wet.size, dtype=np.int32)
    mask = wet.ravel()
    sizes = [0]
    plane = nx*ny
    for seed in np.flatnonzero(mask):
        if labels[seed]:
            continue
        label = len(sizes)
        labels[seed] = label
        queue = deque([int(seed)])
        count = 0
        while queue:
            i = queue.popleft()
            count += 1
            z, remainder = divmod(i, plane)
            y, x = divmod(remainder, nx)
            for enabled, j in ((x > 0, i-1), (x+1 < nx, i+1),
                               (y > 0, i-nx), (y+1 < ny, i+nx),
                               (z > 0, i-plane), (z+1 < nz, i+plane)):
                if enabled and mask[j] and not labels[j]:
                    labels[j] = label
                    queue.append(j)
        sizes.append(count)
    largest = int(np.argmax(sizes))
    body = (labels.reshape(wet.shape) == largest) & wet
    # Preserve the original air samples beside the retained interface, which
    # keeps the subvoxel interpolation valid. Remove other components only in
    # this diagnostic copy; disconnected components are not renderer errors.
    field = np.where(wet & ~body, 0., density)
    return field, dict(component_count=len(sizes)-1, main_body_voxels=int(body.sum()),
                       detached_liquid_voxels=int(wet.sum()-body.sum()))


def compare(coarse, fine):
    for name in ('minimum', 'extent', 'centers', 'matrix', 'sample_volumes'):
        if not np.allclose(coarse[name], fine[name], rtol=0, atol=1e-12):
            raise ValueError(f'Reconstruction input differs: {name}')
    cshape, fshape = np.array(coarse['density'].shape), np.array(fine['density'].shape)
    if np.any(fshape != cshape*2):
        raise ValueError('Exactly two-times finer nested XYZ grid required')
    a = upper_surface(coarse['density'], coarse['minimum'], coarse['extent'])
    b = upper_surface(fine['density'], fine['minimum'], fine['extent'])
    # Fine centers are symmetric about coarse centers. Mean only complete
    # 2x2 neighborhoods; do not fill missing surface crossings at shorelines.
    b = b.reshape(a.shape[0], 2, a.shape[1], 2).mean(axis=(1, 3))
    valid = np.isfinite(a) & np.isfinite(b)
    difference = b[valid]-a[valid]
    if not len(difference):
        raise ValueError('No common upper-surface crossings')
    cv = np.prod(coarse['extent']/coarse['cells'])
    fv = np.prod(fine['extent']/fine['cells'])
    coarse_volume = float((coarse['density'] >= .5).sum()*cv)
    fine_volume = float((fine['density'] >= .5).sum()*fv)
    body_fields = [main_liquid_body(data['density']) for data in (coarse, fine)]
    ca, fb = [upper_surface(field, coarse['minimum'], coarse['extent']) for field, _ in body_fields]
    fb = fb.reshape(ca.shape[0], 2, ca.shape[1], 2).mean(axis=(1, 3))
    body_valid = np.isfinite(ca) & np.isfinite(fb)
    body_change = fb[body_valid]-ca[body_valid]
    return dict(common_columns=int(valid.sum()),
                coarse_only_columns=int((np.isfinite(a) & ~np.isfinite(b)).sum()),
                fine_only_columns=int((~np.isfinite(a) & np.isfinite(b)).sum()),
                height_change_mean_m=float(difference.mean()),
                height_change_rms_m=float(np.sqrt(np.mean(difference**2))),
                absolute_height_change_percentiles_m=np.percentile(abs(difference), [50, 95, 99, 100]).tolist(),
                iso_05_volume_m3=[coarse_volume, fine_volume],
                iso_05_volume_relative_change=(fine_volume-coarse_volume)/coarse_volume,
                components=[stats for _, stats in body_fields],
                main_body_common_columns=int(body_valid.sum()),
                main_body_height_change_rms_m=float(np.sqrt(np.mean(body_change**2))) if len(body_change) else None,
                main_body_absolute_height_change_percentiles_m=np.percentile(abs(body_change), [50, 95, 99, 100]).tolist() if len(body_change) else None,
                renderer_integrated=False, frame_performance_measured=False,
                visual_or_physical_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('coarse', type=Path)
    parser.add_argument('fine', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    with np.load(args.coarse) as coarse, np.load(args.fine) as fine:
        report = compare(coarse, fine)
    report.update(coarse=str(args.coarse.resolve()), fine=str(args.fine.resolve()))
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
