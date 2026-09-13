"""Exact source-array reuse checks, including self-consistent but wrong data."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from export_cartesian_runtime_atlas import verified_packet_dependencies, array_meta, write_json


class DependencyReuseTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="raftsim-atlas-dependency-")
        self.root = Path(self.temporary.name)
        self.directory = self.root/"region_0000"
        self.directory.mkdir()
        self.record = dict(name="region_0000", geometry_sha256="captured-source-identity")
        self.origin = np.array([-5432., 3600.])
        self.expected = dict(bed=np.arange(321*321, dtype="<f8").reshape(321, 321)/1024.,
                             captured_water_mask=np.ones((321, 321), dtype="uint8"))
        arrays = {}
        for name, values in self.expected.items():
            path = self.directory/f"{name}.npy"
            np.save(path, values)
            arrays[name] = array_meta(path, self.directory, values.shape, values.dtype.str)
        self.manifest = dict(schema="raftsim.cooked_flow_fields.v1", coordinate_system="cartesian_east_north_m",
            source_geometry_sha256=self.record["geometry_sha256"], source_elevation_datum_m=220.,
            grid=dict(nx=321, ny=321, dx_m=1., dy_m=1., origin_x_m=-5432., origin_y_m=3600.),
            bands=[dict(band_id="median_runnable", arrays=arrays)])
        self.save_manifest()

    def tearDown(self):
        self.temporary.cleanup()

    def save_manifest(self):
        write_json(self.directory/"manifest.json", self.manifest)

    def verify(self):
        return verified_packet_dependencies(self.root, self.record, self.origin, 220., self.expected)

    def test_exact_files_are_reused_without_mutation(self):
        before = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        actual = self.verify()
        self.assertEqual(set(actual), set(self.expected))
        for name, path in actual.items(): self.assertEqual(path, (self.directory/f"{name}.npy").resolve())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.directory.iterdir()})

    def replace_array(self, name, values, rehash=True):
        path = self.directory/f"{name}.npy"
        np.save(path, values)
        if rehash:
            self.manifest["bands"][0]["arrays"][name] = array_meta(path, self.directory, values.shape, values.dtype.str)
            self.save_manifest()

    def test_corrupt_file_rejected(self):
        self.replace_array("bed", self.expected["bed"]+1., rehash=False)
        with self.assertRaises(AssertionError): self.verify()

    def test_rehashed_wrong_bed_rejected(self):
        self.replace_array("bed", self.expected["bed"]+.00001)
        with self.assertRaises(AssertionError): self.verify()

    def test_rehashed_wrong_wet_mask_rejected(self):
        mask = self.expected["captured_water_mask"].copy()
        mask[100, 100] = 0
        self.replace_array("captured_water_mask", mask)
        with self.assertRaises(AssertionError): self.verify()

    def test_precision_reduction_rejected(self):
        self.replace_array("bed", self.expected["bed"].astype("<f4"))
        with self.assertRaises(AssertionError): self.verify()

    def test_wrong_source_frame_rejected(self):
        for field, value in (("source_geometry_sha256", "other-source"),
                             ("source_elevation_datum_m", 221.),
                             ("coordinate_system", "station_lateral_m")):
            original = self.manifest[field]
            self.manifest[field] = value
            self.save_manifest()
            with self.assertRaises(AssertionError): self.verify()
            self.manifest[field] = original
        self.manifest["grid"]["origin_y_m"] += 1.
        self.save_manifest()
        with self.assertRaises(AssertionError): self.verify()


if __name__ == "__main__":
    unittest.main()
