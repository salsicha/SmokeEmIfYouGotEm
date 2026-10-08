"""Independent native-binary oracle for the bounded MUSCL row-cache path."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import numpy as np
from solver_face_discharge import SOLVER_FLAGS


@unittest.skipUnless(os.environ.get('RAFTSIM_ROLLING_TEST_SOLVER') and
                     os.environ.get('RAFTSIM_PREROLLING_TEST_SOLVER'),
                     'Set isolated candidate and unchanged full-scratch native solvers')
class NativeRollingRowParityTests(unittest.TestCase):
    def setUp(self):
        self.solvers=[os.environ['RAFTSIM_PREROLLING_TEST_SOLVER'],os.environ['RAFTSIM_ROLLING_TEST_SOLVER']]
        self.root=Path(__file__).resolve().parents[2]
        self.fixture=self.root/'unreal/Plugins/SEIYGECore/data/validation/milestone17/analytic_fixtures/fixtures/wet_dry_shoreline/scenario'
        self.temp=tempfile.TemporaryDirectory(prefix='raftsim-rolling-parity-')
        self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name)

    def flags(self,scheme):
        flags=list(SOLVER_FLAGS)
        flags[flags.index('--flux-scheme')+1]=scheme
        return flags

    def invoke(self,solver,scenario,flags):
        result=subprocess.run([solver,'--scenario',str(scenario),*flags],
            capture_output=True,text=True,timeout=90)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return result.stdout

    def hashes(self,path):
        return {p.relative_to(path).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in path.rglob('*') if p.is_file()}

    def test_old_new_fixture_frames_probes_and_diagnostics(self):
        for name in ('wet_dry_shoreline','lake_at_rest_balance','transcritical_bump'):
            scenario=self.fixture.parent.parent/name/'scenario'
            for scheme in ('hll','roe','rusanov'):
                with self.subTest(fixture=name,scheme=scheme):
                    paths=[]
                    for index,solver in enumerate(self.solvers):
                        out=self.work/f'{name}-{scheme}-{index}'
                        self.invoke(solver,scenario,[*self.flags(scheme),'--output',str(out),
                            '--steps','7','--frame-interval','3','--feature-strength-scale','0',
                            '--no-preserve-initial-mass','--stream-output'])
                        paths.append(out)
                    self.assertEqual(self.hashes(paths[0]),self.hashes(paths[1]))
                    for diagnostic in ('--inspect-face-fluxes','--inspect-face-discharge','--inspect-boundary-flux'):
                        a,b=[self.invoke(solver,scenario,[*self.flags(scheme),diagnostic]) for solver in self.solvers]
                        self.assertEqual(a,b,diagnostic)

    def test_cache_wrap_small_grids_and_parallel_wet_dry_fronts(self):
        for ny,nx in ((2,13),(3,13),(4,13),(5,13),(6,13),(129,131)):
            scenario=self.work/f'input-{ny}-{nx}';scenario.mkdir()
            meta=json.loads((self.fixture/'scenario.json').read_text())
            meta['grid'].update(nx=nx,ny=ny,dx=.7,dy=1.1)
            meta.update(fixed_dt=.005,roughness=.035,feature_count=0,probe_count=0)
            for boundary in meta['boundaries']:boundary['kind']='wall'
            (scenario/'scenario.json').write_text(json.dumps(meta))
            (scenario/'features.json').write_text('{"features": []}')
            (scenario/'probes.json').write_text('{"probes": []}')
            row,col=np.indices((ny,nx))
            bed=.8*np.sin(row*.11)+.4*np.cos(col*.17)+np.where((row//7+col//11)%5==0,1.5,0.)
            depth=np.maximum(0.,1.1-bed)
            depth[(row+col)%13==0]=.5e-6
            u=.4*np.sin(col*.05);v=.3*np.cos(row*.13)
            np.save(scenario/'bed.npy',bed)
            np.savez(scenario/'initial_state.npz',depth=depth,u=u,v=v,eta=bed+depth,
                     hu=depth*u,hv=depth*v,wet=depth>1.e-6)
            for scheme in ('hll','roe','rusanov'):
                with self.subTest(grid=(ny,nx),scheme=scheme):
                    paths=[]
                    for index,solver in enumerate(self.solvers):
                        out=self.work/f'out-{ny}-{nx}-{scheme}-{index}'
                        self.invoke(solver,scenario,[*self.flags(scheme),'--output',str(out),
                            '--steps','7','--frame-interval','3','--feature-strength-scale','0',
                            '--no-preserve-initial-mass','--stream-output'])
                        paths.append(out)
                    self.assertEqual(self.hashes(paths[0]),self.hashes(paths[1]))


if __name__=='__main__':unittest.main()
