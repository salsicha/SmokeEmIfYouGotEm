import unittest
import numpy as np
from review_colorado_hydraulic_domain import lateral_axis,construction_lateral_axis,source_footprint_coverage


class HydraulicDomain(unittest.TestCase):
    def fixture(self):
        wet=np.zeros((20,20),bool);wet[8:12,:]=True
        return dict(classified_water_mask=wet,station_m=np.tile(np.arange(20)+.5,(20,1)),
            corner_east_north_m=np.array([0,20]),cell_m=np.array([1.,1.])),dict(source_core_interval_m=[2,18],source_halo_interval_m=[0,20])

    def test_asymmetric_axis_keeps_same_exact_lattice_and_width_limit(self):
        a=lateral_axis([-320,180]);self.assertEqual(len(a),251)
        np.testing.assert_array_equal(np.diff(a),np.full(250,2.))
        for interval in ((-321,179),(-322,180),(0,20),(-20,0),(-2,2),[1],[float('nan'),20]):
            with self.assertRaises(ValueError):lateral_axis(interval)

    def test_legacy_axis_and_refusals_unchanged_without_explicit_domain(self):
        width=dict(widths=[dict(classified_water_intervals_lateral_m=[[-51.3,80.2]],transect_truncated=False)])
        np.testing.assert_array_equal(construction_lateral_axis(width),np.arange(-102.,104.,2.))
        width['widths'][0]['transect_truncated']=True
        with self.assertRaisesRegex(ValueError,'Unbounded'):construction_lateral_axis(width)
        np.testing.assert_array_equal(construction_lateral_axis(width,[-320,180]),lateral_axis([-320,180]))
        with self.assertRaises(ValueError):construction_lateral_axis(dict(widths=[]),[-320,180])
        width['widths'][0]['transect_truncated']=False
        width['widths'][0]['classified_water_intervals_lateral_m']=[[-240,240]]
        with self.assertRaisesRegex(ValueError,'500 m'):construction_lateral_axis(width)

    def test_complete_core_not_halo_is_checked_without_mutating_mask(self):
        g,p=self.fixture();g['classified_water_mask'][1,0]=True
        old=g['classified_water_mask'].copy()
        result=source_footprint_coverage(g,p,[[0,10],[20,10]],[[0,1],[0,1]],[-4,4])
        self.assertTrue(result['complete_classified_core_coverage'])
        self.assertEqual(result['classified_source_core_cells'],64)
        np.testing.assert_array_equal(g['classified_water_mask'],old)

    def test_disconnected_channel_outside_dry_edges_is_not_silently_removed(self):
        g,p=self.fixture();g['classified_water_mask'][1,5:9]=True
        result=source_footprint_coverage(g,p,[[0,10],[20,10]],[[0,1],[0,1]],[-4,4])
        self.assertFalse(result['complete_classified_core_coverage'])
        self.assertEqual(result['uncovered_classified_source_core_cells'],4)

    def test_asymmetric_coverage_uses_physical_boundary_not_distance_buffer(self):
        g,p=self.fixture();g['classified_water_mask'][17,6]=True
        narrow=source_footprint_coverage(g,p,[[0,10],[20,10]],[[0,1],[0,1]],[-4,4])
        broad=source_footprint_coverage(g,p,[[0,10],[20,10]],[[0,1],[0,1]],[-8,4])
        self.assertFalse(narrow['complete_classified_core_coverage'])
        self.assertTrue(broad['complete_classified_core_coverage'])

    def test_bad_registration_and_empty_water_rejected(self):
        for change in ('wet','station','cell'):
            g,p=self.fixture()
            if change=='wet':g['classified_water_mask'][:]=False
            if change=='station':g['station_m'][0,0]=float('nan')
            if change=='cell':g['cell_m']=[2,2]
            with self.assertRaises(ValueError):source_footprint_coverage(g,p,[[0,10],[20,10]],[[0,1],[0,1]],[-4,4])

    def test_captured_end_plane_only_excludes_station_clamped_outside_cells(self):
        g,p=self.fixture();halo=452097.91174945974;end=453334.02824855957
        p.update(source_halo_interval_m=[halo,end],source_core_interval_m=[halo,end])
        local=end-halo
        g['station_m']=np.tile(np.minimum(np.arange(20),17)-17+local,(20,1)).astype(np.float32)
        original=g['station_m'].copy()
        caps=dict(stations=[0.,end],positions=[[0,10],[18,10]],directions=[[1,0],[1,0]])
        kwargs=dict(grid=g,profile=p,xy=[[0,10],[18,10]],normal=[[0,1],[0,1]],lateral=[-4,4],end_caps=caps)
        r=source_footprint_coverage(**kwargs)
        self.assertTrue(r['complete_classified_core_coverage'])
        self.assertEqual(r['outside_route_endpoint_cells'],8)
        self.assertEqual(r['classified_source_core_cells'],72)
        np.testing.assert_array_equal(g['station_m'],original)
        # A real earlier bend beyond this plane is still required water.
        g['station_m'][8,19]=local-1
        r=source_footprint_coverage(**kwargs)
        self.assertFalse(r['complete_classified_core_coverage'])
        self.assertEqual(r['outside_route_endpoint_cells'],7)
        self.assertEqual(r['uncovered_classified_source_core_cells'],1)
        caps['directions'][-1]=[0,0]
        with self.assertRaisesRegex(ValueError,'end planes'):source_footprint_coverage(**kwargs)

    def test_rounded_up_terminal_station_keeps_in_route_water(self):
        g,p=self.fixture();halo=452097.91174945974;end=453334.02817;local=end-halo
        self.assertGreater(float(np.float32(local)),local)
        p.update(source_halo_interval_m=[halo,end],source_core_interval_m=[halo,end])
        g['station_m']=np.full((20,20),local,np.float32)
        caps=dict(stations=[0.,end],positions=[[0,10],[20,10]],directions=[[1,0],[1,0]])
        result=source_footprint_coverage(g,p,[[0,10],[20,10]],[[0,1],[0,1]],[-4,4],end_caps=caps)
        self.assertEqual(result['classified_source_core_cells'],80)
        self.assertEqual(result['outside_route_endpoint_cells'],0)
        self.assertTrue(result['complete_classified_core_coverage'])


if __name__=='__main__':unittest.main()
