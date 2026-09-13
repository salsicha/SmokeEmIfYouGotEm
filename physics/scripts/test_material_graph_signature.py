import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'unreal/Scripts'))
from raftsim_material_graph_signature import canonical_graph


class MaterialGraphSignatureTest(unittest.TestCase):
    def test_wrapper_address_not_identity(self):
        a={'node':{'default_value':"<Struct 'LinearColor' (0xABC123) {r: 1.0}>",
                   'texture':"<Object '/Game/A.A' (0x0123) Class 'Texture2D'>",'code':'return 0xABC123;'}}
        b={'node':{'default_value':"<Struct 'LinearColor' (0x5678) {r: 1.0}>",
                   'texture':"<Object '/Game/A.A' (0x4567) Class 'Texture2D'>",'code':'return 0xABC123;'}}
        self.assertEqual(canonical_graph(a),canonical_graph(b))
        self.assertIn('0xABC123',canonical_graph(a)['node']['code'])
        self.assertIn('0xABC123',a['node']['default_value'])

    def test_asset_values_and_links_remain_significant(self):
        original={'texture':"<Object '/Game/A.A' (0x0123) Class 'Texture2D'>",'default_value':'0.5','inputs':{'UV':'Coordinate_0'}}
        for changed in (dict(original,texture="<Object '/Game/B.B' (0x0123) Class 'Texture2D'>"),
                        dict(original,default_value='0.6'), dict(original,inputs={'UV':'Coordinate_1'})):
            self.assertNotEqual(canonical_graph(original),canonical_graph(changed))


if __name__=='__main__':
    unittest.main()
