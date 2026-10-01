import gzip
import struct
import unittest
from water_feature_cache_stages import decode_configuration, interval_clock, beginning_frame_snapshot


def record():
    # Independent field-by-field packing, not the decoder's struct layout.
    return b''.join((struct.pack('<i', 208), struct.pack('<3i', 80, 21, 39),
        struct.pack('<2f', .0125, .052), struct.pack('<9f', *range(9)),
        struct.pack('<3i', 0, 0, 0), struct.pack('<3f', 0, 0, 0),
        struct.pack('<16f', *range(16)), struct.pack('<9i', 80, 21, 39, 0, 0, 0, 80, 21, 39),
        struct.pack('<3f', 0, 0, 0), struct.pack('<f', 20), b'C01\0'))


def guarded():
    if not s7.timePerFrame:
        phiTmp_s7.copyFrom(phi_s7)
        velTmp_s7.copyFrom(vel_s7)
    return s7.timePerFrame  # Shared continuation, like the native advection body.


def unguarded():
    phiTmp_s7.copyFrom(phi_s7)
    velTmp_s7.copyFrom(vel_s7)


def wrong_guard():
    if s7.timePerFrame:
        phiTmp_s7.copyFrom(phi_s7)
        velTmp_s7.copyFrom(vel_s7)


def wrong_source():
    if not s7.timePerFrame:
        phiTmp_s7.copyFrom(phiParts_s7)
        velTmp_s7.copyFrom(vel_s7)


class CacheStageTests(unittest.TestCase):
    def test_independent_packed_configuration_layout(self):
        data = record()
        self.assertEqual(len(data), 204)
        r = decode_configuration(gzip.compress(data))
        self.assertEqual(r['resolution'], [80, 21, 39])
        self.assertEqual(r['base_resolution'], [80, 21, 39])
        self.assertEqual(r['resolution_max'], [80, 21, 39])
        self.assertAlmostEqual(r['dimensionless_dx'], 1/80)
        self.assertAlmostEqual(r['last_timestep_native'], .052)
        self.assertEqual(r['time_total_native'], 20)
        self.assertEqual(r['object_matrix'], list(range(16)))
        self.assertFalse(r['accepted'])

    def test_configuration_version_length_and_gzip_rejected(self):
        for raw in (record()[:-1], record()+b'x', record()[:-4]+b'C02\0', record()+b'x'*10000):
            with self.assertRaises(ValueError):
                decode_configuration(gzip.compress(raw))
        for raw in (b'not gzip', gzip.compress(record())[:-6]):
            with self.assertRaises(ValueError):
                decode_configuration(raw)

    def test_configuration_invalid_floats_dimensions_and_clock(self):
        for offset, fmt, value in ((4, '<i', 0), (148, '<i', 0), (16, '<f', 0),
                                    (20, '<f', -1), (24, '<f', float('nan')), (196, '<f', -1)):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                data = bytearray(record()); struct.pack_into(fmt, data, offset, value)
                decode_configuration(gzip.compress(data))

    def test_clock_separates_native_physical_and_playback_time(self):
        r = interval_clock({'time_total_native': 19.}, {'time_total_native': 19.3125}, 3, 24)
        self.assertEqual(r['native_interval_error'], 0)
        self.assertEqual(r['playback_interval_seconds'], .125)
        self.assertEqual(r['native_interval_in_physical_seconds'], .125)
        accelerated = interval_clock({'time_total_native': 0.}, {'time_total_native': .625}, 3, 24, 2)
        self.assertEqual(accelerated['native_interval_error'], 0)
        self.assertEqual(accelerated['playback_interval_seconds'], .125)
        self.assertEqual(accelerated['native_interval_in_physical_seconds'], .25)

    def test_clock_invalid_or_nonmonotone_is_not_retimed(self):
        for a, b, span, fps, scale in ((1, 1, 1, 24, 1), (2, 1, 1, 24, 1),
                                       (0, 1, 0, 24, 1), (0, 1, 1, 0, 1), (0, 1, 1, 24, -1)):
            with self.assertRaises(ValueError):
                interval_clock({'time_total_native': a}, {'time_total_native': b}, span, fps, scale)

    def test_actual_guard_pattern_inspected_without_execution(self):
        # Undefined native-like globals would fail if this function were called.
        r = beginning_frame_snapshot(guarded, 's7', 'phi_s7', 'vel_s7', 'phiTmp_s7', 'velTmp_s7')
        self.assertTrue(r['copy_only_at_frame_beginning'])
        self.assertEqual(r['condition'], 'not solver.timePerFrame')

    def test_other_copy_policies_and_wrong_sources_fail_explicitly(self):
        for function in (unguarded, wrong_guard, wrong_source):
            with self.assertRaises(ValueError):
                beginning_frame_snapshot(function, 's7', 'phi_s7', 'vel_s7', 'phiTmp_s7', 'velTmp_s7')


if __name__ == '__main__':
    unittest.main()
