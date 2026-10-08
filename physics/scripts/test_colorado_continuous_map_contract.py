import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np

from build_colorado_continuous_map_contract import ROOT, build, sha, rapid_profile_sources, geographic_takeout
from build_colorado_continuous_assembly import rebase_chart


class ContinuousMapContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'tmp', prefix='continuous-contract-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fields = self.root/'cooked_flow_fields'; fields.mkdir()
        terrain = self.root/'terrain'; terrain.mkdir()
        arrays = {}
        for key, array in [('bed', np.full((11, 20), 100.)), ('h', np.full((11, 20), 2.)),
                           ('wet_mask', np.ones((11, 20), dtype=np.uint8))]:
            np.save(fields/(key+'.npy'), array)
            arrays[key] = dict(file=key+'.npy')
        grid = dict(nx=20, ny=11, dx_m=2., dy_m=2., origin_x_m=100., origin_y_m=-10.)
        (fields/'manifest.json').write_text(json.dumps(dict(grid=grid, bands=[dict(band_id='test', arrays=arrays)])))
        frame = dict(horizontal_origin_epsg6404_m=[200., 300.], vertical_datum_m=90.)
        (terrain/'manifest.json').write_text(json.dumps(frame))
        mapping = dict(frame, schema='raftsim.curved_river_coordinate_map.v1', world_y_sign=-1,
                       points=[[float(s), float(s), 0., 0., 1.] for s in range(0, 302, 2)])
        (self.root/'coordinate_map.json').write_text(json.dumps(mapping))
        (self.root/'moving_water_streaming.json').write_text('{}')
        manifest = dict(schema='raftsim.colorado_continuous_runtime_candidate.v1',
            terrain_solver_bed_max_error_m=0., source_core_interval_m=[100., 138.], full_river_coverage=False,
            files_sha256={p.relative_to(self.root).as_posix(): sha(p) for p in self.root.rglob('*') if p.is_file()})
        (self.root/'manifest.json').write_text(json.dumps(manifest))

    def call(self, start=112., finish=126.):
        return build(self.root, 'L_Colorado_ContractUnitTest', start, finish)

    def test_global_launch_and_wet_collision_coordinates(self):
        result = self.call()
        self.assertEqual(result['launch']['station_m'], 112.)
        self.assertEqual(result['launch']['location_cm'][:2], [11200., 0.])
        self.assertAlmostEqual(result['launch']['location_cm'][2], 1200.-56/3.4)
        self.assertEqual(result['wet_bed_collision_probes_cm'][0], [10000., 1000., 1000.])
        self.assertEqual(len(result['wet_bed_collision_probes_cm']), 220)
        self.assertFalse(result['full_river_coverage'])
        self.assertEqual(result['map_package'], '/Game/RaftSim/Maps/Continuous/L_Colorado_ContractUnitTest')

    def chilko_fixture(self):
        for name in ('coordinate_map.json','terrain/manifest.json'):
            path=self.root/name;data=json.loads(path.read_text())
            data['horizontal_origin_m']=data.pop('horizontal_origin_epsg6404_m')
            data.update(river_id='chilko_river_bc',horizontal_crs='EPSG:3157',
                        vertical_reference='CGVD2013 (EPSG:6647)',world_y_sign=-1)
            if name.startswith('terrain'):data['schema']='raftsim.continuous_landscape.v1'
            path.write_text(json.dumps(data))
        path=self.root/'cooked_flow_fields/manifest.json';data=json.loads(path.read_text())
        data['river_id']='chilko_river_bc';path.write_text(json.dumps(data))
        path=self.root/'manifest.json';data=json.loads(path.read_text())
        data.update(schema='raftsim.continuous_runtime_candidate.v1',river_id='chilko_river_bc')
        data['files_sha256']={name:sha(self.root/name) for name in data['files_sha256']}
        path.write_text(json.dumps(data))

    def test_chilko_uses_its_own_frame_rig_and_map_namespace(self):
        self.chilko_fixture()
        result=build(self.root,'L_Chilko_ContractUnitTest',112.,126.)
        self.assertEqual(result['schema'],'raftsim.continuous_map_import.v1')
        self.assertEqual(result['river_id'],'chilko_river_bc');self.assertEqual(result['rig'],'PaddleCrew')
        self.assertEqual(result['section_id'],'chilko_continuous')
        self.assertEqual(result['wet_bed_collision_probes_cm'][0],[10000.,1000.,1000.])
        with self.assertRaisesRegex(ValueError,'Chilko map name'):
            self.call()
        for option in ('profile_assembly',):
            with self.subTest(option=option),self.assertRaisesRegex(ValueError,'own reviewed contracts'):
                build(self.root,'L_Chilko_ContractUnitTest',112.,126.,**{option:self.root/'wrong.json'})
        path=self.root/'dressing.json'
        data=dict(schema='raftsim.chilko_continuous_dressing.v1',river_id='chilko_river_bc',
            runtime_sha256=sha(self.root/'manifest.json'),terrain_sha256=sha(self.root/'terrain/manifest.json'),
            mesh_files_sha256={})
        path.write_text(json.dumps(data))
        result=build(self.root,'L_Chilko_ContractUnitTest',112.,126.,dressing=path)
        self.assertEqual(result['files_sha256'][result['environment']],sha(path))
        data['schema']='raftsim.colorado_continuous_dressing.v1';path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'different runtime terrain/water'):
            build(self.root,'L_Chilko_ContractUnitTest',112.,126.,dressing=path)

    def test_full_route_does_not_authorize_uncooked_descent(self):
        with self.assertRaisesRegex(ValueError, 'actual cooked coverage'):
            self.call(finish=250.)

    def test_full_colorado_requires_geographic_takeout(self):
        path=self.root/'manifest.json'; manifest=json.loads(path.read_text())
        manifest['full_river_coverage']=True;path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'source-identified Pearce Ferry'):
            self.call()

    def takeout_fixture(self):
        spec=dict(schema='raftsim.colorado_takeout_request.v1')
        for key in ('source_chart','evidence','osm'):
            path=self.root/(key+'.source');path.write_text(key)
            spec[key]=path.relative_to(ROOT).as_posix()
        request=self.root/'takeout-request.json';request.write_text(json.dumps(spec))
        receipt=dict(takeout=dict(projected_epsg6404_m=[326.,305.]),
                     downstream_rapid=dict(projected_epsg6404_m=[340.,300.]),
                     runtime_finish_station_m=None,runtime_ready=False)
        return request,spec,receipt

    def test_takeout_binds_sources_and_reflects_north_once(self):
        request,spec,receipt=self.takeout_fixture()
        with patch('build_colorado_continuous_map_contract.register_takeout',return_value=receipt) as register:
            result=build(self.root,'L_Colorado_ContractUnitTest',112.,126.,takeout_request=request)
        register.assert_called_once_with(b'source_chart',b'evidence',b'osm')
        takeout=result['geographic_takeout']
        self.assertEqual(takeout['takeout_world_xy_cm'],[12600.,-500.])
        self.assertEqual(takeout['downstream_rapid_world_xy_cm'],[14000.,0.])
        self.assertEqual(takeout['cooked_station_interval_m'],[100.,138.])
        self.assertEqual(takeout['coordinate_map_sha256'],sha(self.root/'coordinate_map.json'))
        self.assertIsNone(takeout['source_registration']['runtime_finish_station_m'])
        for key in ('source_chart','evidence','osm'):
            self.assertEqual(result['files_sha256'][spec[key]],sha(ROOT/spec[key]))
        self.assertEqual(result['files_sha256'][request.relative_to(ROOT).as_posix()],sha(request))

    def test_takeout_does_not_accept_an_unverified_receipt(self):
        request,_,_=self.takeout_fixture()
        mapping=json.loads((self.root/'coordinate_map.json').read_text())
        with patch('build_colorado_continuous_map_contract.register_takeout',side_effect=ValueError('source changed')):
            with self.assertRaisesRegex(ValueError,'source changed'):
                geographic_takeout(request,mapping,{})

    def test_colorado_takeout_cannot_be_attached_to_chilko(self):
        self.chilko_fixture()
        with self.assertRaisesRegex(ValueError,'cannot be used for Chilko'):
            build(self.root,'L_Chilko_ContractUnitTest',112.,126.,takeout_request=self.root/'takeout.json')

    def test_changed_takeout_source_cannot_be_bound_after_reading(self):
        request,spec,receipt=self.takeout_fixture()
        mapping=json.loads((self.root/'coordinate_map.json').read_text())
        def change_source(*args):
            (ROOT/spec['osm']).write_text('changed')
            return receipt
        files={}
        with patch('build_colorado_continuous_map_contract.register_takeout',side_effect=change_source):
            with self.assertRaisesRegex(ValueError,'changed during registration'):
                geographic_takeout(request,mapping,files)
        self.assertEqual(files,{})

    def test_takeout_request_cannot_change_between_parse_and_source_binding(self):
        request,_,receipt=self.takeout_fixture()
        mapping=json.loads((self.root/'coordinate_map.json').read_text())
        original_read=Path.read_text
        def change_after_read(path,*args,**kwargs):
            text=original_read(path,*args,**kwargs)
            if path==request:
                path.write_text(text+'\n')
            return text
        files={}
        with patch.object(Path,'read_text',change_after_read), \
             patch('build_colorado_continuous_map_contract.register_takeout',return_value=receipt):
            with self.assertRaisesRegex(ValueError,'changed during registration'):
                geographic_takeout(request,mapping,files)
        self.assertEqual(files,{})

    def test_nanite_selection_changes_no_physical_contract(self):
        baseline=self.call()
        candidate=build(self.root,'L_Colorado_ContractUnitTest',112.,126.,nanite_terrain=True)
        self.assertFalse(baseline.pop('nanite_terrain'))
        self.assertTrue(candidate.pop('nanite_terrain'))
        self.assertEqual(candidate,baseline)
        with self.assertRaisesRegex(ValueError,'must be boolean'):
            build(self.root,'L_Colorado_ContractUnitTest',112.,126.,nanite_terrain='true')

    def test_tampered_dependency_refused(self):
        (self.root/'coordinate_map.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Changed continuous runtime'):
            self.call()

    def test_rejected_candidate_refused(self):
        (self.root/'REJECTED.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'rejected continuous runtime'):
            self.call()

    def test_dressing_bound_to_same_terrain_and_water(self):
        path=self.root/'dressing.json'
        data=dict(schema='raftsim.colorado_continuous_dressing.v1',
                  runtime_sha256=sha(self.root/'manifest.json'),
                  terrain_sha256=sha(self.root/'terrain/manifest.json'),mesh_files_sha256={})
        path.write_text(json.dumps(data))
        result=build(self.root,'L_Colorado_ContractUnitTest',112.,126.,dressing=path)
        self.assertEqual(result['files_sha256'][result['environment']],sha(path))
        data['terrain_sha256']='wrong';path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'different runtime terrain/water'):
            build(self.root,'L_Colorado_ContractUnitTest',112.,126.,dressing=path)

    def test_dressing_asset_changes_refused(self):
        path=self.root/'dressing.json'
        asset=self.root/'mesh.uasset';asset.write_bytes(b'new mesh')
        path.write_text(json.dumps(dict(schema='raftsim.colorado_continuous_dressing.v1',
            runtime_sha256=sha(self.root/'manifest.json'),
            terrain_sha256=sha(self.root/'terrain/manifest.json'),
            mesh_files_sha256={asset.relative_to(ROOT).as_posix():'old mesh hash'})))
        with self.assertRaisesRegex(ValueError,'Changed dressing asset'):
            build(self.root,'L_Colorado_ContractUnitTest',112.,126.,dressing=path)

    def source_assembly(self):
        mapping = json.loads((self.root/'coordinate_map.json').read_text())
        source = dict(schema='raftsim.curved_river_coordinate_map.v1', world_y_sign=-1,
            vertical_reference='NAD83(2011) ellipsoid heights', vertical_datum_m=80.,
            horizontal_origin_epsg6404_m=[190., 280.],
            points=[[0., 10., 20., 0., 1.], [2., 12., 20., 0., 1.]])
        original = self.root/'original.json'; original.write_text(json.dumps(source))
        rebased = self.root/'rebased.json'
        rebased.write_text(json.dumps(rebase_chart(source, [200.,300.],90.)[0]))
        manifest = dict(schema='raftsim.colorado_continuous_construction.v1',
            horizontal_crs='EPSG:6404', horizontal_origin_epsg6404_m=[200.,300.],
            vertical_datum_m=90., source_reaches=[dict(name='Badger Creek',
                source_chart=original.relative_to(ROOT).as_posix(), chart_sha256=sha(original),
                rebased_chart=rebased.name)])
        path=self.root/'assembly.json'; path.write_text(json.dumps(manifest))
        return path, mapping, original, rebased, manifest

    def test_profile_registration_binds_original_and_rebased_geography(self):
        path,mapping,original,rebased,_=self.source_assembly()
        files={}; sources=rapid_profile_sources(path,mapping,files)
        self.assertEqual(sources,[dict(map='L_Colorado_BadgerCreek',
            coordinate_map=rebased.relative_to(ROOT).as_posix())])
        for p in (path,original,rebased): self.assertEqual(files[p.relative_to(ROOT).as_posix()],sha(p))
        result=build(self.root,'L_Colorado_ContractUnitTest',112.,126.,profile_assembly=path)
        self.assertEqual(result['rapid_profile_sources'],sources)

    def test_wrong_frame_or_changed_source_cannot_register(self):
        path,mapping,original,rebased,manifest=self.source_assembly()
        for field,value in [('vertical_datum_m',91.),('horizontal_origin_epsg6404_m',[201.,300.])]:
            with self.assertRaisesRegex(ValueError,'different geographic frame'):
                rapid_profile_sources(path,dict(mapping,**{field:value}),{})
        rebased.write_text('{}')
        with self.assertRaisesRegex(ValueError,'disagrees with original geography'):
            rapid_profile_sources(path,mapping,{})
        original.write_text('{}')
        with self.assertRaisesRegex(ValueError,'Changed original rapid chart'):
            rapid_profile_sources(path,mapping,{})

    def test_soap_creek_profile_is_registered_not_silently_omitted(self):
        path,mapping,original,rebased,manifest=self.source_assembly()
        manifest['source_reaches'][0]['name']='Soap Creek'
        path.write_text(json.dumps(manifest))
        files={}
        self.assertEqual(rapid_profile_sources(path,mapping,files),[
            dict(map='L_Colorado_SoapCreek',coordinate_map=rebased.relative_to(ROOT).as_posix())])
        for p in (path,original,rebased):self.assertEqual(files[p.relative_to(ROOT).as_posix()],sha(p))

    def test_duplicate_and_empty_source_profiles_refused(self):
        path,mapping,_,_,manifest=self.source_assembly()
        manifest['source_reaches']*=2; path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'Duplicate rapid source'):
            rapid_profile_sources(path,mapping,{})
        manifest['source_reaches']=[]; path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'No supported production'):
            rapid_profile_sources(path,mapping,{})

    def test_unkar_is_bound_to_original_geography_not_a_hance_offset(self):
        path,mapping,original,rebased,manifest=self.source_assembly()
        manifest['source_reaches'][0]['name']='Unkar'
        path.write_text(json.dumps(manifest))
        files={}
        self.assertEqual(rapid_profile_sources(path,mapping,files),[
            dict(map='L_Colorado_Unkar',coordinate_map=rebased.relative_to(ROOT).as_posix())])
        for p in (path,original,rebased):self.assertEqual(files[p.relative_to(ROOT).as_posix()],sha(p))

    def test_georgie_uses_its_verified_source_chart_not_24_half_mile(self):
        path,mapping,original,rebased,manifest=self.source_assembly()
        manifest['source_reaches'][0]['name']='Georgie'
        path.write_text(json.dumps(manifest))
        files={}
        self.assertEqual(rapid_profile_sources(path,mapping,files),[
            dict(map='L_Colorado_Georgie',coordinate_map=rebased.relative_to(ROOT).as_posix())])
        for p in (path,original,rebased):self.assertEqual(files[p.relative_to(ROOT).as_posix()],sha(p))
        manifest['source_reaches'][0]['name']='24 1/2 Mile'
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'No supported production'):
            rapid_profile_sources(path,mapping,{})


if __name__ == '__main__':
    unittest.main()
