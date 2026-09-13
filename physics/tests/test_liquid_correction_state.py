import hashlib
import json
import sys
import tempfile
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_correction_state import load_state


class CorrectionStateTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.package=root/'package';self.package.mkdir()
        self.state=root/'state';self.state.mkdir();self.meta=dict(cells=[4,4,4],world_lower_cm=[3,4,5],world_axes=np.eye(3).tolist())
        (self.package/'manifest.json').write_text(json.dumps(self.meta))
        self.arrays=dict(positions_world_cm=np.array([[5.,6,7]]),positions_local_cm=np.array([[2.,2,2]]),
            phi=np.zeros((4,4,4)),boundary=np.zeros((4,4,4,4)),particle_density=np.ones((4,4,4)))
        self.report=dict(candidate_map_and_inverse_valid=True,algorithm_sources_changed=[],native_stages_sha256='native',
            input_package=str(self.package),input_manifest_sha256=hashlib.sha256((self.package/'manifest.json').read_bytes()).hexdigest(),
            candidate_state_file='candidate_state.npz')
        self.save()

    def save(self):
        path=self.state/'candidate_state.npz';np.savez_compressed(path,**self.arrays)
        self.report['candidate_state_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        (self.state/'report.json').write_text(json.dumps(self.report))

    def test_complete_state_retains_particle_and_frame(self):
        a,r=load_state(self.state,self.package,'native',self.meta,1)
        np.testing.assert_array_equal(a['positions_world_cm'],self.arrays['positions_world_cm'])
        self.assertEqual(r['candidate_state_sha256'],self.report['candidate_state_sha256'])

    def test_changed_parent_and_wrong_native_rejected(self):
        with self.assertRaises(ValueError):load_state(self.state,self.package,'different',self.meta,1)
        (self.package/'manifest.json').write_text('{}')
        with self.assertRaises(ValueError):load_state(self.state,self.package,'native',self.meta,1)

    def test_failed_map_or_changed_algorithm_rejected(self):
        self.report['candidate_map_and_inverse_valid']=False;self.save()
        with self.assertRaises(ValueError):load_state(self.state,self.package,'native',self.meta,1)
        self.report['candidate_map_and_inverse_valid']=True;self.report['algorithm_sources_changed']=['map.py'];self.save()
        with self.assertRaises(ValueError):load_state(self.state,self.package,'native',self.meta,1)

    def test_lost_particle_and_changed_frame_rejected(self):
        with self.assertRaises(ValueError):load_state(self.state,self.package,'native',self.meta,2)
        self.arrays['positions_local_cm'][0,0]+=.1;self.save()
        with self.assertRaises(ValueError):load_state(self.state,self.package,'native',self.meta,1)

    def test_negative_density_and_fractional_phase_rejected(self):
        self.arrays['particle_density'][0,0,0]=-1;self.save()
        with self.assertRaises(ValueError):load_state(self.state,self.package,'native',self.meta,1)
        self.arrays['particle_density'][0,0,0]=1;self.arrays['boundary'][0,0,0,3]=.1;self.save()
        with self.assertRaises(ValueError):load_state(self.state,self.package,'native',self.meta,1)

    def test_modified_blob_rejected(self):
        (self.state/'candidate_state.npz').write_bytes(b'changed')
        with self.assertRaises(ValueError):load_state(self.state,self.package,'native',self.meta,1)


if __name__=='__main__':unittest.main()
