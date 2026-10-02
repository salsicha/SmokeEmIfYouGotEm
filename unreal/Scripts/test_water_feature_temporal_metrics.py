import unittest
from water_feature_temporal_metrics import step_clock, paired_column_differences


class TemporalMetricsTests(unittest.TestCase):
    def rows(self,m=1):
        return [dict(index=i,frame=193,dt_native=.1041666667/(2*m),
            time_per_frame_native=i*.1041666667/(2*m),time_total_native=20.+i*.1041666667/(2*m),
            primary_before=12,primary_after=13) for i in range(2*m)]

    def test_same_duration_subdivisions(self):
        for m in (1,2,4):
            self.assertAlmostEqual(step_clock(self.rows(m),193,193,m)['integrated_duration_s'],1/24)

    def test_integrator_overrun_is_not_hidden(self):
        rows=self.rows();rows[-1]['dt_native']+=.0001
        self.assertGreater(step_clock(rows,193,193,1)['integrated_duration_s'],1/24)

    def test_missing_frame_rejected(self):
        with self.assertRaises(ValueError):step_clock(self.rows(),193,194,1)

    def test_missing_after_or_nonfinite_rejected(self):
        for change in ({'dt_native':float('nan')},{'primary_after':0},{'time_per_frame_native':-1.}):
            rows=self.rows();rows[0].update(change)
            with self.assertRaises(ValueError):step_clock(rows,193,193,1)

    def test_missing_column_preserved(self):
        a=[dict(column=[3,4],interface=dict(status='supported',crossings=[dict(relative_height_m=.3)]))]
        b=[dict(column=[3,4],interface=dict(status='absent',crossings=[]))]
        row=paired_column_differences(a,b)[0]
        self.assertFalse(row['supported']);self.assertIsNone(row['vertical_difference_m'])

    def test_mismatched_cohort_rejected(self):
        with self.assertRaises(ValueError):paired_column_differences([{'column':[3,4]}],[{'column':[3,5]}])


if __name__=='__main__':unittest.main()
