import unittest
from types import SimpleNamespace
import numpy as np
from chilko_triangle_ownership import preserve_triangle_support, support_offsets
from export_colorado_catalog_runtime import landscape_sample


def sample(xy):
    z = np.full(xy.shape[:-1], 100.)
    inferred = xy[..., 0] < 1.
    return dict(source_height_m=z, height_m=np.where(inferred, 98., z),
                inferred_bed=inferred, mapped_water=np.ones(z.shape, bool))


class TriangleOwnershipTests(unittest.TestCase):
    def test_stencil_matches_actual_positive_native_basis(self):
        z = np.zeros((3, 3)); z[1, 1] = 1
        offsets = support_offsets()
        self.assertEqual(len(offsets), 37)
        self.assertTrue((landscape_sample(z, 1-offsets[:, 1]/2, 1+offsets[:, 0]/2)>0).all())
        for r in range(-4, 5):
            for c in range(-4, 5):
                exists = ((offsets == [c*.5, -r*.5]).all(axis=1)).any()
                self.assertEqual(exists, landscape_sample(z, 1+r/4, 1+c/4)>0)

    def test_previously_valid_vertex_cut_lowered_protected_triangle_interior(self):
        x, y = np.meshgrid([0., 2.], [2., 0.]); xy = np.stack((x, y), -1)
        original = sample(xy)
        # x=1.5 is protected ground, but the old vertex-only export cut 0.5 m.
        self.assertEqual(landscape_sample(original['height_m'], .5, .75), 99.5)
        fixed = preserve_triangle_support(SimpleNamespace(sample=sample), xy, original)
        self.assertEqual(landscape_sample(fixed['height_m'], .5, .75), 100.)
        np.testing.assert_array_equal(original['height_m'], [[98., 100.], [98., 100.]])
        np.testing.assert_array_equal(fixed['inference_support_veto'], [[True, False], [True, False]])

    def test_deep_interior_retained_and_shared_vertices_identical(self):
        xy = np.array([[-4., 0.], [0., 0.], [2., 0.]])
        model = SimpleNamespace(sample=sample)
        whole = preserve_triangle_support(model, xy, sample(xy))
        np.testing.assert_array_equal(whole['height_m'], [98., 100., 100.])
        for i in range(3):
            part = preserve_triangle_support(model, xy[i:i+1], sample(xy[i:i+1]))
            for key in whole: np.testing.assert_array_equal(part[key], whole[key][i:i+1])
        reverse = preserve_triangle_support(model, xy[::-1], sample(xy[::-1]))
        for key in whole: np.testing.assert_array_equal(reverse[key][::-1], whole[key])

    def test_missing_support_and_invalid_inference_rejected(self):
        xy = np.array([[0., 0.]])
        def broken(q):
            r = sample(q); r['source_height_m'][0] = np.nan; return r
        with self.assertRaises(ValueError):
            preserve_triangle_support(SimpleNamespace(sample=broken), xy, sample(xy))
        r = sample(xy); r['inferred_bed'][:] = False
        with self.assertRaises(ValueError):
            preserve_triangle_support(SimpleNamespace(sample=sample), xy, r)

    def test_empty_inference_does_not_request_unneeded_halo(self):
        xy = np.array([[4., 0.]])
        def fail(q): raise AssertionError('No halo needed')
        r = preserve_triangle_support(SimpleNamespace(sample=fail), xy, sample(xy))
        self.assertFalse(r['inference_support_veto'].any())


if __name__ == '__main__': unittest.main()
