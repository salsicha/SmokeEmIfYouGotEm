import copy
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_native_retirement import crossing, indexed, verify_partition, verify_population


class NativeRetirementTest(unittest.TestCase):
    def setUp(self):
        self.profile = dict(domain={'native_face_bounds_m': [[0, 0], [1, 1]]},
                            packed_vectors=[[1, 0, 0], [0, 1, 0], [50, 50, 10],
                                            [100, 100, 100], [50, 50, 50], [2, 2, 2],
                                            [6, 6, 2], [300, 300, 100]]+[[10, 70, -5]]*8)

    def test_all_outgoing_faces_and_above_stage_spray(self):
        for end, face, row in (([-10, -25, 50], 0, 0), ([120, -25, 80], 1, 2),
                               ([25, 10, 50], 2, 4), ([25, -120, 50], 3, 6)):
            result = crossing([25, -25, 50], end, self.profile)
            self.assertEqual(result[:2], (face, row))
            self.assertTrue(0 < result[2] < 1)

    def test_inside_and_exact_outer_edge_are_not_exits(self):
        for end in ([90, -50, 50], [100, -50, 50]):
            self.assertIsNone(crossing([25, -25, 50], end, self.profile))

    def test_corner_floor_roof_rejected(self):
        for end in ([125, -125, 50], [150, -50, -200], [150, -50, 400]):
            with self.assertRaisesRegex(ValueError, 'Floor, roof or ambiguous'):
                crossing([50, -50, 50], end, self.profile)

    def test_nonfinite_and_exterior_origins_rejected(self):
        for start in ([101, -50, 50], [50, -50, 9], [np.nan, 0, 50]):
            with self.assertRaisesRegex(ValueError, 'origin'):
                crossing(start, [120, -50, 50], self.profile)

    def test_dry_incoming_and_below_bed_rejected(self):
        for row in ([10, 70, 1], [70, 70, -1], [60, 70, -1]):
            p = copy.deepcopy(self.profile);p['packed_vectors'][10] = row
            with self.assertRaisesRegex(ValueError, 'parent face'):
                crossing([50, -25, 50], [120, -25, 50], p)

    def test_crossing_row_not_endpoint_row(self):
        # At x=100, y=40; endpoint y=70 must not select the second row.
        result = crossing([90, -10, 50], [110, -70, 50], self.profile)
        self.assertEqual(result[:2], (1, 2))

    def test_pointwise_bed_accepts_clearance_and_rejects_real_leak(self):
        p=copy.deepcopy(self.profile);p['packed_vectors'][10]=[60,70,-5]
        queried=[]
        def bed(face,tangent):
            queried.append((face,tangent));return 40
        result=crossing([90,-10,50],[110,-70,50],p,bed_query=bed)
        self.assertEqual(result[:2],(1,2));self.assertEqual(queried,[(1,40)])
        with self.assertRaisesRegex(ValueError,'parent face'):
            crossing([90,-10,50],[110,-70,50],self.profile,bed_query=lambda f,t:55)

    def test_exact_bed_does_not_allow_inlet_dry_or_invalid_geometry(self):
        for stage,speed,bed in ((70,5,40),(30,-5,40),(70,-5,np.nan)):
            p=copy.deepcopy(self.profile);p['packed_vectors'][10]=[10,stage,speed]
            with self.assertRaises(ValueError):
                crossing([90,-25,50],[110,-25,50],p,bed_query=lambda f,t:bed)

    def test_fraction_error_is_derived_from_frame_not_observed_time(self):
        local = crossing([90, -25, 50], [120, -25, 50], self.profile)
        p = copy.deepcopy(self.profile)
        p['domain']['native_face_bounds_m'] = [[120, 0], [121, 1]]
        p['packed_vectors'][2][0] = 12050
        translated = crossing([12090, -25, 50], [12120, -25, 50], p)
        self.assertEqual(local[:3], translated[:3])
        self.assertGreater(translated[3], local[3])
        self.assertLess(translated[3], 0.001)

    def fixture(self):
        # Two native particles: one survivor changing owners; one true outlet.
        b = np.zeros((10, 2), dtype='<u4')
        b[:3] = np.array([[30, 120], [-25, -25], [50, 50]], dtype='<f4').view('<u4')
        b[3:6] = np.array([[25, 90], [-25, -25], [50, 50]], dtype='<f4').view('<u4')
        b[6:8] = [[0, 1], [5, 5]];b[8:] = [[0, 0], [0, 1]]
        words = np.zeros((10, 4), dtype='<u4');words[:, 2] = b[:, 0]
        refs = np.zeros((4, 2), dtype='<u4');refs[2] = [0, 0]
        handles = np.zeros((4, 2), dtype='<u4');handles[2] = [0, 0x80000001]
        after = b[:, :1].copy();after[6:8, 0] = handles[2]
        ew = np.zeros((10, 2), dtype='<u4');ew[:, 0] = b[:, 1]
        er = np.zeros((2, 2), dtype='<u4');er[0] = [0, 1]
        records = np.zeros((2, 4), dtype='<u4')
        records[0] = [2, 1, 2, np.array(1/3, dtype='<f4').view('<u4').item()]
        return dict(before={0: b, 1: b[:, :0]}, after={0: b[:, :0], 1: after},
                    words=words, refs=refs, counts=np.array([0, 1], dtype='<u4'), caps=[2, 2], handles=handles,
                    exit_words=ew, exit_refs=er, exit_records=records,
                    exit_counts=np.array([[0, 1, 0, 0, 1], [0, 0, 0, 0, 0]], dtype='<u4'), exit_caps=[2, 0],
                    control=np.array([1, 0, 2, 1], dtype='<u4'), destinations={0: np.array([1, -1]), 1: np.array([])},
                    classify=lambda a, b: crossing(a, b, self.profile), position=0, start=3, index_plane=6)

    def test_exact_partition_payload_and_handles(self):
        retired, changed = verify_partition(**self.fixture())
        self.assertEqual(retired[0][:4], (0, 1, 1, 2));self.assertEqual(changed, 1)

    def test_corrupt_gate_count_payload_and_crossing_rejected(self):
        for field, index in [('control', 0), ('exit_counts', (0, 4)), ('exit_words', (9, 0)),
                             ('exit_records', (0, 2)), ('exit_records', (0, 3))]:
            with self.subTest(field=field, index=index):
                d = self.fixture();d[field][index] = 0xffffffff
                with self.assertRaises(ValueError):
                    verify_partition(**d)

    def test_duplicate_reference_and_missing_source_rejected(self):
        d = self.fixture();d['exit_refs'][0] = [0, 0]
        with self.assertRaisesRegex(ValueError, 'Duplicated'):
            verify_partition(**d)
        d = self.fixture();d['exit_counts'][:] = 0;d['control'][3] = 0
        with self.assertRaisesRegex(ValueError, 'omitted'):
            verify_partition(**d)

    def test_native_sink_corruption_and_wrong_destination_rejected(self):
        d = self.fixture();d['after'][1][0, 0] ^= 1
        with self.assertRaisesRegex(ValueError, 'Native survivor payload'):
            verify_partition(**d)
        d = self.fixture();d['destinations'][0][0] = 0
        with self.assertRaisesRegex(ValueError, 'misrouted'):
            verify_partition(**d)

    def test_interior_cannot_be_retired(self):
        d = self.fixture();d['destinations'][0][1] = 1
        with self.assertRaisesRegex(ValueError, 'not exterior'):
            verify_partition(**d)

    def test_wrong_finite_crossing_time_rejected(self):
        d = self.fixture()
        d['exit_records'][0, 3] = np.array(0.9, dtype='<f4').view('<u4')
        with self.assertRaisesRegex(ValueError, 'independent segment'):
            verify_partition(**d)

    def test_duplicate_birth_identity_rejected(self):
        d = self.fixture();d['before'][0][9, 1] = 0
        with self.assertRaisesRegex(ValueError, 'Duplicated birth'):
            indexed(d['before'], [8, 9])

    def test_births_with_retirements_are_accounted_separately(self):
        current = {(0, 0): (1, np.array([0], dtype='<u4')), (1, 1): (1, np.array([1], dtype='<u4'))}
        self.assertEqual(verify_population(current, {(0, 0), (1, 0)}, {(1, 0)}, {0: 0, 1: 1}, 0), {(1, 1)})

    def test_equal_total_cannot_hide_loss_with_birth(self):
        current = {(1, 1): (1, np.array([1], dtype='<u4'))}
        with self.assertRaisesRegex(ValueError, 'Lost'):
            verify_population(current, {(0, 0), (1, 0)}, {(1, 0)}, {0: 0, 1: 1}, 0)

    def test_retired_identity_cannot_be_reborn(self):
        current = {(1, 0): (1, np.array([0], dtype='<u4'))}
        with self.assertRaisesRegex(ValueError, 'resurrected'):
            verify_population(current, {(1, 0)}, {(1, 0)}, {0: 0, 1: 1}, 0)

    def test_spawn_count_owner_and_sequence_must_match(self):
        current = {(1, 1): (1, np.array([1], dtype='<u4'))}
        with self.assertRaisesRegex(ValueError, 'spawn plan'):
            verify_population(current, {(1, 0)}, {(1, 0)}, {0: 1, 1: 0}, 0)
        with self.assertRaisesRegex(ValueError, 'initial owner'):
            verify_population({(1, 1): (0, np.array([1], dtype='<u4'))}, {(1, 0)}, {(1, 0)}, {0: 0, 1: 1}, 0)
        with self.assertRaisesRegex(ValueError, 'sequence'):
            verify_population({(1, 3): (1, np.array([3], dtype='<u4'))}, {(1, 0)}, {(1, 0)}, {0: 0, 1: 1}, 0)


if __name__ == '__main__':
    unittest.main()
