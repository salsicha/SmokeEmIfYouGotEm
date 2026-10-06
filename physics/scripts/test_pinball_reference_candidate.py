import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
from PIL import Image
from build_pinball_reference_candidate import stage, continue_candidate, rock_height, PACKAGE, TERRAIN, sha


class PinballGeometryTests(unittest.TestCase):
    def test_constant_boundary_continuation_preserves_conserved_state(self):
        with tempfile.TemporaryDirectory(prefix='raftsim-pinball-resume-') as tmp:
            root=Path(tmp);candidate=root/'candidate';scenario=candidate/'scenario';scenario.mkdir(parents=True)
            run=root/'run';run.mkdir();(run/'last.csv').write_text('mock frame')
            bed=np.array([[1.,2.],[3.,4.]])
            np.save(scenario/'bed.npy',bed)
            sc=dict(grid=dict(nx=2,ny=2,origin_x=0,origin_y=0,dx=2,dy=2),
                    metadata=dict(scenario_id='same'),boundaries=[dict(kind='discharge_profile')])
            (scenario/'scenario.json').write_text(json.dumps(sc))
            (candidate/'candidate.json').write_text(json.dumps(dict(scenario_bed_sha256=sha(scenario/'bed.npy'),rocks=[])))
            (run/'manifest.json').write_text(json.dumps(dict(scenario_id='same',disable_fixture_calibrations=True,frames=['last.csv'])))
            (run/'validation.json').write_text(json.dumps(dict(finite_state=True,velocity_limit_reached=False,mass_relative_drift=.004)))
            f=dict(h=np.ones((2,2)),eta=bed+1,u=np.full((2,2),2.),v=np.zeros((2,2)),
                   hu=np.full((2,2),2.),hv=np.zeros((2,2)),x=np.array([[0,2],[0,2]]),y=np.array([[0,0],[2,2]]))
            with patch('export_hance_evidence_runtime.read_frame',return_value=f):
                receipt=continue_candidate(candidate,run,root/'continued')
                with np.load(root/'continued/scenario/initial_state.npz') as state:
                    np.testing.assert_array_equal(state['hu'],f['hu'])
                    np.testing.assert_array_equal(state['hv'],f['hv'])
                self.assertEqual(receipt['continuation']['source_validation']['mass_relative_drift'],.004)
                f['eta']=f['eta']+1
                with self.assertRaisesRegex(ValueError,'bed/grid'):continue_candidate(candidate,run,root/'wrong-bed')
                self.assertFalse((root/'wrong-bed').exists())
                sc['boundaries'][0]['hydrograph']=[dict(time=0,value=1)]
                (scenario/'scenario.json').write_text(json.dumps(sc))
                with self.assertRaisesRegex(ValueError,'constant boundaries'):continue_candidate(candidate,run,root/'wrong-forcing')

    def test_closed_local_crown(self):
        f=dict(station_m=10,lateral_m=3,length_m=8,width_m=6)
        self.assertEqual(rock_height(10,3,f,1,4),4)
        self.assertEqual(rock_height(10,4,f,1,4),4)
        self.assertTrue(np.isneginf(rock_height(14,3,f,1,4)))
        self.assertTrue(np.isneginf(rock_height(10,6,f,1,4)))
        self.assertGreater(rock_height(12,3,f,1,4),1)

    def test_bar_crown_connects_bank_to_second_rock_without_a_deep_seam(self):
        bar=dict(station_m=2052,lateral_m=-26,length_m=24,width_m=42,flat_crown_fraction=.8)
        lateral=np.linspace(-32,-10,89)
        crown=rock_height(2050,lateral,bar,150.53,154.96)
        np.testing.assert_allclose(crown,154.96,atol=1e-9)
        self.assertTrue(np.isneginf(rock_height(2052,-47,bar,150.53,154.96)))
        for invalid in (0,1,-.1):
            with self.assertRaises(ValueError):
                rock_height(2050,-16,bar|dict(flat_crown_fraction=invalid),150.53,154.96)

    def test_stage_preserves_live_data_and_changes_only_rock_support(self):
        manifest=PACKAGE/'cooked_flow_fields/manifest.json'
        terrain=TERRAIN/'huacas_evidence_heightfield_2017.png'
        original=(sha(manifest),sha(terrain))
        cm=json.loads(manifest.read_text());g=cm['grid']
        if 'pinball_reference' in cm:
            with tempfile.TemporaryDirectory(prefix='raftsim-pinball-test-') as tmp:
                with self.assertRaisesRegex(ValueError,'already installed'):stage(Path(tmp)/'candidate')
            self.assertEqual((sha(manifest),sha(terrain)),original)
            return
        before=np.load(PACKAGE/'cooked_flow_fields'/cm['bands'][0]['arrays']['bed']['file'])
        ss,ll=np.meshgrid(g['origin_x_m']+np.arange(g['nx'])*g['dx_m'],
                         g['origin_y_m']+np.arange(g['ny'])*g['dy_m'])
        with tempfile.TemporaryDirectory(prefix='raftsim-pinball-test-') as tmp:
            output=Path(tmp)/'candidate';report=stage(output)
            after=np.load(output/'scenario/bed.npy')
            allowed=np.zeros(before.shape,dtype=bool)
            for r in report['rocks']:
                allowed|=np.isfinite(rock_height(ss,ll,r['feature'],r['base_m'],r['crest_m']))
                self.assertAlmostEqual(r['crest_m']-r['crown_reference_surface_m'],-r['feature']['crest_below_ws_m'])
            self.assertTrue(np.array_equal(before[~allowed],after[~allowed]))
            self.assertTrue(np.all(after>=before))
            self.assertGreater(np.count_nonzero(after>before),0)
            hf=np.array(Image.open(terrain));patch=np.array(Image.open(output/terrain.name))
            self.assertEqual(hf.shape,patch.shape)
            self.assertTrue(np.all(patch>=hf))
            self.assertLess(np.count_nonzero(patch!=hf),4096)
            self.assertEqual((sha(manifest),sha(terrain)),original)
            with self.assertRaises(ValueError):stage(output)


if __name__=='__main__':unittest.main()
