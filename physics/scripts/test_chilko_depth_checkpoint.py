from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from chilko_depth_checkpoint import DepthCheckpoint,array_digest


class DepthCheckpointTests(unittest.TestCase):
    def make(self,folder,**changes):
        binding=dict(discharge_m3s=45.,batch_size=32,source='fixture',code='fixture',grid=1.)
        binding.update(changes)
        return DepthCheckpoint(folder,binding,np.ones(5),64)

    def test_round_trip_and_absent_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint=self.make(tmp)
            start,depth,*history=checkpoint.load()
            self.assertEqual(start,0);np.testing.assert_array_equal(depth,np.ones(5))
            self.assertEqual(history,[[],[],[]])
            checkpoint.save(32,np.full(5,2.),np.ones(32),np.full(32,45.),np.full(32,10.))
            start,depth,before,after,width=checkpoint.load()
            self.assertEqual(start,32);np.testing.assert_array_equal(depth,np.full(5,2.))
            self.assertEqual(after,[45.]*32)

    def test_changed_source_code_grid_or_configuration_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make(tmp).save(32,np.ones(5),np.ones(32),np.full(32,45.),np.ones(32))
            for changes in (dict(source='changed'),dict(code='changed'),dict(grid=2.),dict(discharge_m3s=40.)):
                with self.assertRaisesRegex(ValueError,'changed'):self.make(tmp,**changes).load()

    def test_invalid_state_is_never_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint=self.make(tmp)
            for rows,depth,after in ((31,np.ones(5),45.),(96,np.ones(5),45.),
                                     (32,np.full(5,11.),45.),(32,np.full(5,.5),45.),
                                     (32,np.ones(5),44.),(32,np.full(5,np.nan),45.)):
                with self.assertRaises(ValueError):
                    checkpoint.save(rows,depth,np.ones(rows),np.full(rows,after),np.ones(rows))
            self.assertFalse((Path(tmp)/'latest.npz').exists())

    def test_interrupted_replace_preserves_previous_complete_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint=self.make(tmp)
            checkpoint.save(32,np.ones(5),np.ones(32),np.full(32,45.),np.ones(32))
            with patch('chilko_depth_checkpoint.os.replace',side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):
                    checkpoint.save(64,np.full(5,2.),np.ones(64),np.full(64,45.),np.ones(64))
            self.assertEqual(checkpoint.load()[0],32)
            checkpoint.save(64,np.full(5,2.),np.ones(64),np.full(64,45.),np.ones(64))
            self.assertEqual(checkpoint.load()[0],64)

    def test_corrupt_completed_state_is_rejected_on_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint=self.make(tmp)
            np.savez(Path(tmp)/'latest.npz',binding=checkpoint.binding,completed=64,
                     depth=np.ones(5),before=np.ones(32),after=np.full(32,45.),width=np.ones(32))
            with self.assertRaises(ValueError):checkpoint.load()

    def test_digest_covers_shape_dtype_and_values(self):
        original=np.arange(4,dtype=float)
        for other in (original.reshape(2,2),original.astype(int),original+1):
            self.assertNotEqual(array_digest(original),array_digest(other))


if __name__=='__main__':unittest.main()
