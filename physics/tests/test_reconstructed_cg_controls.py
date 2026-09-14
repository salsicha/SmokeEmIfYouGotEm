import math
import struct
import unittest
from audit_reconstructed_cg_controls import COUNTS, EXPONENTS, audit


def fixture(control):
    data = bytearray(struct.pack('<III', 0x52534343, 1, 6))
    for tag, n in enumerate(COUNTS):
        zero = control == 'zero-rhs'
        data.extend(struct.pack('<IIIIIId', tag, n, 0, 0 if zero else 1, 0, int(zero), 1.))
        values = [0.] * n if zero else [math.ldexp((1., -1., 0.)[i % 3], EXPONENTS[tag]) for i in range(n)]
        raw = struct.pack('<' + 'd'*n, *values)
        data.extend(raw); data.extend(raw)
    return data


class ControlAuditTests(unittest.TestCase):
    def test_both_explicit_controls(self):
        for control in ('zero-rhs', 'identity-range'):
            result = audit(fixture(control), control)
            self.assertTrue(result['passed'])
            self.assertFalse(result['actual_source_or_physical_history_accepted'])

    def test_original_source_magic_rejected(self):
        data = fixture('zero-rhs'); struct.pack_into('<I', data, 0, 0x52534347)
        with self.assertRaises(ValueError): audit(data, 'zero-rhs')

    def test_lost_smallest_subnormal_rejected(self):
        data = fixture('identity-range'); data[44:52] = bytes(8)
        with self.assertRaises(ValueError): audit(data, 'identity-range')

    def test_false_zero_termination_rejected(self):
        data = fixture('identity-range'); struct.pack_into('<I', data, 32, 1)
        with self.assertRaises(ValueError): audit(data, 'identity-range')

    def test_shape_truncation_and_trailing_bytes_rejected(self):
        data = fixture('zero-rhs')
        for bad in (data[:-1], data + b'\0'):
            with self.assertRaises(ValueError): audit(bad, 'zero-rhs')
        struct.pack_into('<I', data, 16, 1)
        with self.assertRaises(ValueError): audit(data, 'zero-rhs')

    def test_wrong_control_rejected(self):
        with self.assertRaises(ValueError): audit(fixture('identity-range'), 'zero-rhs')
        with self.assertRaises(ValueError): audit(fixture('zero-rhs'), 'unknown')


if __name__ == '__main__': unittest.main()
