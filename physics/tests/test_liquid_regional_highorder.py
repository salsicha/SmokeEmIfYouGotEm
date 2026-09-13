import unittest
import numpy as np
from liquid_interface_global import layout, assemble, extract
from liquid_interface_highorder import advect_limited
from liquid_interface_regional_highorder import advect_regions
from audit_liquid_native_interface import validate_ledger
from diagnose_liquid_exterior_extensions import compare as compare_extensions


class RegionalHighOrderTest(unittest.TestCase):
    def fixture(self):
        sizes = np.array([[14, 7, 10]]*4); offsets = np.array([[0, 0], [10, 0], [0, 3], [10, 3]])
        z, y, x = np.indices((10, 10, 24))
        phi = ((z-4.3)*60-70*np.exp(-((x-10.4)/1.8)**2)*(.8+.2*np.cos((y-4.5)*.6))).astype('<f4').astype(float)
        velocity = np.zeros((*phi.shape, 3))+[30, 5, -3]
        solid = (x >= 11) & (x <= 13) & (y == 2) & (z <= 3)
        columns = []
        for owner, (ox, oy) in enumerate(offsets):
            for dy in range(7):
                for dx in range(14):
                    gx, gy = dx+ox, dy+oy
                    if not 2 <= gx < 22 or not 2 <= gy < 8:
                        continue
                    source = int(gx >= 12)+2*int(gy >= 5)
                    if source != owner:
                        columns.append((source, owner, int(gx-offsets[source, 0]), int(gy-offsets[source, 1]), dx, dy))
        return phi, velocity, solid, sizes, offsets, columns

    def test_layout_and_exact_assembly(self):
        p, _, _, sizes, offsets, columns = self.fixture()
        found, shape = layout(sizes, columns)
        np.testing.assert_array_equal(found, offsets)
        np.testing.assert_array_equal(assemble(extract(p, offsets, sizes), found, shape), p)
        copies = extract(p, offsets, sizes);copies[1][3, 2, 0] += .01
        with self.assertRaises(ValueError):
            assemble(copies, found, shape)
        with self.assertRaises(ValueError):
            layout(sizes, columns+columns)
        with self.assertRaises(ValueError):
            layout(sizes, [])

    def test_24_step_corner_matches_global(self):
        p, v, s, sizes, offsets, columns = self.fixture();h = np.array([70, 120, 60])
        fields = extract(p, offsets, sizes); velocities = extract(v, offsets, sizes); solids = extract(s, offsets, sizes)
        for _ in range(24):
            p, report = advect_limited(p, v, h, .5, [2, 2, 2], [22, 8, 8], True, solid=s)
            p = p.astype('<f4').astype(float)
            fields, status = advect_regions(fields, velocities, solids, h, .5, columns)
            self.assertTrue(report['candidate_step_valid'])
            validate_ledger(status.ravel(), sizes, 1, True)
        np.testing.assert_allclose(assemble(fields, offsets, p.shape), p, atol=.0001, rtol=0)

    def test_failure_is_not_fallback_success(self):
        p, v, s, sizes, offsets, columns = self.fixture();v *= 10000
        _, status = advect_regions(extract(p, offsets, sizes), extract(v, offsets, sizes), extract(s, offsets, sizes),
                                   np.array([70, 120, 60]), 1., columns)
        self.assertGreater(status[:, 1].sum(), 0)
        self.assertGreater(status[:, 7].sum(), 0)
        with self.assertRaises(ValueError):
            validate_ledger(status.ravel(), sizes, 1, True)

    def test_ledger_rejects_hidden_failures(self):
        valid = [216, 0, 0, 200, 12, 16, 1, 0]
        validate_ledger(valid, [[10, 10, 10]], 1, True)
        for word, value in [(0, 215), (1, 1), (2, 1), (3, 199), (4, 201), (5, 15), (6, 17), (7, 1)]:
            bad = valid.copy();bad[word] = value
            with self.assertRaises(ValueError):
                validate_ledger(bad, [[10, 10, 10]], 1, True)

    def test_exterior_disagreement_is_not_averaged_or_called_physical(self):
        p, _, _, sizes, offsets, _ = self.fixture();copies = extract(p, offsets, sizes)
        copies[1][3, 0, 0] += 7
        before = copies[1].copy();result = compare_extensions(copies, offsets, p.shape)
        self.assertFalse(result['whole_grid_agrees']);self.assertTrue(result['physical_xy_agrees'])
        np.testing.assert_array_equal(copies[1], before)
        copies[1][3, 2, 0] += 2
        self.assertFalse(compare_extensions(copies, offsets, p.shape)['physical_xy_agrees'])


if __name__ == '__main__':
    unittest.main()
