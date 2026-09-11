"""A manifest label cannot substitute for matching the actual geometry bytes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/scripts'))
from export_south_fork_survey_review_fields import validate_geometry_source


class ExportGeometryIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.bed=self.root/'bed.tif'
        self.bed.write_bytes(b'candidate geometry bytes')
        self.sha=hashlib.sha256(self.bed.read_bytes()).hexdigest()
        self.manifest=self.root/'manifest.json'
        self.record={'shared_geometry_path':'bed.tif','shared_geometry_sha256':self.sha}
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.record))

    def test_matching_variant_allowed(self):
        self.assertEqual(validate_geometry_source(self.manifest,self.sha,self.root),self.record)

    def test_registered_mesh_uses_mesh_hash_not_parent_raster(self):
        from south_fork_geometry_source import REGISTERED_SCHEMA
        self.record={'schema':REGISTERED_SCHEMA,'mesh_path':'bed.tif','mesh_sha256':self.sha,
            'parent_raster_sha256':'0'*64}
        self.save()
        self.assertEqual(validate_geometry_source(self.manifest,self.sha,self.root),self.record)
        with self.assertRaises(ValueError):validate_geometry_source(self.manifest,'0'*64,self.root)
        self.bed.write_bytes(b'changed mesh connectivity')
        with self.assertRaises(ValueError):validate_geometry_source(self.manifest,self.sha,self.root)

    def test_irregular_geometry_never_falls_back_to_raster(self):
        from south_fork_geometry_source import require_sampling_kind
        require_sampling_kind(True,'registered_triangles')
        for method in ('bilinear','render_triangles'):
            require_sampling_kind(False,method)
            with self.assertRaises(ValueError):require_sampling_kind(True,method)
        with self.assertRaises(ValueError):require_sampling_kind(False,'registered_triangles')

    def test_changed_actual_geometry_rejected(self):
        self.bed.write_bytes(b'changed after cooking')
        with self.assertRaises(ValueError):
            validate_geometry_source(self.manifest,self.sha,self.root)

    def test_other_cook_geometry_rejected(self):
        with self.assertRaises(ValueError):
            validate_geometry_source(self.manifest,'0'*64,self.root)

    def test_outside_project_geometry_rejected_before_read(self):
        self.record['shared_geometry_path']='../outside.tif'
        self.save()
        with self.assertRaises(ValueError):
            validate_geometry_source(self.manifest,self.sha,self.root)


if __name__=='__main__':unittest.main()
