import unittest
import numpy as np
from extend_futaleufu_terrain_context import supported_chunks,lattice,verify_join


class ContextTests(unittest.TestCase):
    def test_only_fully_supported_tiles_and_all_interior_tiles(self):
        grid=dict(epsg=32718,shape=[652,844],transform=[10,0,737790,0,-10,5201340,0,0,1])
        origin=[739986.,5195961.5];indices=supported_chunks(grid,origin,252)
        self.assertEqual(len(indices),800)
        self.assertEqual(len(indices),len(set(indices)))
        for key in indices:
            xy=lattice(key,origin,2)
            self.assertTrue((xy[...,0]>=737795).all() and (xy[...,0]<=746225).all())
            self.assertTrue((xy[...,1]>=5194825).all() and (xy[...,1]<=5201335).all())
        self.assertEqual(indices[0],(-8,-4));self.assertEqual(indices[-1],(23,20))

    def test_lattice_shared_edges_exact(self):
        a=lattice((1,2),[739986.,5195961.5],2)
        b=lattice((2,2),[739986.,5195961.5],2)
        c=lattice((1,3),[739986.,5195961.5],2)
        np.testing.assert_array_equal(a[:,-1],b[:,0]);np.testing.assert_array_equal(a[0],c[-1])

    def test_existing_bed_preserved_and_only_exterior_edges_checked(self):
        src=np.full((127,127),1000,np.uint16);bed=src.copy();bed[20:80,20:80]=900
        verify_join((0,0),bed,src,{(0,0)})
        bed[:,0]=900
        with self.assertRaisesRegex(ValueError,'seam'):verify_join((0,0),bed,src,{(0,0)})
        verify_join((0,0),bed,src,{(0,0),(-1,0),(0,-1),(0,1)})

    def test_invalid_frame_rejected(self):
        for epsg in (32618,3157):
            with self.assertRaises(ValueError):supported_chunks(dict(epsg=epsg,shape=[30,30],transform=[10,0,0,0,-10,0]),[0,0],252)


if __name__=='__main__':unittest.main()
