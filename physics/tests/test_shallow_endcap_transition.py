"""Partial constructive endcap evidence, NOT a closed-cell or runtime proof."""
from fractions import Fraction as F
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from audit_stored_bank_contour import cross
from three_wet_bank_envelope import certificate, value


class ShallowEndcapTransitionTests(unittest.TestCase):
    # Original shared-reserve replay frame414/source19466, not surveyed terrain.
    # Raw source SHA256: 9b8e68b71b25ef793b4cda668593dc82d73731475e09962c893dc5ee7188d1f3
    bed = tuple(map(F, (8.0471343994140625, 8.0450592041015625,
                       7.95037841796875, 8.0014495849609375)))
    depth = tuple(map(F, (0., .0020726395305246115,
                         .0076036825776100159, .016833245754241943)))
    origin = (F(0), F(0))
    edge = (F(177, 102400), F(0))
    endcap = (F(10668, 102400), F(1, 102400))

    def test_two_spans_with_shared_binary64_dry_witness(self):
        seam = (self.endcap[0], F(31, 102400))
        # Deliberately audit the actual rounded binary64 witness coordinates,
        # rather than a rational construction that native code cannot store.
        witness = tuple(map(F, (.1034755936750478, .0003045401247502055)))
        edge_inner = (F(.000729515625), F(0))
        for p in (self.edge, self.endcap, seam):
            buffer = (11600 + 100*p[0], -8600 - 100*p[1])
            for v in buffer:
                self.assertEqual(F(struct.unpack("f", struct.pack("f", float(v)))[0]), v)
        for p, q, a, b in ((self.edge, self.endcap, edge_inner, witness),
                           (self.endcap, seam, witness, witness)):
            self.assertGreater(cross(self.origin, p, q), 0)
            for determinant in (cross(p, q, b), cross(p, b, a), cross(self.origin, a, b)):
                self.assertGreaterEqual(determinant, 0)
            self.assertTrue(certificate(self.bed, self.depth, (p, q, q), 1))
            self.assertTrue(certificate(self.bed, self.depth, (self.origin, a, b), -1))
            for outer, inner in ((p, a), (q, b)):
                self.assertLessEqual(100*sum(abs(x-y) for x, y in zip(outer, inner)), F(1, 10))
            # Local signed-area identity includes both unclosed end rays.
            # This must not be presented as the entire cell's coverage proof.
            self.assertEqual(cross(self.origin, a, b)+cross(p, q, b)+cross(p, b, a),
                             cross(self.origin, p, q)+cross(self.origin, q, b)+cross(self.origin, a, p))

    def test_skipping_endcap_directly_to_original_next_row_is_not_wet(self):
        original_next = (F(3032, 102400), F(2, 102400))
        self.assertFalse(certificate(self.bed, self.depth, (self.edge, original_next, original_next), 1))

    def test_singleton_endcap_retains_close_witness_without_outer_strip(self):
        # Original frame399/source19466: an additional vertical GPU row is
        # not wholly wet. Retaining only its close dry witness repairs the
        # local fan; this is still not a complete native-cell certificate.
        depth = tuple(map(F, (0., .0020153657533228397,
                             .0075053912587463856, .01678166538476944)))
        edge = (F(3003, 102400), F(0))
        first = (F(4085, 102400), F(1, 102400))
        second = (F(4763, 102400), F(2, 102400))
        edge_inner = (F(float(edge[0])-(.001-128*sys.float_info.epsilon)), F(0))
        close = tuple(map(F, (.03889307043774284, .00000976858282226931)))
        next_inner = tuple(map(F, (.04551398667041141, .0000192164546170079)))
        old = tuple(map(F, (.0398912873524747, .0010084748524462786)))
        # The next vertex still needs its inward-rotated dry witness; the
        # singleton repair must not replace every inner point with a radial.
        radial_next = tuple(map(F, (.04551409160220575, .000019111522822677198)))
        self.assertGreater(value(self.bed, depth, radial_next), 0)
        self.assertFalse(certificate(self.bed, depth, (self.origin, close, radial_next), -1))
        self.assertLess(cross(self.origin, old, next_inner), 0)
        vertical = (first[0], second[1])
        self.assertFalse(certificate(self.bed, depth, (first, vertical, vertical), 1))
        for p, q, a, b in ((edge, first, edge_inner, close),
                           (first, second, close, next_inner)):
            self.assertTrue(certificate(self.bed, depth, (p, q, q), 1))
            self.assertTrue(certificate(self.bed, depth, (self.origin, a, b), -1))
            for tri in ((self.origin, p, q), (p, q, b), (p, b, a), (self.origin, a, b)):
                self.assertGreater(cross(*tri), 0)
            for outer, witness in ((p, a), (q, b)):
                self.assertLessEqual(sum(abs(x-y) for x, y in zip(outer, witness)), F(1, 1000))
            for outer in (p, q):
                for v in (11600+100*outer[0], -8600-100*outer[1]):
                    self.assertEqual(F(struct.unpack('f', struct.pack('f', float(v)))[0]), v)

    def test_second_row_connects_through_first_row_not_directly_to_axis(self):
        # Original shared-reserve frame389/source19466. Its second-row
        # direct-edge repair overshot the radial dry band. The actual first
        # row already provides the shared-edge connection; retain that path.
        depth = tuple(map(F, (0., .0019775389228016138,
                             .0074386345222592354, .016744846478104591)))
        edge = (F(487, 10240), F(0))
        first = (F(5547, 102400), F(1, 102400))
        second = (F(3097, 51200), F(1, 51200))
        width = .001 - 128*sys.float_info.epsilon
        # Audit rounded binary64 witnesses rather than ideal rational ones.
        def inner(p):
            factor = 1. - width / float(sum(p))
            return tuple(F(float(v)*factor) for v in p)
        a, b = inner(first), inner(second)
        self.assertTrue(certificate(self.bed, depth, (edge, first, first), 1))
        self.assertTrue(certificate(self.bed, depth, (first, second, second), 1))
        self.assertTrue(certificate(self.bed, depth, (self.origin, a, b), -1))
        self.assertFalse(certificate(self.bed, depth, (edge, second, second), 1))
        for tri in ((self.origin, first, second), (first, second, b),
                    (first, b, a), (self.origin, a, b)):
            self.assertGreater(cross(*tri), 0)
        for outer, witness in ((first, a), (second, b)):
            self.assertLessEqual(sum(abs(x-y) for x, y in zip(outer, witness)), F(1, 1000))


if __name__ == "__main__":
    unittest.main()
