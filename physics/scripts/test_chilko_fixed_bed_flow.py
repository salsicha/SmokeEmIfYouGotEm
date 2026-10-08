import copy
import unittest
import numpy as np
from prepare_chilko_fixed_bed_flow import change_inflow


class FixedBedFlowTests(unittest.TestCase):
    def setUp(self):
        self.sc=dict(grid=dict(ny=3,dy=2.),roughness=.01986525,feature_count=0,
            metadata=dict(scenario_id='parent',provenance=dict(target_discharge_m3s=45.,
                continuous_terrain=dict(discharge_m3s=45.,manning_n=.045))),
            boundaries=[dict(edge='west',kind='discharge_profile',metadata=dict(target_discharge_m3s=45.),
                ghost_cells=[[100.,0.,0.,0.],[99.,1.,7.5,0.],[98.,2.,7.5,0.]]*2),
                dict(edge='east',kind='outflow',stage=100.),dict(edge='north',kind='bank'),dict(edge='south',kind='bank')])

    def test_only_inflow_velocity_and_labels_change_not_geometry_or_outlet(self):
        original=copy.deepcopy(self.sc)
        for discharge in (29.6,33.5,60.):
            result,receipt=change_inflow(self.sc,discharge,'control')
            self.assertEqual(self.sc,original)
            self.assertEqual(result['boundaries'][1:],self.sc['boundaries'][1:])
            for key in ('roughness','grid','feature_count'):self.assertEqual(result[key],self.sc[key])
            self.assertEqual(result['metadata']['provenance']['continuous_terrain'],
                             self.sc['metadata']['provenance']['continuous_terrain'])
            g=np.array(result['boundaries'][0]['ghost_cells'])
            np.testing.assert_array_equal(g[:,[0,1,3]],np.array(self.sc['boundaries'][0]['ghost_cells'])[:,[0,1,3]])
            self.assertAlmostEqual(float((g[:3,1]*g[:3,2]).sum()*2.),discharge)
            self.assertEqual(receipt['terrain_inference_discharge_m3s'],45.)
            self.assertFalse(receipt['runtime_promotion_authorized'])

    def test_unsupported_or_unchanged_discharge_and_reused_name_refused(self):
        for q,name in [(0,'control'),(501,'control'),(float('nan'),'control'),(45,'control'),(33.5,'parent'),(33.5,'')]:
            with self.assertRaises(ValueError):change_inflow(self.sc,q,name)

    def test_inconsistent_ghost_discharge_or_rows_are_refused(self):
        for row,column,value in [(1,2,8.),(4,2,8.),(1,3,1.),(1,1,-1.),(1,0,float('nan'))]:
            sc=copy.deepcopy(self.sc);sc['boundaries'][0]['ghost_cells'][row][column]=value
            with self.assertRaises(ValueError):change_inflow(sc,33.5,'control')

    def test_unreviewed_forcing_and_boundary_layout_refused(self):
        variants=[]
        for key,value in [('feature_count',1),('cascading',True)]:
            sc=copy.deepcopy(self.sc);sc[key]=value;variants.append(sc)
        sc=copy.deepcopy(self.sc);sc['boundaries'][0]['time_series']=[1,2];variants.append(sc)
        sc=copy.deepcopy(self.sc);sc['boundaries'][1]['kind']='discharge_profile';variants.append(sc)
        for sc in variants:
            with self.assertRaises(ValueError):change_inflow(sc,33.5,'control')


if __name__=='__main__':unittest.main()
