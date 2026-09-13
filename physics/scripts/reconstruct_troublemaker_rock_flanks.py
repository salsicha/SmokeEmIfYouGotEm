"""Reconstruct only inferred rock-to-bed connecting faces, with fixed captures.

The two-metre support band is an explicit geometric prior, not measured
bathymetry or a surveyed boulder outline. A bounded, bed-obstacle harmonic
extension removes the one-cell extrusion implicit in the original builder.
Render, collision and hydraulics must consume this same revised triangle mesh.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT/'tmp/troublemaker-sparse-rock-support-20260912'


def extend_fixed_surface(xyz, faces, editable, tolerance=1e-6, max_iterations=4000):
    """Weighted graph harmonic extension above the unchanged original bed.

    Every noneditable node is a Dirichlet constraint. Positive inverse-square
    edge weights retain the maximum principle on irregular registered XY.
    This changes heights only; connectivity and captured XYZ are immutable.
    """
    xyz = np.asarray(xyz, dtype=float)
    faces = np.asarray(faces)
    editable = np.asarray(editable, dtype=bool)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or editable.shape != (len(xyz),):
        raise ValueError('Matching XYZ and editable mask required')
    if not np.isfinite(xyz).all() or tolerance <= 0 or max_iterations < 1:
        raise ValueError('Finite geometry and positive convergence limits required')
    if faces.ndim != 2 or faces.shape[1] != 3 or not np.issubdtype(faces.dtype, np.integer):
        raise ValueError('Integer triangle connectivity required')
    if faces.size and (faces.min() < 0 or faces.max() >= len(xyz)):
        raise ValueError('Triangle index outside geometry')
    nodes = np.flatnonzero(editable)
    z = xyz[:, 2].copy()
    if not len(nodes):
        return z, dict(iterations=0, maximum_update_m=0., maximum_residual_m=0.)
    selected = faces[np.any(editable[faces], axis=1)]
    edges = np.concatenate((selected[:, [0, 1]], selected[:, [1, 2]], selected[:, [2, 0]]))
    edges = np.unique(np.sort(edges, axis=1), axis=0)
    directed = np.concatenate((edges, edges[:, ::-1]))
    directed = directed[editable[directed[:, 0]]]
    lengths2 = np.sum((xyz[directed[:, 0], :2]-xyz[directed[:, 1], :2])**2, axis=1)
    if np.any(lengths2 <= 1e-12):
        raise ValueError('Degenerate horizontal edge')
    row_map = np.full(len(xyz), -1, dtype=np.int64)
    row_map[nodes] = np.arange(len(nodes))
    row = row_map[directed[:, 0]]
    neighbour = directed[:, 1]
    weights = 1./lengths2
    sums = np.bincount(row, weights=weights, minlength=len(nodes))
    if np.any(sums <= 0):
        raise ValueError('Unconnected editable vertex')
    floor = z[nodes].copy()

    def update():
        average = np.bincount(row, weights=weights*z[neighbour], minlength=len(nodes))/sums
        return np.maximum(floor, average)

    for iteration in range(1, max_iterations+1):
        proposed = update()
        maximum = float(np.max(abs(proposed-z[nodes])))
        z[nodes] = proposed
        if maximum <= tolerance:
            break
    else:
        raise ValueError(f'Flank interpolation did not converge in {max_iterations} iterations')
    residual = float(np.max(abs(update()-z[nodes])))
    assert np.array_equal(z[~editable], xyz[~editable, 2])
    assert np.all(z >= xyz[:, 2]) and z.max() <= xyz[:, 2].max()+1e-9
    return z, dict(iterations=iteration, maximum_update_m=maximum, maximum_residual_m=residual)


def main():
    from scipy.spatial import cKDTree
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--support-band-m', type=float, default=2.)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output.exists():
        raise ValueError('Fresh project-local output required')
    if not np.isfinite(args.support_band_m) or not 0 < args.support_band_m <= 2.:
        raise ValueError('The unmeasured support prior must remain within two metres')
    parent = json.loads((PARENT/'manifest.json').read_text())
    original_path = PARENT/'registered_mesh_source.npz'
    assert hashlib.sha256(original_path.read_bytes()).hexdigest() == parent['mesh_sha256']
    with np.load(original_path) as data:
        mesh = {key: data[key].copy() for key in data.files}
    original_z = mesh['z_m'].copy()
    authority = mesh['authority'].ravel().copy()
    xyz = np.column_stack([mesh[k].ravel() for k in ('east_m', 'north_m', 'z_m')])
    distance, _ = cKDTree(xyz[authority == 3, :2]).query(xyz[:, :2])
    editable = (authority == 2) & (distance <= args.support_band_m)
    z, stats = extend_fixed_surface(xyz, mesh['triangles'], editable)
    changed = z-xyz[:, 2] > 1e-5
    # Retain original precision and avoid changing cells solely by roundoff.
    mesh['z_m'].ravel()[changed] = z[changed]
    mesh['authority'].ravel()[changed] = 5  # inferred connecting flank, NOT a captured return
    protected = np.isin(authority, [1, 3, 4])
    assert np.array_equal(mesh['z_m'].ravel()[protected], original_z.ravel()[protected])
    assert np.all(distance[changed] <= args.support_band_m)
    output.mkdir()
    path = output/'registered_mesh_source.npz'
    np.savez_compressed(path, **mesh)
    report = dict(parent)
    report.update(mesh_path=path.relative_to(ROOT).as_posix(),
        mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        parent_mesh_path=original_path.relative_to(ROOT).as_posix(), parent_mesh_sha256=parent['mesh_sha256'],
        all_recorded_heights_unchanged=False,
        original_measured_ground_and_rock_xyz_unchanged=True,
        faces_between_returns_authority='Inferred weighted harmonic extension above prior bed, fixed captured XYZ; not surveyed rock flanks.',
        flank_reconstruction=dict(support_band_prior_m=args.support_band_m,
            authority_code=5, changed_vertices=int(changed.sum()),
            maximum_height_change_m=float((mesh['z_m']-original_z).max()),
            mean_changed_height_m=float((mesh['z_m']-original_z).ravel()[changed].mean()),
            **stats),
        hydraulic_validation_passed=False, game_integrated=False, production_promoted=False)
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['flank_reconstruction'], indent=2))


if __name__ == '__main__':
    main()
