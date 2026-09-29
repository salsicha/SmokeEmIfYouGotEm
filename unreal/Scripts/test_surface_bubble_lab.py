"""Small exact/invariant checks, run in Blender's bundled Python."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_surface_bubble_lab import evolve, cap_mesh, SPEED, SHEAR


single = np.array([[.11, -.005]])
positions, overlap = evolve(single, np.array([.001]), 10)
expected = single[0]+np.arange(73)[:, None]/24*np.array([SPEED+SHEAR*single[0, 1], 0.])
np.testing.assert_allclose(positions[:, 0], expected, atol=1e-13, rtol=0)
assert overlap == 0

pair = np.array([[.12, -.005], [.1182, -.0037]])
radii = np.array([.001, .001])
coarse, overlap = evolve(pair, radii, 10)
fine, _ = evolve(pair, radii, 20)
assert overlap <= 2e-8
assert np.min(np.linalg.norm(fine[:, 1]-fine[:, 0], axis=1)) >= .002-2e-8
assert np.max(np.linalg.norm(fine-coarse, axis=2)) < .00005
centroid = pair.mean(axis=0)
expected = centroid+np.arange(73)[:, None]/24*np.array([SPEED+SHEAR*centroid[1], 0.])
np.testing.assert_allclose(fine.mean(axis=1), expected, atol=1e-13, rtol=0)

mesh = cap_mesh(.001)
coords = np.array([v.co[:] for v in mesh.vertices])
assert abs(coords[:, 2].max()-.0004) < 1e-9
assert coords[:, 2].min() >= -1e-12
assert np.linalg.norm(coords[:, :2], axis=1).max() <= .001+1e-9
assert all(p.normal.z > 0 for p in mesh.polygons)
print('SURFACE_BUBBLE_TESTS_PASSED: isolated advection, non-overlap, timestep refinement, centroid transport, cap dimensions/normals', flush=True)
