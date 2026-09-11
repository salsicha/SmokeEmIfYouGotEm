from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from recenter_south_fork_liquid_window import rebase_mesh
from build_south_fork_liquid_sources import unresolved_outgoing_dry_noise,split_face_discharge


class Source(dict):
    @property
    def files(self):return list(self)


class LiquidWindowRebaseTest(unittest.TestCase):
    def test_dry_outgoing_noise_is_not_permission_to_drop_inflow(self):
        self.assertTrue(unresolved_outgoing_dry_noise(-1.567e-9,[0,0]))
        for q,depth in [(1e-9,[0,0]),(-1e-6,[0,0]),(-1e-9,[0,.001]),(float('nan'),[0,0])]:
            self.assertFalse(unresolved_outgoing_dry_noise(q,depth))
        with self.assertRaises(ValueError):split_face_discharge(1e-9,[0,0],.125)
        with self.assertRaises(ValueError):split_face_discharge(-1e-9,[0,0],.125)

    def test_only_coordinate_origin_changes(self):
        x=np.array([-1.,0.,1.]);y=np.array([1.,0.,-1.])
        east,north=np.meshgrid(x,y)
        data=Source(east_m=east,north_m=north,nominal_east_axis_m=x,nominal_north_axis_m=y,
            z_m=np.arange(9).reshape(3,3),authority=np.arange(9).reshape(3,3)%3+1,
            triangles=np.array([[0,1,3],[1,4,3]],dtype=np.int32))
        old={k:v.copy() for k,v in data.items()};offset=np.array([-9.3,3.67])
        changed=rebase_mesh(data,offset)
        for key in data:np.testing.assert_array_equal(data[key],old[key])
        for key,axis in [('east_m',0),('north_m',1),('nominal_east_axis_m',0),('nominal_north_axis_m',1)]:
            np.testing.assert_allclose(changed[key]+offset[axis],old[key],atol=1e-14)
        for key in ('z_m','authority','triangles'):np.testing.assert_array_equal(changed[key],old[key])

    def test_invalid_translation_rejected(self):
        for offset in ([float('nan'),0],[1,2,3],[-float('inf'),0]):
            with self.assertRaises(ValueError):rebase_mesh(Source(),offset)


if __name__=='__main__':unittest.main()
