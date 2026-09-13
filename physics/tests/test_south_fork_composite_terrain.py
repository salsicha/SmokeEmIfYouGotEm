import importlib.util
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('composite', ROOT/'physics/scripts/south_fork_composite_terrain.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def rectangle(x0, y0, x1, y1, nx, ny):
    x, y = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y1, y0, ny))
    xyz = np.stack((x, y, 2*x+3*y), axis=-1)
    return [xyz[0], xyz[:, -1], xyz[-1, ::-1], xyz[::-1, 0]]


def test_seam_preserves_all_boundary_vertices_and_has_no_holes_or_overlap():
    inner, outer = rectangle(2, 2, 8, 8, 13, 17), rectangle(0, 0, 10, 10, 6, 6)
    xyz, faces = MODULE.stitch_rectangular_boundaries(inner, outer)
    expected = set(tuple(p) for edge in inner+outer for p in edge)
    assert set(map(tuple, xyz)) == expected
    p, q, r = xyz[faces[:, 0]], xyz[faces[:, 1]], xyz[faces[:, 2]]
    twice_area = (q[:, 0]-p[:, 0])*(r[:, 1]-p[:, 1])-(q[:, 1]-p[:, 1])*(r[:, 0]-p[:, 0])
    assert np.all(twice_area > 0) and abs(twice_area.sum()*.5-64) < 1e-12
    edges, counts = np.unique(np.sort(faces[:, [[0, 1], [1, 2], [2, 0]]].reshape(-1, 2), axis=1), axis=0, return_counts=True)
    assert counts.max() == 2 and len(xyz)-len(edges)+len(faces) == 0
    assert (counts == 1).sum() == len(expected)
    centroid = xyz[faces].mean(axis=1)
    assert np.allclose(MODULE.sample_triangles(xyz, faces, centroid[:, 0], centroid[:, 1]), centroid[:, 2], atol=1e-12)


def test_seam_has_no_inside_or_outside_fallback():
    xyz, faces = MODULE.stitch_rectangular_boundaries(rectangle(2, 2, 8, 8, 4, 4), rectangle(0, 0, 10, 10, 3, 3))
    for x, y in [(5., 5.), (11., 5.)]:
        try:
            MODULE.sample_triangles(xyz, faces, x, y)
        except ValueError:
            continue
        raise AssertionError('Seam extrapolated into another terrain owner')


def test_coarse_sampler_is_render_triangle_not_bilinear():
    z = np.array([[0., 0.], [0., 4.]])
    assert MODULE.sample_regular_triangles(z, 0., 1., 1., .5, .5) == 0
    assert MODULE.sample_regular_triangles(z, 0., 1., 1., .75, .25) == 2
    for x, y in [(-1., .5), (2., 0.)]:
        try:
            MODULE.sample_regular_triangles(z, 0., 1., 1., x, y)
        except ValueError:
            continue
        raise AssertionError('Coarse sampler extrapolated')


def test_replacement_removes_exact_coarse_quads_and_rejects_unaligned_cut():
    z = np.zeros((6, 6))
    mask = MODULE.coarse_quad_mask(z, 0, 5, 1, [1, 1, 4, 4])
    assert mask.sum() == 16 and not mask[1:4, 1:4].any()
    for bounds in ([1.5, 1, 4, 4], [-1, 1, 4, 4]):
        try:
            MODULE.coarse_quad_mask(z, 0, 5, 1, bounds)
        except ValueError:
            continue
        raise AssertionError('Unsafe source cut accepted')


def test_streamed_tiles_keep_all_source_triangles_and_shared_edges_exact():
    z = np.arange(42, dtype=np.float32).reshape(6, 7)*.1
    mask = np.ones((5, 6), dtype=bool)
    mask[1:3, 2:4] = False
    tiles = list(MODULE.coarse_mesh_tiles(z, mask, 100, 200, 2, 120, tile_quads=2))
    assert sum(len(t['triangles']) for t in tiles) == mask.sum()*2
    by_source = {}
    for tile in tiles:
        world = tile['xyz_local_m'] + np.r_[tile['origin_utm_m'], 120]
        for index, point in zip(tile['source_grid_vertex_index'], world):
            r, c = divmod(int(index), z.shape[1])
            expected = np.array([100+c*2, 200-r*2, float(z[r, c])])
            assert np.array_equal(point, expected)
            if index in by_source:
                assert np.array_equal(point, by_source[index])
            by_source[index] = point
