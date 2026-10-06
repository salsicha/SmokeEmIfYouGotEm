"""Read-only staging guards, without importing Unreal or touching real assets."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[2]/'unreal/Scripts/stage_south_fork_triangle_review.py'
spec=importlib.util.spec_from_file_location('triangle_staging',SCRIPT)
staging=importlib.util.module_from_spec(spec);spec.loader.exec_module(staging)


class TriangleStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        def put(path,data):
            path=self.root/path;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data);return staging.sha(path)
        self.put=put
        level_hash=put(staging.LEVEL_FILE,b'preserved review')
        self.hash_patch=patch.object(staging,'BEFORE_SHA',level_hash)
        self.hash_patch.start();self.addCleanup(self.hash_patch.stop)
        geometry_hash=put('source/bed.tif',b'captured and inferred geometry')
        fbx_hash=put('source/terrain.fbx',b'triangles')
        mesh_hash=put('source/engine_mesh_source.npz',b'vertices')
        self.save('source/manifest.json',dict(shared_geometry_sha256=geometry_hash,shared_geometry_path='source/bed.tif'))
        self.save(staging.SOURCE,dict(source_geometry_sha256=geometry_hash,
            source_geometry_manifest='source/manifest.json',fbx='source/terrain.fbx',
            fbx_sha256=fbx_hash,mesh_source_sha256=mesh_hash))
        depth_hash=put(Path(staging.NEW_FIELDS)/'h.npy',b'exported depth')
        self.fields=dict(production_promoted=False,all_bands_passed=False,
            review=dict(source_geometry_sha256=geometry_hash,source_bed_sampling='render_triangles',saved_frame_sanity=[dict(passed=True)]),
            bands=[dict(arrays=dict(h=dict(file='h.npy',sha256=depth_hash)))])
        self.start=dict(source_geometry_sha256=geometry_hash,source_bed_sampling='render_triangles',
            cooked_fields_dir=staging.NEW_FIELDS,coordinate_map_path=staging.NEW_FIELDS+'/coordinate_map.json')
        self.flush()

    def save(self,path,data):self.put(path,json.dumps(data).encode())
    def flush(self):
        self.save(Path(staging.NEW_FIELDS)/'manifest.json',self.fields)
        self.save(Path(staging.NEW_FIELDS)/'engine_start.json',self.start)

    def test_valid_unaccepted_package_is_read_only(self):
        result=staging.validate_package(self.root)
        self.assertEqual(result[0],self.fields)
        self.assertFalse((self.root/staging.BACKUP).exists())
        self.assertEqual((self.root/staging.LEVEL_FILE).read_bytes(),b'preserved review')

    def test_changed_map_is_not_overwritten(self):
        self.put(staging.LEVEL_FILE,b'user changes')
        with self.assertRaisesRegex(ValueError,'map changed'):staging.validate_package(self.root)

    def test_previous_attempt_must_be_inspected(self):
        for path in (staging.BACKUP,staging.REPORT):
            with self.subTest(path=path):
                self.put(path,b'prior evidence')
                with self.assertRaises(FileExistsError):staging.validate_package(self.root)
                (self.root/path).unlink()

    def test_source_geometry_bytes_verified(self):
        self.put('source/bed.tif',b'different terrain')
        with self.assertRaisesRegex(ValueError,'identity mismatch'):staging.validate_package(self.root)

    def test_bilinear_package_rejected(self):
        for owner in (self.fields['review'],self.start):
            with self.subTest(owner=owner):
                owner['source_bed_sampling']='bilinear';self.flush()
                with self.assertRaisesRegex(ValueError,'Triangle sampling'):staging.validate_package(self.root)
                owner['source_bed_sampling']='render_triangles'

    def test_wrong_start_package_rejected(self):
        self.start['cooked_fields_dir']=staging.OLD_FIELDS;self.flush()
        with self.assertRaisesRegex(ValueError,'different fields'):staging.validate_package(self.root)

    def test_changed_export_and_mesh_rejected(self):
        for path,message in ((Path(staging.NEW_FIELDS)/'h.npy','array changed'),('source/terrain.fbx','Mesh export')):
            with self.subTest(path=path):
                previous=(self.root/path).read_bytes();self.put(path,b'changed')
                with self.assertRaisesRegex(ValueError,message):staging.validate_package(self.root)
                self.put(path,previous)

    def test_unsafe_history_rejected(self):
        for history in ([],[dict(passed=False)]):
            self.fields['review']['saved_frame_sanity']=history;self.flush()
            with self.assertRaisesRegex(ValueError,'Unsafe'):staging.validate_package(self.root)

    def test_no_implicit_acceptance(self):
        self.fields['all_bands_passed']=True;self.flush()
        with self.assertRaisesRegex(ValueError,'unaccepted'):staging.validate_package(self.root)
