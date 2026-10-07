import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from chilko_corridor_terrain import CorridorTerrain
from mosaic_lidarbc_crops import sha


class CorridorSamplerTests(unittest.TestCase):
    def make(self,root):
        rows=[]
        for x,y in ((0,0),(1,0),(0,1),(1,1)):
            west,south=x*2,y*2
            xx,yy=np.meshgrid(west+np.arange(2)+.5,south+2-np.arange(2)-.5)
            height=(xx+10*yy).astype(np.float32)
            kind=np.full(height.shape,1 if x==0 else 2,np.uint8)
            path=root/f'{x}_{y}.npz'
            np.savez(path,height_m=height,source_kind=kind,x0=float(west),y_top=float(south+2),cell_m=1.)
            rows.append(dict(cell=[x,y],bounds=[west,south,west+2,south+2],file=path.name,sha256=sha(path)))
        m=dict(schema='raftsim.chilko_corridor_terrain.v1',river_id='chilko_river_bc',
            horizontal_crs='EPSG:3157',vertical_reference='CGVD2013 (EPSG:6647)',cell_m=1.,tiles=rows)
        (root/'manifest.json').write_text(json.dumps(m))

    def test_bilinear_crosses_four_tiles_without_clamping_or_losing_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make(root);sampler=CorridorTerrain(root,cache_tiles=1)
            points=np.array([[2,2],[1.75,1.75],[2.25,2.25],[.5,.5],[3.5,3.5]])
            h,k=sampler.sample(points)
            np.testing.assert_allclose(h,points[:,0]+10*points[:,1])
            np.testing.assert_array_equal(k,[2,2,2,1,2])
            self.assertEqual(len(sampler.cache),1)

    def test_outer_edge_requires_actual_support_except_at_exact_pixel_center(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make(root);sampler=CorridorTerrain(root)
            h,k=sampler.sample([[.5,.5],[.49,.5],[3.51,3.5],[-20,3]])
            self.assertEqual(h[0],5.5);self.assertTrue(np.isnan(h[1:]).all())
            np.testing.assert_array_equal(k,[1,0,0,0])

    def test_changed_tile_and_duplicate_lattice_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make(root);sampler=CorridorTerrain(root)
            path=root/'0_0.npz';path.write_bytes(path.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError,'Changed'):sampler.sample([[1,1]])
            p=root/'manifest.json';m=json.loads(p.read_text());m['tiles'].append(m['tiles'][0]);p.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'lattice'):CorridorTerrain(root)

    def test_input_shape_preserved_and_invalid_coordinates_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make(root);sampler=CorridorTerrain(root)
            h,k=sampler.sample(np.array([[[.5,.5],[2,2]]]))
            self.assertEqual(h.shape,(1,2));self.assertEqual(k.shape,(1,2))
            with self.assertRaises(ValueError):sampler.sample([[np.nan,1]])

    def test_inferred_transition_is_not_mislabeled_native(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make(root);p=root/'manifest.json';m=json.loads(p.read_text())
            path=root/'1_0.npz'
            with np.load(path) as z:arrays={key:z[key] for key in z.files}
            arrays['source_kind'][:]=3;np.savez(path,**arrays)
            for row in m['tiles']:
                if row['file']==path.name:row['sha256']=sha(path)
            p.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'receipt'):CorridorTerrain(root).sample([[2.5,1.]])
            m.update(schema='raftsim.chilko_corridor_conditioned_terrain.v1',
                inferred_seam=dict(native_pixels_unchanged=True,measured=False),source_terrain=dict(sha256='source'))
            p.write_text(json.dumps(m));h,k=CorridorTerrain(root).sample([[2.5,1.],[2,2]])
            np.testing.assert_array_equal(k,[3,3])


if __name__=='__main__':unittest.main()
