import json
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from export_chilko_continuous_terrain import export
from export_colorado_continuous_terrain import LandscapeTriangles, sha
from build_curvilinear_river_scenario import canonical_terrain_bed


class ChilkoContinuousTerrain(unittest.TestCase):
    def evidence(self,root):
        ev=root/'evidence';ev.mkdir()
        r,c=np.indices((520,520))
        bed=950+.01*c-.02*r+((r%2)*(c%2))*.3
        np.savez_compressed(ev/'evidence_grid.npz',bed=bed,class_code=np.zeros(bed.shape,dtype='uint8'))
        m=dict(schema='raftsim.chilko.lava_canyon_evidence_grid.v1',
            crs='EPSG:3157 NAD83(CSRS) / UTM zone 10N',vertical='CGVD2013 orthometric metres (LidarBC)',
            grid=dict(x0=441995,y_top=5750509,nx=520,ny=520,cell_m=1))
        (ev/'manifest.json').write_text(json.dumps(m))
        return ev

    def sample(self,out,ev,xy=None,**overrides):
        args=dict(manifest_path=out/'manifest.json',evidence=ev,
            xy=np.array([[442010.,5750400.]]) if xy is None else xy,
            river_id='chilko_river_bc',crs='EPSG:3157',vertical='CGVD2013 (EPSG:6647)',
            origin=[442000,5750000],datum=900.)
        args.update(overrides)
        return canonical_terrain_bed(**args)

    def test_triangle_bed_is_exact_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ev=self.evidence(root);out=root/'terrain'
            before=sha(ev/'evidence_grid.npz')
            m=export(ev,out,[442000,5750000],900.)
            self.assertEqual(len(m['chunks']),4);self.assertGreater(len(m['incomplete_source_chunks']),0)
            self.assertEqual(before,sha(ev/'evidence_grid.npz'))
            xy=np.array([[442010.25,5750400.75],[442252.,5750252.]])
            bed,receipt=self.sample(out,ev,xy)
            np.testing.assert_array_equal(bed,LandscapeTriangles(out).sample(xy))
            self.assertEqual(receipt['manifest_sha256'],sha(out/'manifest.json'))
            self.assertFalse(m['engine_validated']);self.assertFalse(m['full_river_complete'])
            self.assertNotIn('horizontal_origin_epsg6404_m',m)
            self.assertAlmostEqual(m['landscape']['actor_z_cm'],(200+2400*32768/65535-900)*100)
            with self.assertRaisesRegex(ValueError,'Fresh'):export(ev,out,[442000,5750000],900.)

    def test_water_frame_and_source_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ev=self.evidence(root);out=root/'terrain'
            export(ev,out,[442000,5750000],900.)
            for args in [dict(crs='EPSG:32610'),dict(vertical='ellipsoid'),dict(datum=901),
                         dict(origin=[442001,5750000]),dict(river_id='colorado')]:
                with self.subTest(args=args),self.assertRaisesRegex(ValueError,'frames disagree'):
                    self.sample(out,ev,**args)
            with self.assertRaisesRegex(ValueError,'entire hydraulic grid'):
                self.sample(out,ev,np.array([[441999.,5750400.]]))
            with (ev/'evidence_grid.npz').open('ab') as stream:stream.write(b'changed')
            with self.assertRaisesRegex(ValueError,'sources disagree'):self.sample(out,ev)

    def test_generic_frame_cannot_be_mislabeled_as_colorado(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ev=self.evidence(root);out=root/'terrain'
            m=export(ev,out,[442000,5750000],900.)
            for key,value in [('river_id','unknown'),('horizontal_crs','EPSG:6404'),
                              ('vertical_reference','NAD83(2011) ellipsoid'),
                              ('horizontal_origin_epsg6404_m',[442000,5750000])]:
                changed=dict(m);changed[key]=value
                (out/'manifest.json').write_text(json.dumps(changed))
                with self.subTest(key=key),self.assertRaisesRegex(ValueError,'geographic frame'):
                    LandscapeTriangles(out)

    def test_source_frame_and_missing_evidence_fail_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ev=self.evidence(root);out=root/'terrain'
            path=ev/'manifest.json';m=json.loads(path.read_text());m['crs']='EPSG:32610'
            path.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'evidence frame'):export(ev,out,[442000,5750000],900.)
            self.assertFalse(out.exists())
            m['crs']='EPSG:3157 NAD83(CSRS) / UTM zone 10N';path.write_text(json.dumps(m))
            bed=np.full((520,520),np.nan)
            np.savez_compressed(ev/'evidence_grid.npz',bed=bed,class_code=np.zeros(bed.shape,dtype='uint8'))
            with self.assertRaisesRegex(ValueError,'invalid source'):export(ev,out,[442000,5750000],900.)
            self.assertFalse(out.exists())

    def test_scenario_initialization_uses_native_triangles_before_depth_and_flux(self):
        from build_curvilinear_river_scenario import main
        from export_colorado_continuous_runtime import registered_queries
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ev=self.evidence(root);out=root/'terrain';inputs=root/'inputs'
            path=ev/'manifest.json';m=json.loads(path.read_text())
            m.update(parameters=dict(discharge_m3s=5),statistics=dict(reach_station_m=[30,430]))
            path.write_text(json.dumps(m))
            with np.load(ev/'evidence_grid.npz') as arrays:bed=arrays['bed'].copy()
            rr,cc=np.indices(bed.shape);channel=(abs(441995+cc+.5-442200)<12)
            np.savez_compressed(ev/'evidence_grid.npz',bed=bed,dem2021=bed,
                                class_code=np.zeros(bed.shape,dtype='uint8'),river=channel,channel=channel)
            station=np.arange(0.,471.,2.)
            points=np.column_stack((442200+np.sin(station/160),5750490-station,station))
            (ev/'centreline.json').write_text(json.dumps(dict(points_xy_station=points.tolist())))
            (ev/'profile.json').write_text(json.dumps(dict(station_center_m=station.tolist(),
                ws_reference_m=(970-station*.01).tolist(),ws_reference_method='synthetic test only')))
            export(ev,out,[442000,5750000],900.)
            argv=['build',str(ev),str(inputs),'--river-id','chilko_river_bc','--section-id','synthetic',
                '--scenario-id','synthetic','--flow-band','test','--crs-label','EPSG:3157',
                '--vertical-reference','CGVD2013 (EPSG:6647)','--vertical-datum-m','900',
                '--origin','442000','5750000','--terrain-manifest',str(out/'manifest.json'),
                '--flow-source','synthetic','--description','test only']
            with patch('sys.argv',argv),contextlib.redirect_stdout(io.StringIO()):main()
            with np.load(inputs/'reference.npz') as ref:
                expected=LandscapeTriangles(out).sample(np.stack((ref['world_x'],ref['world_y']),axis=-1))
                surface=np.broadcast_to(ref['ws_reference'],expected.shape)
                expected_depth=np.where(ref['channel']&(surface-expected>.02),surface-expected,0.)
            np.testing.assert_array_equal(np.load(inputs/'scenario/bed.npy'),expected)
            with np.load(inputs/'scenario/initial_state.npz') as state:
                np.testing.assert_array_equal(state['depth'],expected_depth)
                np.testing.assert_allclose((state['hu']*2).sum(axis=0),5.,atol=1e-12)
            report=json.loads((inputs/'build_report.json').read_text())
            self.assertEqual(report['continuous_terrain']['manifest_sha256'],sha(out/'manifest.json'))
            chart=json.loads((inputs/'coordinate_map.json').read_text())
            terrain=json.loads((out/'manifest.json').read_text())
            scenario=json.loads((inputs/'scenario/scenario.json').read_text())
            _,queries=registered_queries(chart,terrain,scenario['grid'])
            np.testing.assert_allclose(LandscapeTriangles(out).sample(queries),expected,atol=1e-8,rtol=0)
            for key,value in [('river_id','colorado'),('horizontal_crs','EPSG:6404'),
                              ('vertical_reference','ellipsoid')]:
                bad=dict(chart);bad[key]=value
                with self.subTest(key=key),self.assertRaisesRegex(ValueError,'geographic frame'):
                    registered_queries(bad,terrain,scenario['grid'])


if __name__=='__main__':unittest.main()
