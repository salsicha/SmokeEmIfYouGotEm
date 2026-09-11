from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from plan_south_fork_guided_review import plan,aligned_raft_clearance
from summarize_south_fork_guided_review import meets_bounded_criteria


class GuidedRouteTests(unittest.TestCase):
    def test_ledger_rejects_old_outlet_only_success(self):
        report=dict(finite=True,reached_outlet=True,missing_ground_queries=0,
            duration_s=99.,minimum_tube_clearance_cm=0.,maximum_route_error_m=39.28)
        self.assertFalse(meets_bounded_criteria(report))

    def test_ledger_accepts_only_bounded_metrics(self):
        report=dict(finite=True,reached_outlet=True,missing_ground_queries=0,
            duration_s=81.13,minimum_tube_clearance_cm=44.89,maximum_route_error_m=4.97)
        self.assertTrue(meets_bounded_criteria(report))
        for field,value in (('finite',False),('reached_outlet',False),
            ('missing_ground_queries',1),('minimum_tube_clearance_cm',-.11),
            ('maximum_route_error_m',float('nan')),('duration_s',121.)):
            with self.subTest(field=field):
                self.assertFalse(meets_bounded_criteria(dict(report,**{field:value})))

    def test_aligned_envelope_preserves_exact_bilinear_extrema(self):
        y,x=np.mgrid[:20,:30]
        depth=3.+x*.1+y*.2
        clearance=aligned_raft_clearance(depth,1.)
        self.assertAlmostEqual(clearance[10,15],depth[10,15]-.235-.24)
        self.assertEqual(clearance[0,0],0.)

    def test_routes_around_obstacle_without_changing_depth(self):
        depth=np.full((19,30),2.);depth[7:12,13:16]=0;before=depth.copy()
        points,clearance=plan(depth,(9,4),25,footprint_radius=2.)
        self.assertEqual(points[-1][1],25)
        self.assertTrue(all(clearance[y,x]>=.55 for y,x in points))
        self.assertTrue(np.array_equal(depth,before))

    def test_disconnected_channel_rejected(self):
        depth=np.full((15,25),2.);depth[:,12]=0
        with self.assertRaises(ValueError):plan(depth,(7,4),20,footprint_radius=2.)

    def test_diagonal_corner_not_navigable(self):
        with self.assertRaises(ValueError):plan(np.eye(4)*2,(0,0),3,footprint_radius=0)

    def test_raft_footprint_not_only_center_must_fit(self):
        depth=np.zeros((9,20));depth[4,:]=2.
        with self.assertRaises(ValueError):plan(depth,(4,4),15,footprint_radius=2.)

    def test_favourable_current_is_traversable_without_mutating_flow(self):
        depth=np.full((5,20),2.);u=np.full_like(depth,3.);v=np.zeros_like(depth)
        points,_=plan(depth,(2,0),19,footprint_radius=0,velocity=(u,v))
        self.assertEqual(points[-1],(2,19))
        np.testing.assert_array_equal(u,3.)
        np.testing.assert_array_equal(v,0.)

    def test_current_stronger_than_paddling_rejects_upstream_route(self):
        depth=np.full((5,20),2.)
        with self.assertRaises(ValueError):
            plan(depth,(2,0),19,footprint_radius=0,
                velocity=(np.full_like(depth,-3.),np.zeros_like(depth)))

    def test_invalid_velocity_is_rejected(self):
        depth=np.full((5,20),2.)
        for velocity in ((np.zeros((2,2)),np.zeros_like(depth)),
                         (np.full_like(depth,np.nan),np.zeros_like(depth)),
                         (np.zeros_like(depth),)):
            with self.subTest(velocity_shapes=[a.shape for a in velocity]):
                with self.assertRaises(ValueError):
                    plan(depth,(2,0),19,footprint_radius=0,velocity=velocity)


if __name__=='__main__':unittest.main()
