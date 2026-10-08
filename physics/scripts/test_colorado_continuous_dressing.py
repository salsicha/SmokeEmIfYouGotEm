import unittest
import numpy as np
from build_colorado_continuous_dressing import candidates, eligible, SourceWaterClearance, terrain_support_slope
from scipy.ndimage import distance_transform_edt, map_coordinates


class DressingTests(unittest.TestCase):
    def test_support_preserves_arbitrary_planar_gradient(self):
        xy=np.array([[0.,0.],[37.,-91.],[-252.,252.]])
        for gx,gy in ((0,0),(.2,.3),(-.8,.1),(.4,-.4)):
            sample=lambda p: 100+gx*p[...,0]+gy*p[...,1]
            np.testing.assert_allclose(terrain_support_slope(sample,xy,sample(xy)),np.hypot(gx,gy),atol=1e-12)

    def test_ridge_and_hollow_cannot_cancel_to_flat(self):
        xy=np.array([[0.,0.]])
        for sign in (-1.,1.):
            sample=lambda p: 100+sign*np.abs(p[...,0])
            slope=terrain_support_slope(sample,xy,sample(xy))
            np.testing.assert_allclose(slope,[1.])
            self.assertFalse(eligible(sample(xy),slope,np.array([20.]),np.array([20.]))[0])

    def test_diagonal_fold_is_checked(self):
        xy=np.array([[0.,0.]])
        sample=lambda p: 100+np.minimum(np.abs(p[...,0]),np.abs(p[...,1]))
        np.testing.assert_allclose(terrain_support_slope(sample,xy,sample(xy)),[1/np.sqrt(2)])

    def test_unknown_support_and_invalid_shapes_refused(self):
        xy=np.array([[0.,0.],[10.,10.]])
        sample=lambda p: np.where((p[...,0]==1)&(p[...,1]==1),np.nan,100.)
        slope=terrain_support_slope(sample,xy,np.array([100.,100.]))
        self.assertTrue(np.isinf(slope[0]));self.assertEqual(slope[1],0.)
        with self.assertRaises(ValueError):terrain_support_slope(sample,xy,np.array([100.]))
        with self.assertRaises(ValueError):terrain_support_slope(lambda p: np.ones(len(p)),xy,np.array([100.,100.]))

    def test_source_clearance_cache_preserves_overlap_minimum_after_eviction(self):
        sources=[]
        for i in range(6):
            wet=np.zeros((20,20),bool);wet[:,3+i]=True
            sources.append(dict(bounds=(i*10,20,20,20),grid=dict(
                corner_east_north_m=np.array([i*10,20]),classified_water_mask=wet)))
        clearance=SourceWaterClearance(sources,max_grids=1)
        for offset in list(range(6))+list(reversed(range(6))):
            xy=np.array([[offset*10+.5,15.5],[offset*10+14.5,10.5],[-100,0]])
            expected=np.full(3,np.inf);covered=np.zeros(3,bool)
            for s in sources:
                x,y,h,w=s['bounds'];r=y-xy[:,1]-.5;c=xy[:,0]-x-.5
                valid=(r>=0)&(r<=h-1)&(c>=0)&(c<=w-1)
                values=map_coordinates(distance_transform_edt(~s['grid']['classified_water_mask']),
                    [r[valid],c[valid]],order=1,prefilter=False)
                expected[valid]=np.minimum(expected[valid],values);covered|=valid
            actual,actual_covered=clearance.sample(xy)
            np.testing.assert_array_equal(actual,expected)
            np.testing.assert_array_equal(actual_covered,covered)
            self.assertLessEqual(len(clearance.distances),1)

    def test_source_clearance_requires_positive_cache(self):
        for size in (0,-1,True,1.5):
            with self.assertRaises(ValueError):SourceWaterClearance([],size)

    def test_deterministic_extension_and_no_duplicate_seams(self):
        a=candidates([0,0]);b=candidates([252,0]);again=candidates([0,0])
        np.testing.assert_array_equal(a,again)
        self.assertTrue((a[:,0]<252).all())
        self.assertTrue((b[:,0]>=252).all())
        self.assertFalse(set(map(tuple,a[:,:2])) & set(map(tuple,b[:,:2])))
        self.assertTrue(((a[:,3]>=.65)&(a[:,3]<1.2)).all())

    def test_geographic_chunk_offsets_do_not_duplicate_cells(self):
        a=candidates([242600,650500]);b=candidates([242852,650500])
        self.assertFalse(set(map(tuple,a[:,:2])) & set(map(tuple,b[:,:2])))

    def test_water_steep_and_unknown_terrain_excluded(self):
        z=np.array([100,100,100,100,np.nan,100,100])
        slope=np.array([0,0,0,1,0,np.nan,0])
        source=np.array([20,5,20,20,20,20,200])
        solved=np.array([20,20,5,20,20,20,20])
        np.testing.assert_array_equal(eligible(z,slope,source,solved),[True,False,False,False,False,False,False])


if __name__=='__main__':unittest.main()
