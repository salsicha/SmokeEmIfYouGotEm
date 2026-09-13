import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_stratified_source import select_sites,cumulative_weights,native_sites


class StratifiedSourceTest(unittest.TestCase):
    def test_uniform_batch_distinct_sites(self):
        for offset in (0,.001,.5,.999999):
            chosen,r=select_sites(np.ones(128),32,offset)
            self.assertEqual(len(np.unique(chosen)),32);self.assertEqual(r['duplicate_site_births'],0)

    def test_nonuniform_counts_preserve_expectation(self):
        weights=np.array([1.,3,7,2,0,4]);total=np.zeros(len(weights))
        for k in range(2048):
            chosen,r=select_sites(weights,9,(k+.5)/2048)
            total+=np.bincount(chosen,minlength=len(weights));self.assertLessEqual(r['maximum_count_discrepancy'],1.)
        np.testing.assert_allclose(total/2048,9*weights/weights.sum(),atol=1/2048)
        self.assertEqual(total[4],0)

    def test_high_weight_site_is_not_illegally_capped_to_one_birth(self):
        chosen,r=select_sites([99,1],10,.5)
        self.assertEqual(len(chosen),10);self.assertGreater(r['duplicate_site_births'],0)
        self.assertFalse(r['mass_or_source_weights_modified'])

    def test_empty_batch_and_invalid_distribution(self):
        chosen,r=select_sites([1,2],0,.5);self.assertEqual(len(chosen),0)
        for w in ([],[0,0],[-1,2],[1,np.inf]):
            with self.assertRaises(ValueError):cumulative_weights(w)
        for n,u in ((-1,.5),(1,1),(1,-.1),(True,.5)):
            with self.assertRaises(ValueError):select_sites([1],n,u)

    def test_native_integer_identity_hash_and_batch_permutation(self):
        sequence=np.arange(17000123,17000156,dtype=np.int64);first=np.full(33,sequence[0]);count=np.full(33,33)
        a=native_sites(np.linspace(1,3,3712),sequence,first,count,173193)
        self.assertEqual(len(np.unique(a)),33)
        order=np.arange(33)[::-1]
        np.testing.assert_array_equal(native_sites(np.linspace(1,3,3712),sequence[order],first,count,173193),a[order])
        # Above float's exact-integer range, identities still remain integers.
        self.assertFalse(np.array_equal(a,native_sites(np.linspace(1,3,3712),sequence+1,first+1,count,173193)))

    def test_native_bounds_and_collapsed_positive_weight_are_rejected(self):
        with self.assertRaises(ValueError):native_sites([1],np.array([2]),np.array([3]),np.array([1]),0)
        with self.assertRaises(ValueError):native_sites([1,1e-20],np.array([2]),np.array([2]),np.array([1]),0)


if __name__=='__main__':unittest.main()
