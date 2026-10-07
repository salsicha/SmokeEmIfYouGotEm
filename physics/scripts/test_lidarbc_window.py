import unittest
import copy
from types import SimpleNamespace

import numpy as np
from affine import Affine
from pyproj import CRS, Transformer

from capture_lidarbc_window import validate_catalogue, validate_raster, validate_window
from build_chilko_evidence_grid import (validate_construction_chain, imagery_sampling_grid,
                                      imagery_sampling_points, supported_channel_core,
                                      correct_inferred_bed)
from compare_river_cook import anchor_evidence_kind
from capture_chilko_fwa_polygon import validate_polygon


class LidarBCWindowTests(unittest.TestCase):
    def test_offline_budget_does_not_expand_default_network_capture(self):
        from mosaic_lidarbc_crops import MAX_MOSAIC_PIXELS
        window=[0,0,3000,4000]
        with self.assertRaises(ValueError):validate_window(window)
        self.assertEqual(validate_window(window,MAX_MOSAIC_PIXELS),tuple(window))
        with self.assertRaises(ValueError):validate_window([0,0,6000,6000],MAX_MOSAIC_PIXELS)
        for budget in (0,-1,True,1.5):
            with self.assertRaises(ValueError):validate_window([0,0,1,1],budget)

    def test_bounded_integer_window(self):
        self.assertEqual(validate_window([442900, 5750760, 444100, 5752490]),
                         (442900, 5750760, 444100, 5752490))
        for window in ([0, 0, 0, 1], [2, 0, 1, 2], [0, 0, 9000, 9000],
                       [0.1, 0, 2, 2], [0, 0, float('nan'), 1]):
            with self.assertRaises(ValueError):
                validate_window(window)

    def test_only_public_native_dem_url_allowed(self):
        name = 'bc_092o091_xli1m_utm10_20230918_20231006.tif'
        url = 'https://nrs.objectstore.gov.bc.ca/gdwuts/092/092o/2023/dem/' + name
        row = dict(filename=name, s3Url=url, spacing='1 metre', projection='utm10')
        self.assertEqual(validate_catalogue(row, name), url)
        for bad in (dict(row, s3Url=url.replace('/dem/', '/dsm/')),
                    dict(row, s3Url=url.replace('https:', 'http:')),
                    dict(row, s3Url=url.replace('nrs.objectstore.gov.bc.ca', 'example.org')),
                    dict(row, spacing='10 metre'), dict(row, projection='utm11')):
            with self.assertRaises(ValueError):
                validate_catalogue(bad, name)

    def test_compound_datum_required(self):
        src = dict(crs=CRS(6653), res=(1., 1.), count=1, dtypes=('float32',),
                   transform=Affine(1., 0., 442900., 0., -1., 5752490.))
        validate_raster(SimpleNamespace(**src))
        for change in (dict(crs=CRS(3157)), dict(crs=CRS(32610)), dict(res=(2., 2.)),
                       dict(transform=Affine(1., .1, 0, 0, -1., 0))):
            with self.assertRaises(ValueError):
                validate_raster(SimpleNamespace(**dict(src, **change)))

    def test_explicit_construction_chain_is_not_an_implicit_named_reach(self):
        self.assertEqual(validate_construction_chain([38000, 39200], 55845).tolist(), [38000, 39200])
        for chain in ([-1, 10], [10, 10], [20, 10], [0, 60000], [0, float('inf')]):
            with self.assertRaises(ValueError):
                validate_construction_chain(chain, 55845)

    def test_existing_colour_report_still_imports(self):
        # Geometry registration must not remove the existing module's public import.
        import measure_chilko_water_colour
        self.assertTrue(callable(measure_chilko_water_colour.main))

    def test_cook_review_does_not_call_inferred_surface_measured(self):
        self.assertEqual(anchor_evidence_kind(dict(
            ws_reference_method='inferred_dem_channel_surface_pava_5m_not_water_survey')),
            'inferred_dem_surface_reference')
        self.assertEqual(anchor_evidence_kind({}), 'unclassified_reference_not_verified_measurement')
        self.assertEqual(anchor_evidence_kind(dict(anchor_evidence_kind='measured')), 'measured')
        with self.assertRaises(ValueError):
            anchor_evidence_kind(dict(anchor_evidence_kind='measured', ws_reference_method='inferred_dem'))

    def test_official_polygon_capture_requires_identity_closed_rings_and_full_response(self):
        feature = dict(properties=dict(WATERBODY_KEY=328961612, WATERBODY_TYPE='R',
                                      WATERSHED_GROUP_CODE='CHIR'),
                       geometry=dict(type='Polygon', coordinates=[[[-123.83, 51.90], [-123.82, 51.90],
                           [-123.82, 51.91], [-123.83, 51.91], [-123.83, 51.90]]]))
        data = dict(type='FeatureCollection', features=[feature])
        self.assertEqual(validate_polygon(data, 328961612), 5)
        with self.assertRaises(ValueError):
            validate_polygon(data, 123)
        with self.assertRaises(ValueError):
            validate_polygon(dict(data, exceededTransferLimit=True), 328961612)
        broken = copy.deepcopy(data)
        broken['features'][0]['geometry']['coordinates'][0].pop()
        with self.assertRaises(ValueError):
            validate_polygon(broken, 328961612)

    @staticmethod
    def imagery_item():
        band = dict(x0=440100., y0=5763070., cell_m=10., shape=[1573, 1461],
                    raster_bands=[dict(scale=.0001, offset=-.1, nodata=0)])
        return dict(epsg=32610, bands={key: copy.deepcopy(band) for key in ('blue', 'green', 'red', 'nir')},
                    window_utm_m=dict(xmin=440108.360686, ymax=5763063.844157))

    def test_native_pixel_origin_and_coordinate_transform(self):
        item = self.imagery_item()
        xc, yc = [443514.5, 443515.5], [5751531.5, 5751530.5]
        fr, fc = imagery_sampling_grid(xc, yc, item)
        tx = Transformer.from_crs(3157, 32610, always_xy=True)
        for row, north in enumerate(yc):
            for col, east in enumerate(xc):
                e, n = tx.transform(east, north)
                self.assertAlmostEqual(fc[row, col], (e - 440100.) / 10 - .5, places=9)
                self.assertAlmostEqual(fr[row, col], (5763070. - n) / 10 - .5, places=9)
        wrong_fc = (xc[0] - item['window_utm_m']['xmin']) / 10 - .5
        self.assertGreater(abs(fc[0, 0] - wrong_fc), .5)
        # Requested acquisition bounds do not define the returned raster origin.
        item['window_utm_m'] = dict(xmin=0, ymax=0)
        other_fr, other_fc = imagery_sampling_grid(xc, yc, item)
        np.testing.assert_array_equal(fr, other_fr)
        np.testing.assert_array_equal(fc, other_fc)

    def test_channel_core_retention_cannot_widen_banks_or_lower_high_ground(self):
        strict = np.array([False, False, False, False, False, True])
        interior = np.array([True, False, True, True, True, True])
        support = np.array([.75, .75, .49, .75, .75, .75])
        dem = np.array([100.2, 100.2, 100.2, 100.3, 100.2, 100.2])
        surface = np.array([100., 100., 100., 100., np.nan, 100.])
        original = dem.copy()
        np.testing.assert_array_equal(supported_channel_core(strict, interior, support, dem, surface),
                                      [True, False, False, False, False, False])
        np.testing.assert_array_equal(dem, original)

    def test_depth_calibration_preserves_dry_ground_and_inferred_rocks(self):
        bed = np.array([101., 98., 99.7, 97.])
        classes = np.array([0, 2, 4, 2])
        station = np.array([np.nan, 5., 5., 10.])
        surface = np.array([np.nan, 100., 100., 100.])
        correction = dict(station=[0., 10.], delta=[-.2, -.4])
        actual = correct_inferred_bed(bed, classes, station, surface, correction)
        np.testing.assert_allclose(actual, [101., 97.7, 99.7, 96.6])
        np.testing.assert_array_equal(bed, [101., 98., 99.7, 97.])
        np.testing.assert_array_equal(classes, [0, 2, 4, 2])
        raised = correct_inferred_bed(bed, classes, station, surface,
                                     dict(station=[0., 10.], delta=[10., 10.]))
        np.testing.assert_allclose(raised, [101., 99.95, 99.7, 99.95])
        for corr in (dict(station=[0., 0.], delta=[-.2, -.4]),
                     dict(station=[0., 10.], delta=[np.nan, -.4]),
                     dict(station=[0., 10.], delta=[-.2])):
            with self.assertRaises(ValueError):
                correct_inferred_bed(bed, classes, station, surface, corr)

    def test_imagery_edges_are_not_extrapolated_into_new_whitewater(self):
        item = self.imagery_item()
        for x, y in (([440000], [5751500]), ([455000], [5751500]),
                     ([443500], [5747000]), ([443500], [5764000]),
                     ([float('nan')], [5751500])):
            with self.assertRaises(ValueError):
                imagery_sampling_grid(x, y, item)

    def test_runtime_drape_and_evidence_use_identical_pixel_registration(self):
        from export_chilko_evidence_runtime import imagery_sampling_points as runtime_sampling
        item = self.imagery_item()
        x, y = [443514.5, 443515.5], [5751531.5, 5751530.5]
        east, north = np.meshgrid(x, y)
        expected = imagery_sampling_grid(x, y, item)
        actual = runtime_sampling(east, north, item)
        for a, b in zip(expected, actual):
            np.testing.assert_array_equal(a, b)
        for east, north in (([], []), ([443514.5], [5751531.5, 5751530.5])):
            with self.assertRaises(ValueError):
                imagery_sampling_points(east, north, item)

    def test_unverified_imagery_geometry_and_encoding_are_rejected(self):
        for field, value in (('cell_m', 20), ('shape', [1, 1]), ('x0', float('nan')),
                             ('raster_bands', [dict(scale=.0001, offset=0, nodata=0)])):
            item = self.imagery_item()
            item['bands']['red'][field] = value
            with self.assertRaises(ValueError):
                imagery_sampling_grid([443500], [5751500], item)
        item = self.imagery_item()
        item['epsg'] = 3157
        with self.assertRaises(ValueError):
            imagery_sampling_grid([443500], [5751500], item)


if __name__ == '__main__':
    unittest.main()
