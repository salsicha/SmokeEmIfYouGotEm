"""The source catalog must not reverse its own reviewed location evidence."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]


class ChilkoCatalogSequenceTests(unittest.TestCase):
    def setUp(self):
        catalog=json.loads((ROOT/'physics/data/real_world/named_rapid_source_catalog.json').read_text())
        self.river=next(r for r in catalog['rivers'] if r['river_id']=='chilko_river_lava_canyon')
        self.evidence=json.loads((ROOT/self.river['sequence_evidence']['path']).read_text())

    def test_catalog_array_and_numeric_order_match_reviewed_sequence(self):
        rapids=self.river['rapids']
        names=[r['name'] for r in rapids]
        self.assertEqual([r['order'] for r in rapids],list(range(1,len(rapids)+1)))
        self.assertLess(names.index('Bidwell Rapids'),names.index('Green Mile'))
        self.assertLess(names.index('Green Mile'),names.index('White Mile'))
        green=next(e for e in self.evidence['entries'] if e['name']=='Green Mile')
        self.assertEqual(green['upstream_anchor'],'bcww_bidwell')
        self.assertEqual(green['downstream_anchor'],'bcww_white_mile')

    def test_order_does_not_claim_boundaries_or_aliases(self):
        green=next(e for e in self.evidence['entries'] if e['name']=='Green Mile')
        self.assertEqual(green['location_status'],'sequence_bracket_only')
        self.assertIsNone(green['boundary_lon_lat'])
        aliases=next(e for e in self.evidence['identity_checks'] if e['names']==['Green Mile','White Kilometer'])
        self.assertFalse(aliases['automatic_alias_allowed'])
        self.assertFalse(self.evidence['runtime_ready'])
        self.assertIn('aggregate reach',self.river['sequence_evidence']['qualification'])


if __name__=='__main__':unittest.main()
