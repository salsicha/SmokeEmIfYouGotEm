import sys
from pathlib import Path
import unittest
import ctypes
import bpy
import manta
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_secondary_boundary import BoundaryCompletion
from probe_water_feature_solver_stages import cleanup, vector_data_address, grid_array


class NativeBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # This build registers inherited grid methods during native domain
        # initialization, not merely import manta. Load, never save, the fixture.
        if 'Feature liquid' not in bpy.data.objects:
            raise ValueError('Load the preserved native eddy fixture before this suite')
        bpy.context.scene.frame_set(168)

    def test_liquid_near_wall_not_ballistic_spray_after_completion(self):
        space, hook, args, error_text = {}, BoundaryCompletion(), {}, None
        try:
            space['s98'] = manta.Solver(name='boundary_test98', gridSize=manta.vec3(12, 12, 12), dim=3)
            for key, kind in [('flags_s98', manta.FlagGrid), ('phi_s98', manta.LevelsetGrid),
                ('v_s98', manta.MACGrid), ('nr_s98', manta.RealGrid), ('ta_s98', manta.RealGrid),
                ('wc_s98', manta.RealGrid), ('ke_s98', manta.RealGrid), ('normal_s98', manta.VecGrid)]:
                space[key] = space['s98'].create(kind, name=key)
            space['flags_s98'].initDomain(boundaryWidth=0)
            space['phi_s98'].setConst(-4.)
            space['flags_s98'].updateFromLevelset(levelset=space['phi_s98'])
            space['v_s98'].setConst(manta.vec3(0, 0, 0))
            args = dict(flags=space['flags_s98'], v=space['v_s98'], phi=space['phi_s98'],
                normal=space['normal_s98'], neighborRatio=space['nr_s98'],
                potTA=space['ta_s98'], potWC=space['wc_s98'], potKE=space['ke_s98'],
                radius=2, tauMinTA=5, tauMaxTA=20, tauMinWC=2, tauMaxWC=8,
                tauMinKE=1, tauMaxKE=5, scaleFromManta=.075)
            for corrected in (False, True):
                if corrected:
                    hook.compute(**args)
                else:
                    hook.original(**args)
                self.assertEqual(grid_array(space['nr_s98'], (12, 12, 12))[1, 6, 6], 1 if corrected else 0)
                space['pp_s98'] = space['s98'].create(manta.BasicParticleSystem, name='test_particles')
                space['vel_pp98'] = space['pp_s98'].create(manta.PdataVec3)
                space['life_pp98'] = space['pp_s98'].create(manta.PdataReal)
                space['force_pp98'] = space['pp_s98'].create(manta.PdataVec3)
                space['pp_s98'].addParticle(pos=manta.vec3(1.5, 6.5, 6.5))
                space['pp_s98'].addParticle(pos=manta.vec3(6.5, 6.5, 6.5))
                space['vel_pp98'].setConst(manta.vec3(0, 0, 0))
                space['force_pp98'].setConst(manta.vec3(0, 0, 0))
                space['life_pp98'].setConst(1.)
                manta.flipUpdateSecondaryParticles(mode='linear', pts_sec=space['pp_s98'],
                    v_sec=space['vel_pp98'], l_sec=space['life_pp98'], f_sec=space['force_pp98'],
                    flags=space['flags_s98'], v=space['v_s98'], neighborRatio=space['nr_s98'],
                    radius=2, gravity=manta.vec3(0, 0, 0), k_b=.5, k_d=.6, c_s=.4, c_b=.77,
                    scale=False, dt=1e-6)
                self.assertEqual(space['pp_s98'].pySize(), 2)
                address = vector_data_address(space['pp_s98'].getDataPointer(), 2, 16)
                data = np.frombuffer(bytes((ctypes.c_ubyte*32).from_address(address)),
                    dtype=np.dtype([('pos', '<f4', 3), ('flags', '<i4')]))
                np.testing.assert_array_equal(data['flags'] & 14, [4, 4] if corrected else [2, 4])
                np.testing.assert_array_equal(data['pos'], [[1.5, 6.5, 6.5], [6.5, 6.5, 6.5]])
                for key in ('force_pp98', 'life_pp98', 'vel_pp98', 'pp_s98'):
                    del space[key]
            self.assertEqual(hook.calls, 1)
            self.assertGreater(hook.total_changed, 0)
        except Exception as error:
            error_text = f'{type(error).__name__}: {error}'
            error.__traceback__ = None
        finally:
            args.clear()
            cleanup(space, '98')
        if error_text:
            self.fail(error_text)

    def test_hook_install_restore_does_not_persist(self):
        hook = BoundaryCompletion()
        try:
            hook.install()
            self.assertNotEqual(manta.flipComputeSecondaryParticlePotentials, hook.original)
        finally:
            hook.restore()
        self.assertIs(manta.flipComputeSecondaryParticlePotentials, hook.original)


if __name__ == '__main__':
    unittest.main(argv=['native-secondary-boundary'])
