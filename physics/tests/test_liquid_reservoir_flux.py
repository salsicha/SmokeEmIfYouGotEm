import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_reservoir_flux import balance


class ReservoirFluxTest(unittest.TestCase):
    def test_ring_includes_all_corners_and_cancels_core_exchange(self):
        qx=np.broadcast_to(np.arange(7),(6,7));qy=np.broadcast_to(2*np.arange(7)[:,None],(7,6))
        r,mask=balance(qx,qy,[[1,1],[5,5]],[[0,0],[6,6]])
        self.assertEqual(mask.sum(),20)
        self.assertEqual(r,dict(core_inflow=-48,outer_inflow=-108,buffer_inflow=-60,buffer_cell_gain=-60))

    def test_signed_backflow_is_not_lost_by_separate_positive_sums(self):
        qx=np.zeros((6,7));qy=np.zeros((7,6));qx[2,1]=-7
        r,_=balance(qx,qy,[[1,1],[5,5]],[[0,0],[6,6]])
        self.assertEqual(r['core_inflow'],-7);self.assertEqual(r['buffer_inflow'],7)
        self.assertEqual(r['outer_inflow'],0)

    def test_uniform_throughflow_has_no_artificial_storage(self):
        r,_=balance(np.full((6,7),4),np.full((7,6),-2),[[1,1],[5,5]],[[0,0],[6,6]])
        self.assertEqual(set(r.values()),{0})

    def test_reject_non_nested_or_fractional_ownership(self):
        for core in ([[0,1],[5,5]],[[1,1],[7,5]],[[1,1],[1,5]],[[1.5,1],[5,5]]):
            with self.assertRaises(ValueError):balance(np.zeros((6,7)),np.zeros((7,6)),core,[[0,0],[6,6]])

    def test_reject_nonfinite_flux(self):
        qx=np.zeros((6,7));qx[1,1]=np.nan
        with self.assertRaises(ValueError):balance(qx,np.zeros((7,6)),[[1,1],[5,5]],[[0,0],[6,6]])
