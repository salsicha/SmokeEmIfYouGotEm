import unittest
from audit_water_source_bounds import audit


def fixture():
    return '\n'.join(f'WaterBoundsPair frame={i} exact=1 candidate_first={(i//2)%2} '
                     'vertices=50625 reference_ms=0.8 candidate_ms=0.3'
                     for i in range(120, 184))


class BoundsPairsTest(unittest.TestCase):
    def test_complete_orders_do_not_claim_game_acceptance(self):
        result = audit(fixture())
        self.assertEqual([r['count'] for r in result['order_groups']], [32, 32])
        self.assertFalse(result['game_performance_accepted'])
        self.assertFalse(result['visual_accepted'])

    def test_missing_duplicate_and_reordered_frames_fail(self):
        lines = fixture().splitlines()
        for altered in (lines[1:], lines + lines[:1], lines[::-1]):
            with self.assertRaises(ValueError):
                audit('\n'.join(altered))

    def test_bad_pair_values_fail(self):
        for before, after in [('exact=1', 'exact=0'), ('vertices=50625', 'vertices=0'),
                              ('reference_ms=0.8', 'reference_ms=0'),
                              ('candidate_ms=0.3', 'candidate_ms=nan'),
                              ('candidate_first=0', 'candidate_first=1')]:
            with self.assertRaises(ValueError):
                audit(fixture().replace(before, after, 1))

    def test_runtime_error_fails(self):
        with self.assertRaises(ValueError):
            audit(fixture() + '\nWater source bounds mismatch')
