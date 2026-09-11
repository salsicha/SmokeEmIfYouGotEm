import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_secondary_particles import particle_rows, surface_alignment, sampled_contact_verified, recorded_current_stage_order


class SecondaryRecordsTest(unittest.TestCase):
    def test_current_stage_order_requires_actual_nonzero_coverage(self):
        report=dict(current_surface_before_secondary=True,error='',updates_with_simulation_tick=10,
                    reconstruction_before_secondary_updates=10,secondary_pre_stage_events=20)
        self.assertTrue(recorded_current_stage_order(report))
        for changes in ({'current_surface_before_secondary':False},{'error':'late update'},
                        {'reconstruction_before_secondary_updates':9},{'secondary_pre_stage_events':9},
                        {'updates_with_simulation_tick':0,'reconstruction_before_secondary_updates':0}):
            self.assertFalse(recorded_current_stage_order(dict(report,**changes)))
        self.assertFalse(recorded_current_stage_order({}))

    def test_contact_gate_requires_all_actual_probes_and_clean_state(self):
        capture=dict(complete=True,error=None,secondary_exact_contact_compiled=True)
        record=dict(count=2,exact_bed_probe_count=2,below_bed=0,outside_domain=0,
                    missing_exact_bed_probe_count=0,nonfinite_positions=0,nonfinite_velocities=0)
        self.assertTrue(sampled_contact_verified(capture,[record],[]))
        for key in record:
            missing=record.copy();del missing[key]
            with self.subTest(missing=key):
                self.assertFalse(sampled_contact_verified(capture,[missing],[]))
        for key in ('below_bed','outside_domain','missing_exact_bed_probe_count',
                    'nonfinite_positions','nonfinite_velocities'):
            with self.subTest(failed=key):
                self.assertFalse(sampled_contact_verified(capture,[dict(record,**{key:1})],[]))
        self.assertFalse(sampled_contact_verified(capture,[dict(record,exact_bed_probe_count=1)],[]))

    def test_contact_gate_rejects_empty_uncompiled_or_failed_capture(self):
        capture=dict(complete=True,error=None,secondary_exact_contact_compiled=True)
        record=dict(count=2,exact_bed_probe_count=2,below_bed=0,outside_domain=0,
                    missing_exact_bed_probe_count=0,nonfinite_positions=0,nonfinite_velocities=0)
        for override in (dict(complete=False),dict(error='capture failed'),dict(secondary_exact_contact_compiled=False)):
            self.assertFalse(sampled_contact_verified(dict(capture,**override),[record],[]))
        self.assertFalse(sampled_contact_verified(capture,[record],['GPU error']))
        self.assertFalse(sampled_contact_verified(capture,[],[]))
        self.assertFalse(sampled_contact_verified(capture,[dict(record,count=0,exact_bed_probe_count=0)],[]))

    def test_alignment_uses_local_origin_and_anisotropic_extent(self):
        z,y,x=np.indices((4,5,6))
        native=((z+.5)*10-20)[...,None].astype(float)
        rendered=np.concatenate((native+3,np.zeros_like(native)),axis=-1)
        rows=np.array([[1,-1,-20,5,18,0,0,0],[2,-1,5,20,25,0,0,0],[3,-1,100,20,25,0,0,0]])
        result=surface_alignment(rows,[0,1,2],rendered,native,[60,100,40],[-30,-50,0])
        self.assertEqual(result['sampled_count'],2)
        self.assertEqual(result['out_of_volume_count'],1)
        self.assertAlmostEqual(result['by_state']['foam']['rendered_distance_cm_quantiles'][2],1)
        self.assertAlmostEqual(result['by_state']['foam']['native_distance_cm_quantiles'][2],-2)
        self.assertEqual(result['by_state']['foam']['opposite_surface_sign_count'],1)
        self.assertEqual(result['by_state']['foam']['rendered_inside_count'],0)
        np.testing.assert_allclose(result['by_state']['foam']['rendered_absolute_distance_cm_quantiles'],[1,1,1])
        self.assertEqual(result['by_state']['bubble']['count'],0)
        self.assertFalse(result['rendered_visibility_verified'])

    def test_alignment_empty_and_invalid_states(self):
        field=np.ones((2,2,2,1))
        self.assertEqual(surface_alignment([],[],field,field,[2,2,2],[0,0,0])['sampled_count'],0)
        with self.assertRaises(ValueError):
            surface_alignment([[1,-1,1,1,1,0,0,0]],[4],field,field,[2,2,2],[0,0,0])

    def test_empty_is_valid_but_not_emission(self):
        self.assertEqual(particle_rows({'position_count':0}).shape,(0,8))

    def test_actual_identity(self):
        rows=[[12,-1,1,2,3,4,5,6]]
        self.assertEqual(particle_rows({'position_count':1,'particle_rows':rows})[0,0],12)

    def test_missing_nonfinite_and_duplicate_rejected(self):
        row=[12,-1,1,2,3,4,5,6]
        for count,rows in ((1,[]),(2,[row,row]),(1,[[12,-1,float('nan'),2,3,4,5,6]]),(1,[[12,0,1,2,3,4,5,6]])):
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                particle_rows({'position_count':count,'particle_rows':rows})
