import copy
import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_optical_controls import effective_coefficients,verify_material,simulation_hash


class OpticalControlTest(unittest.TestCase):
    def test_rgb_times_alpha_not_display_color(self):
        np.testing.assert_allclose(effective_coefficients('(R=0.6,G=0.05,B=0.02,A=0.056)'),[.0336,.0028,.00112])
        with self.assertRaises(ValueError):effective_coefficients('(R=-1,G=0,B=0,A=1)')

    def test_actual_parameters_required_and_foam_preserved(self):
        material=dict(vectors=dict(Absorption='(R=.003,G=.0018,B=.0022,A=1)',Scattering='(R=.0002,G=.00025,B=.00022,A=1)'),
                      scalars={'River Roughness':.22,'Opacity':0,'River Foam Strength':1})
        case=dict(absorption_per_cm=[.003,.0018,.0022],scattering_per_cm=[.0002,.00025,.00022],roughness=.22)
        self.assertTrue(verify_material(material,case))
        for key,value in [('River Roughness',.12),('Opacity',1),('River Foam Strength',4)]:
            changed=copy.deepcopy(material);changed['scalars'][key]=value
            self.assertFalse(verify_material(changed,case))

    def test_optics_not_physics_can_change(self):
        snapshot=dict(runtime_materials=[1],emitters=[{'positions':[1,2,3]}],captured_system_state={'time':12})
        original=simulation_hash(snapshot)
        snapshot['runtime_materials']=[2]
        self.assertEqual(original,simulation_hash(snapshot))
        snapshot['emitters'][0]['positions'][0]=4
        self.assertNotEqual(original,simulation_hash(snapshot))


if __name__=='__main__':unittest.main()
