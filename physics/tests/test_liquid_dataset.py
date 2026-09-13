import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_dataset import resolve


class LiquidDatasetTest(unittest.TestCase):
    def test_legacy_capture_stays_on_original_dataset(self):
        self.assertEqual(resolve({})['key'],'core-v1')
        self.assertNotEqual(resolve({})['parent'],resolve(key='reservoir-v1')['parent'])

    def test_unknown_key_and_conflicting_capture_are_rejected(self):
        for key in ('../reservoir-v1','unknown',''):
            with self.assertRaises(ValueError):resolve(key=key)
        with self.assertRaises(ValueError):resolve({'native_dataset':{'key':'core-v1'}},key='reservoir-v1')

    def test_all_captured_manifest_identities_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths=resolve(key='reservoir-v1',root=tmp)
            fields={'parent_manifest_sha256':paths['parent']/'manifest.json',
                'ownership_manifest_sha256':paths['regions']/'manifest.json',
                'geometry_manifest_sha256':paths['geometry']/'manifest.json','face_bed_sha256':paths['face_bed']}
            evidence={'key':'reservoir-v1'}
            for i,(field,path) in enumerate(fields.items()):
                path.parent.mkdir(parents=True,exist_ok=True);data=str(i).encode();path.write_bytes(data)
                evidence[field]=hashlib.sha256(data).hexdigest()
            self.assertEqual(resolve({'native_dataset':evidence},root=tmp)['key'],'reservoir-v1')
            for field in fields:
                corrupt=dict(evidence);corrupt[field]='0'*64
                with self.assertRaises(ValueError):resolve({'native_dataset':corrupt},root=tmp)

    def test_invalid_capture_descriptor_is_not_treated_as_legacy(self):
        for evidence in (None,False,[],{},'core-v1'):
            with self.assertRaises(ValueError):resolve({'native_dataset':evidence})
