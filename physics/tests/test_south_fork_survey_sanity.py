from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from south_fork_survey_sanity import check_frame


class SurveySanityTests(unittest.TestCase):
    def frame(self):
        data=np.zeros(3,dtype=[(key,float) for key in ('h','eta','u','v','hu','hv')])
        data['h']=2.5;data['eta']=7.;data['u']=2.;data['hu']=5.
        return data

    def test_finite_bounded_candidate(self):
        self.assertTrue(check_frame(self.frame())['passed'])

    def test_depth_blowup_even_without_velocity_clipping(self):
        frame=self.frame();frame['h'][1]=3593.283905553646
        self.assertFalse(check_frame(frame)['passed'])

    def test_emergency_velocity_cap_is_not_valid_water(self):
        frame=self.frame();frame['u'][1]=60.;frame['v'][1]=60.
        self.assertFalse(check_frame(frame)['passed'])

    def test_nan_momentum_cannot_hide_behind_finite_depth(self):
        frame=self.frame();frame['hv'][1]=np.nan
        self.assertFalse(check_frame(frame)['passed'])

    def test_missing_fields_rejected(self):
        with self.assertRaises(ValueError):check_frame(np.zeros(1,dtype=[('h',float)]))


if __name__=='__main__':unittest.main()
