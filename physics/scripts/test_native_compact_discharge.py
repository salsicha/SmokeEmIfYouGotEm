import json
import os
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from solver_face_discharge import face_discharge,SOLVER_FLAGS


class CompactDischargeContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='raftsim-flux-contract-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.scenario=self.root/'scenario';self.scenario.mkdir()
        grid=dict(nx=3,ny=2,dx=2.,dy=3.,origin_x=0.,origin_y=0.)
        (self.scenario/'scenario.json').write_text(json.dumps(dict(grid=grid)))
        original={k:np.zeros((2,3)) for k in ('depth','eta','u','v','hu','hv')}
        original.update(wet=np.zeros((2,3),bool),extra_native_field=np.arange(4))
        np.savez(self.scenario/'initial_state.npz',**original)
        self.before=(self.scenario/'initial_state.npz').read_bytes()
        self.frame={k:np.full((2,3),i+.25) for i,k in enumerate(('h','eta','u','v','hu','hv','wet'))}
        self.reply=dict(nx=3,ny=2,dx_m=2.,dy_m=3.,units='m3/s',sign='positive_grid_x',
                        layout='station_faces',discharge=[1.,2.,3.,4.])

    def invoke(self,reply):
        def inspect(command,**kwargs):
            pkg=Path(command[command.index('--scenario')+1])
            self.assertIn('--inspect-face-discharge',command)
            with np.load(pkg/'initial_state.npz',allow_pickle=False) as saved:
                for key,name in (('depth','h'),('eta','eta'),('u','u'),('v','v'),('hu','hu'),('hv','hv')):
                    np.testing.assert_array_equal(saved[key],self.frame[name])
                np.testing.assert_array_equal(saved['wet'],self.frame['wet']>.5)
                np.testing.assert_array_equal(saved['extra_native_field'],np.arange(4))
            return SimpleNamespace(stdout=json.dumps(reply))
        with patch('solver_face_discharge.shutil.disk_usage',return_value=SimpleNamespace(free=100*1024**3)), \
             patch('solver_face_discharge.subprocess.run',side_effect=inspect):
            return face_discharge(sys.executable,self.scenario,self.frame,compact=True,scratch_parent=self.root)

    def test_scratch_state_all_fields_preserved_and_cleaned(self):
        np.testing.assert_array_equal(self.invoke(self.reply),self.reply['discharge'])
        self.assertEqual(self.before,(self.scenario/'initial_state.npz').read_bytes())
        self.assertFalse(list(self.root.glob('raftsim-face-inspect-*')))

    def test_refuse_wrong_contract_missing_nonfinite_or_wrong_grid(self):
        for change in (dict(units='m2/s'),dict(layout='row_major'),dict(nx=4),dict(dy_m=2.),
                       dict(discharge=[1.,2.]),dict(discharge=[1.,2.,3.,float('nan')])):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.invoke(dict(self.reply,**change))
            self.assertFalse(list(self.root.glob('raftsim-face-inspect-*')))

    def test_disk_guard_precedes_copy_and_native_launch(self):
        with patch('solver_face_discharge.shutil.disk_usage',return_value=SimpleNamespace(free=40*1024**3)), \
             patch('solver_face_discharge.subprocess.run') as execute:
            with self.assertRaisesRegex(ValueError,'headroom'):
                face_discharge(sys.executable,self.scenario,self.frame,compact=True,scratch_parent=self.root)
            execute.assert_not_called()


@unittest.skipUnless(os.environ.get('RAFTSIM_COMPACT_TEST_SOLVER'), 'Set isolated compact solver for native tests')
class CompactDischargeNativeTests(unittest.TestCase):
    def test_actual_face_sum_parity_and_compact_payload(self):
        solver=Path(os.environ['RAFTSIM_COMPACT_TEST_SOLVER']).resolve()
        fixtures=Path(__file__).resolve().parents[2]/'unreal/Plugins/SEIYGECore/data/validation/milestone17/analytic_fixtures/fixtures'
        for name in ('wet_dry_shoreline','lake_at_rest_balance','transcritical_bump'):
            scenario=fixtures/name/'scenario'
            base=[str(solver),'--scenario',str(scenario),*SOLVER_FLAGS]
            full=subprocess.run(base+['--inspect-face-fluxes'],check=True,capture_output=True,text=True,timeout=60).stdout
            compact=subprocess.run(base+['--inspect-face-discharge'],check=True,capture_output=True,text=True,timeout=60).stdout
            a,b=json.loads(full),json.loads(compact)
            expected=np.asarray(a['x_faces']).reshape(a['ny'],a['nx']+1).sum(0)*a['dy_m']
            np.testing.assert_array_equal(b['discharge'],expected)
            self.assertLess(len(compact),len(full))

    @unittest.skipUnless(os.environ.get('RAFTSIM_PRECOMPACT_TEST_SOLVER'),'Set prior isolated solver for old/new integration parity')
    def test_old_and_new_integrators_save_identical_actual_frames(self):
        root=Path(__file__).resolve().parents[2]
        scenario=root/'unreal/Plugins/SEIYGECore/data/validation/milestone17/analytic_fixtures/fixtures/wet_dry_shoreline/scenario'
        with tempfile.TemporaryDirectory(prefix='raftsim-step-parity-') as temporary:
            outputs=[]
            for label,var in (('old','RAFTSIM_PRECOMPACT_TEST_SOLVER'),('new','RAFTSIM_COMPACT_TEST_SOLVER')):
                out=Path(temporary)/label
                run=subprocess.run([os.environ[var],'--scenario',str(scenario),'--output',str(out),*SOLVER_FLAGS,
                    '--steps','5','--frame-interval','2','--feature-strength-scale','0','--no-preserve-initial-mass'],
                    capture_output=True,text=True,timeout=90)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                outputs.append(next(out.iterdir()))
            old,new=outputs
            self.assertEqual((old/'manifest.json').read_bytes(),(new/'manifest.json').read_bytes())
            manifest=json.loads((old/'manifest.json').read_text())
            for name in ['validation.json',*manifest['frames'],*manifest['probes'],*manifest['cross_sections']]:
                self.assertEqual((old/name).read_bytes(),(new/name).read_bytes(),name)


if __name__=='__main__':unittest.main()
