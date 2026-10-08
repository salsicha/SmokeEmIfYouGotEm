"""Input-boundary tests; actual engine registration has a separate receipt."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verify_rapid_candidate_registration as registration

class CandidateInputTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.root_patch=patch.object(registration,'ROOT',self.root)
        self.root_patch.start();self.addCleanup(self.root_patch.stop)
        self.source=self.root/'source'
        (self.source/'scenario').mkdir(parents=True)
        files=['coordinate_map.json','reference.npz','scenario/bed.npy']
        for name in files:(self.source/name).write_bytes(name.encode())
        self.data=dict(schema='raftsim.rapid_feature_source_candidate.v1',rapid='Test',source_directory='source',
                       source_sha256={name:registration.sha(self.source/name) for name in files},
                       features=[[800,4,25,.9,4,.55]])
        self.path=self.root/'candidate.json'

    def load(self,data=None):
        self.path.write_text(json.dumps(self.data if data is None else data))
        return registration.load_candidate(self.path)

    def test_binds_candidate_and_all_three_sources(self):
        data,source,bound=self.load()
        self.assertEqual(source,self.source)
        self.assertEqual(data,self.data)
        self.assertEqual(len(bound),4)
        self.assertEqual(bound[self.path],registration.sha(self.path))

    def test_rejects_source_edit(self):
        (self.source/'scenario/bed.npy').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Changed candidate source'):self.load()

    def test_rejects_incomplete_source_binding(self):
        del self.data['source_sha256']['reference.npz']
        with self.assertRaisesRegex(ValueError,'Bind all'):self.load()

    def test_rejects_source_path_escape(self):
        self.data['source_directory']='../outside'
        with self.assertRaises(ValueError):self.load()

    def test_rejects_absolute_path_escape(self):
        with self.assertRaises(ValueError):registration.inside(self.root,str(self.root.parent/'outside'))

    def test_rejects_unknown_schema(self):
        self.data['schema']='unknown'
        with self.assertRaisesRegex(ValueError,'Unsupported'):self.load()

    def test_rejects_empty_layout(self):
        self.data['features']=[]
        with self.assertRaisesRegex(ValueError,'Empty'):self.load()

    def test_rejects_nonfinite_values_in_every_column(self):
        for i in range(6):
            for value in (float('nan'),float('inf'),-float('inf')):
                data=copy.deepcopy(self.data);data['features'][0][i]=value
                with self.subTest(column=i,value=value):
                    with self.assertRaisesRegex(ValueError,'finite'):self.load(data)

    def test_rejects_incomplete_feature(self):
        self.data['features'][0].pop()
        with self.assertRaisesRegex(ValueError,'Six finite'):self.load()

    def test_rejects_out_of_range_shared_kernel_parameters(self):
        for column,value in ((3,0),(3,1.21),(4,1.99),(4,7.01),(5,-.01),(5,1.01)):
            data=copy.deepcopy(self.data);data['features'][0][column]=value
            with self.subTest(column=column,value=value):
                with self.assertRaisesRegex(ValueError,'bounds'):self.load(data)

if __name__=='__main__':unittest.main()
