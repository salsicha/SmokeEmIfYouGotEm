import unittest
from build_bidwell_exit_controls import build,matched_core


class BidwellExitControls(unittest.TestCase):
    def test_matched_exit_preserves_upstream_route_not_just_first_two_nodes(self):
        def sample(route,s):
            for (a,x),(b,y) in zip(route,route[1:]):
                if a<=s<=b:return x+(y-x)*(s-a)/(b-a)
            self.fail('outside route')
        trials=matched_core()[0]['trials']
        for t in trials[1:]:
            self.assertEqual(t['finish_m'],1080)
            for s in range(650,int(t['route_laterals'][2][0])+1):
                self.assertAlmostEqual(sample(trials[0]['route_laterals'],s),sample(t['route_laterals'],s))

    def test_runout_cannot_be_hidden_behind_old_finish(self):
        plan=build()[0]
        self.assertEqual(len(plan['trials']),3)
        for t in plan['trials']:
            self.assertEqual(t['finish_m'],1080)
            self.assertEqual(t['lookahead_m'],45)
            self.assertEqual(t['start_m'],650)
            self.assertEqual(t['lane_m'],0)
            self.assertTrue(t['strict_route'])
            self.assertFalse(t['normal_rescue_inputs'])
            self.assertEqual(t['gates'][-1]['station_m'],1075)
            self.assertNotIn('rescue_drill_station_m',t)

    def test_early_and_late_exits_differ_in_timing_not_boat_or_water(self):
        a,b=build()[0]['trials'][1:]
        allowed={'id','variant','route_laterals'}
        self.assertEqual({k:v for k,v in a.items() if k not in allowed},
                         {k:v for k,v in b.items() if k not in allowed})
        self.assertEqual(a['route_laterals'][:2],b['route_laterals'][:2])
        self.assertEqual(a['route_laterals'][-1],b['route_laterals'][-1])
        self.assertLess(a['route_laterals'][3][0],b['route_laterals'][3][0])


if __name__=='__main__': unittest.main()
