import unittest
import numpy as np
from scipy.spatial import cKDTree
from cooked_water_clearance import CookedWaterClearance
from export_colorado_continuous_runtime import registered_queries


class CookedWaterClearanceTests(unittest.TestCase):
    def fixture(self,nx=101,ny=31):
        s=np.arange(nx)*2.;angle=s*.018
        points=np.column_stack((s,40*np.sin(angle),40*np.cos(angle),np.sin(angle),np.cos(angle)))
        mapping=dict(schema='raftsim.curved_river_coordinate_map.v1',world_y_sign=-1,
            horizontal_origin_epsg6404_m=[242600.,650500.],vertical_datum_m=310.,points=points.tolist())
        terrain=dict(horizontal_origin_epsg6404_m=[242600.,650500.],vertical_datum_m=310.)
        grid=dict(nx=nx,ny=ny,dx=2.,dy=2.,origin_x=0.,origin_y=-float(ny-1))
        wet=np.random.default_rng(35).random((ny,nx))>.4
        return mapping,terrain,grid,wet

    def test_all_close_bends_and_chunk_orders_equal_global_tree(self):
        mapping,terrain,grid,wet=self.fixture()
        _,water=registered_queries(mapping,terrain,grid)
        tree=cKDTree(water[wet]);rng=np.random.default_rng(3)
        queries=rng.uniform([-100,-100],[100,100],size=(400,2))+[242600,650500]
        # A request including distant station indices near the same bend must
        # still inspect every physically nearby branch, not one station window.
        for block in (31,93,262144):
            sample=CookedWaterClearance(mapping,terrain,grid,wet,block_cells=block)
            for radius in (0.,12.,27.):
                expected=np.minimum(radius,tree.query(queries)[0]-np.hypot(2.,2.))
                for indices in (np.arange(400),np.arange(399,-1,-1)):
                    chunks=[sample.sample(queries[part],radius) for part in np.array_split(indices,17)]
                    np.testing.assert_array_equal(np.concatenate(chunks),expected[indices])

    def test_exact_threshold_nextafter_and_large_translation(self):
        for origin in (0.,242600.,1.e12):
            mapping,terrain,grid,wet=self.fixture(3,3)
            mapping['horizontal_origin_epsg6404_m']=[origin,origin]
            terrain['horizontal_origin_epsg6404_m']=[origin,origin]
            mapping['points']=[[s,s,0.,0.,1.] for s in (0.,2.,4.)]
            wet[:]=False;wet[1,1]=True
            _,water=registered_queries(mapping,terrain,grid)
            threshold=12+np.hypot(2.,2.)
            distances=np.array([np.nextafter(threshold,-np.inf),threshold,np.nextafter(threshold,np.inf)])
            xy=water[1,1]+np.column_stack((distances,np.zeros(3)))
            sampler=CookedWaterClearance(mapping,terrain,grid,wet,block_cells=3)
            expected=np.minimum(12,cKDTree(water[wet]).query(xy)[0]-np.hypot(2.,2.))
            np.testing.assert_array_equal(sampler.sample(xy),expected)

    def test_lattice_subset_and_generic_chilko_frame(self):
        mapping,terrain,grid,wet=self.fixture(11,5)
        grid.update(nx=4,origin_x=8.);wet=wet[:,4:8]
        for obj in (mapping,terrain):
            obj['horizontal_origin_m']=obj.pop('horizontal_origin_epsg6404_m')
            obj.update(river_id='chilko_river_bc',horizontal_crs='EPSG:3157',
                       vertical_reference='CGVD2013 (EPSG:6647)',world_y_sign=-1)
        terrain['schema']='raftsim.continuous_landscape.v1'
        _,water=registered_queries(mapping,terrain,grid)
        xy=water.reshape(-1,2)+[5,10]
        sampler=CookedWaterClearance(mapping,terrain,grid,wet,block_cells=5)
        expected=np.minimum(12,cKDTree(water[wet]).query(xy)[0]-np.hypot(2.,2.))
        np.testing.assert_array_equal(sampler.sample(xy),expected)

    def test_mask_is_borrowed_and_reads_are_bounded(self):
        mapping,terrain,grid,wet=self.fixture()
        class Mask:
            shape=wet.shape
            maximum=0
            def __getitem__(self,key):
                result=wet[key];self.maximum=max(self.maximum,result.size);return result
        mask=Mask();sampler=CookedWaterClearance(mapping,terrain,grid,mask,block_cells=93)
        sampler.sample(np.array([[242600.,650500.],[242650.,650550.]]))
        self.assertIs(sampler.wet,mask);self.assertLessEqual(mask.maximum,93)

    def test_invalid_or_unknown_data_is_not_clearance(self):
        mapping,terrain,grid,wet=self.fixture()
        for bad in (wet[:2],np.zeros_like(wet),np.full(wet.shape,np.nan),np.full(wet.shape,2)):
            with self.assertRaises(ValueError):CookedWaterClearance(mapping,terrain,grid,bad)
        for block in (0,1,True,31.5):
            with self.assertRaises(ValueError):CookedWaterClearance(mapping,terrain,grid,wet,block_cells=block)
        sampler=CookedWaterClearance(mapping,terrain,grid,wet)
        for xy in (np.array([[np.nan,0]]),np.zeros((2,3))):
            with self.assertRaises(ValueError):sampler.sample(xy)
        for radius in (-1.,np.nan,np.inf):
            with self.assertRaises(ValueError):sampler.sample(np.zeros((1,2)),radius)
        self.assertEqual(sampler.sample(np.empty((0,2))).shape,(0,))


if __name__=='__main__':unittest.main()
