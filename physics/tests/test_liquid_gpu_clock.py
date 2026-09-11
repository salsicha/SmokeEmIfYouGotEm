from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_gpu_clock import compare


class GPUClockTest(unittest.TestCase):
    def clock(self):
        age=np.r_[np.linspace(.1,12.,715),np.full(35,12.)]
        delta=np.r_[0,np.diff(age)]
        return np.stack((age,delta,np.zeros(750),(delta>0).astype(float)),axis=-1)

    def test_actual_age_and_pause(self):
        self.assertTrue(compare(self.clock(),11.999989,np.array([12.]))['gpu_clock_verified'])

    def test_rejects_callback_time_and_changed_paused_clock(self):
        clock=self.clock();clock[:,1]=1/60
        self.assertFalse(compare(clock,12.,np.array([12.]))['gpu_clock_verified'])
        clock=self.clock();clock[-1,0]+=.01
        self.assertFalse(compare(clock,12.,np.array([12.]))['gpu_clock_verified'])

    def test_surface_metadata_and_independent_age_must_match(self):
        self.assertFalse(compare(self.clock(),12.1,np.array([12.]))['gpu_clock_verified'])
        self.assertFalse(compare(self.clock(),12.,np.array([0.]))['gpu_clock_verified'])

    def test_split_clock_quantization_is_exact_in_half_storage(self):
        age=np.linspace(0,70,200001,dtype=np.float32)
        whole=np.floor(age)
        fraction=np.rint((age-whole)*2048)/2048
        stored_whole=whole.astype(np.float16).astype(np.float32)
        stored_fraction=fraction.astype(np.float16).astype(np.float32)
        self.assertTrue(np.array_equal(whole,stored_whole))
        self.assertTrue(np.array_equal(fraction,stored_fraction))
        self.assertLessEqual(np.max(abs(stored_whole+stored_fraction-age)),1/4096)


if __name__=='__main__':unittest.main()
