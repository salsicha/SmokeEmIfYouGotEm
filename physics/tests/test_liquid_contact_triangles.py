import json
import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build_south_fork_liquid_contact import sample_packed
from south_fork_registered_mesh import RegisteredMeshSampler


class RegisteredLiquidContactTest(unittest.TestCase):
    def test_quad_relative_encoding_at_large_world_coordinates(self):
        packed=[[10000.,4000.,50.],[50.,1.,1.],
                [0,0,100],[50,0,125],[0,-50,150],
                [50,0,125],[50,-50,175],[0,-50,150]]
        points=np.array([[10012.5,3987.5],[10037.5,3962.5]],dtype=np.float32)
        expected=100+.5*(points[:,0]-10000)-(points[:,1]-4000)
        np.testing.assert_allclose(sample_packed(packed,points,relative_vertices=True),expected,atol=1e-5)
        self.assertTrue(np.isnan(sample_packed(packed,[[0,0]],relative_vertices=True)).all())

    def test_packed_query_matches_original_triangles(self):
        root = Path(__file__).resolve().parents[2]
        directory = root/'unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908'
        profile = json.loads((directory/'triangle_contact_profile.json').read_text())
        window = json.loads((directory/'manifest.json').read_text())
        geometry = json.loads((root/window['source_geometry_manifest']).read_text())
        sampler = RegisteredMeshSampler(np.load(root/geometry['mesh_path']))
        # Includes off-seed locations; query coordinates use the GPU's float32.
        points = np.random.default_rng(218).uniform(-1500, 1500, (30000, 2)).astype(np.float32)
        expected = sampler.sample(points[:, 0]/100., points[:, 1]/100.)*100
        actual = sample_packed(profile['packed_vectors'], points)
        self.assertTrue(np.isfinite(actual).all())
        self.assertLess(float(np.max(abs(expected-actual))), .01)
        self.assertTrue(np.isnan(sample_packed(profile['packed_vectors'], [[100000, 100000]])).all())


if __name__ == '__main__':
    unittest.main()
