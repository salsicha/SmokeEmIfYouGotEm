import unittest
import numpy as np
from build_colorado_shared_hydraulic_frame import shared_frame,select_window


class SharedHydraulicFrame(unittest.TestCase):
    def data(self):
        return shared_frame([dict(easting=1000+s,northing=2000+30*np.sin(s/160)) for s in np.arange(0,2600,10)])

    def window(self,lo,hi):
        return dict(schema='raftsim.colorado_continuous_source_window.v1',source_halo_interval_m=[lo,hi])

    def test_overlapping_windows_share_exact_positions_normals_and_global_grid(self):
        data=self.data();a=select_window(data,self.window(0,1500));b=select_window(data,self.window(887,2400))
        common,ia,ib=np.intersect1d(a[0],b[0],return_indices=True)
        self.assertGreater(len(common),250)
        self.assertGreater(b[0][0],880)
        for i in range(4):np.testing.assert_array_equal(a[i][ia],b[i][ib])
        np.testing.assert_allclose(a[4][ia],b[4][ib]+887,atol=1e-12,rtol=0)
        np.testing.assert_allclose(np.mod(b[0],2),0,atol=0,rtol=0)

    def test_window_selection_never_clamps_a_missing_source_range(self):
        with self.assertRaises(ValueError):select_window(self.data(),self.window(3000,3400))
        with self.assertRaises(ValueError):select_window(self.data(),dict(source_halo_interval_m=[0,200]))

    def test_disconnected_source_cannot_be_smoothed_into_a_fake_connection(self):
        with self.assertRaises(ValueError):shared_frame([dict(easting=0,northing=0),dict(easting=100,northing=0)])


if __name__=='__main__':unittest.main()
